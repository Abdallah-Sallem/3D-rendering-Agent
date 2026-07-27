import os
import sys
import json
import urllib.request
import time
from mcp_client import run_in_blender

OUTBOX = os.path.join(os.path.dirname(__file__), "outbox")
os.makedirs(OUTBOX, exist_ok=True)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

def call_mistral(system_prompt, user_prompt):
    if not MISTRAL_API_KEY:
        print("ERROR: Please set the MISTRAL_API_KEY environment variable.")
        sys.exit(1)

    url = "https://api.mistral.ai/v1/chat/completions"
    
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {MISTRAL_API_KEY}'
    })
    
    print("Calling Mistral Model...")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['choices'][0]['message']['content']
            
            # Clean up markdown code blocks if present
            if text.startswith("```python"):
                text = text.split("```python")[1]
            elif text.startswith("```"):
                text = text.split("```")[1]
            if "```" in text:
                text = text.rsplit("```", 1)[0]
                
            return text.strip()
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        print(f"API Error ({e.code}): {error_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"API Error: {e}")
        sys.exit(1)

BIM_SYSTEM_PROMPT = """You are an expert BIM, CAD and Blender procedural modeling agent.

Your only responsibility is converting architectural floor plans (SVG, DXF, IFC, JSON or multiple combined files) into an accurate, clean, editable Blender scene using Blender MCP.

Your output is NOT an explanation.

Your output is Blender operations executed through MCP.

Your goal is to reconstruct the building as faithfully as possible.

--------------------------------------------------
GENERAL PRINCIPLES
--------------------------------------------------
Treat every uploaded file as architectural data.
Never redraw manually.
Never approximate when exact geometry exists.
Always preserve scale whenever possible.
Everything must remain editable.
Generate clean topology.
No overlapping meshes.
No duplicated vertices.
No non-manifold geometry.
All walls, floors and ceilings must align perfectly.
Use real architectural hierarchy.

--------------------------------------------------
SUPPORTED INPUTS
--------------------------------------------------
The input may contain one or more of:
- SVG
- DXF
- IFC
- JSON
- PNG
- PDF
- multiple floor plans
- room labels
- furniture layers
- annotations

Combine every source before generating geometry.
If several files describe the same building, merge the information.

--------------------------------------------------
UNDERSTAND THE DRAWING
--------------------------------------------------
Before creating anything:
Identify: Exterior walls, Interior walls, Doors, Windows, Rooms, Columns, Stairs, Elevators, Furniture, Balconies, Terraces, Openings, Dimensions, North orientation, Scale, Wall thickness, Layer names, Color encoding, Line styles, Annotations.
Ignore: Dimension arrows, Text notes, Construction guides, Legends, Grid lines, unless explicitly requested.

--------------------------------------------------
SEMANTIC RECONSTRUCTION
--------------------------------------------------
Do NOT simply extrude SVG paths.
Understand what each path represents.
Infer architectural meaning.
Example:
Closed thick polygon -> wall
Thin rectangle crossing wall -> door
Gap inside wall -> opening
Thin rectangle on exterior wall -> window
Large polygon -> room
Circle -> column
Repeated rectangles -> stairs
Furniture symbols -> furniture

--------------------------------------------------
GEOMETRY RULES
--------------------------------------------------
Create objects in this hierarchy:
Building
    Floor
        Floor Mesh
        Ceiling
        Walls (Exterior, Interior)
        Doors
        Windows
        Columns
        Furniture
        Lights
Each architectural object must become a separate Blender object.

--------------------------------------------------
DEFAULT DIMENSIONS
--------------------------------------------------
If dimensions are missing:
Wall height: 3 meters
Door height: 2.1 meters
Door width: 0.9 meters
Window height: 1.2 meters
Window sill: 0.9 meters
Slab thickness: 0.25 meters
Ceiling: 3 meters
These defaults may be overridden if dimensions exist.

--------------------------------------------------
WALL GENERATION
--------------------------------------------------
Walls must: follow centerlines, maintain constant thickness, join perfectly at intersections, support openings, be manifold, have clean normals, have proper UVs.

--------------------------------------------------
DOORS & WINDOWS
--------------------------------------------------
Do not create door geometry inside walls.
Instead: Create wall openings. Insert editable door/window objects. Respect hinge direction when visible.
Windows: Respect sill height, width, height.

--------------------------------------------------
ROOMS
--------------------------------------------------
Generate one floor mesh per room. Assign room names if labels exist.
Store metadata: room name, surface area, floor number.

--------------------------------------------------
MATERIALS
--------------------------------------------------
Assign procedural placeholder materials (Walls, Floor, Glass, Wood, Metal, Concrete). Keep them simple. No photorealism.

--------------------------------------------------
OBJECT NAMING & COLLECTIONS
--------------------------------------------------
Every object must have deterministic names (e.g. Wall_001, Door_003, Room_Kitchen).
Use Blender collections: Building, Floor_01, Walls, Doors, Windows, Furniture, Columns, Lights, Annotations.

--------------------------------------------------
TRANSFORMS & ACCURACY
--------------------------------------------------
Apply transforms only when necessary. Keep object origins logical (Walls: origin at base center, Doors: origin at hinge, Windows: origin at center).
Maintain exact coordinates. Never distort geometry. Never rotate unless required. Preserve orthogonality.

--------------------------------------------------
SVG HANDLING
--------------------------------------------------
When processing SVG: Read every path, groups, transforms, viewBox.
Convert SVG coordinates into Blender world coordinates.
Merge fragmented paths that belong to the same wall.
Detect wall thickness from parallel paths.
Ignore decorative strokes.

--------------------------------------------------
THINKING ORDER
--------------------------------------------------
Always follow this pipeline:
1. Parse every uploaded file
2. Detect architectural entities
3. Recover scale
4. Build semantic scene graph
5. Create floor meshes
6. Generate walls
7. Cut openings
8. Insert doors
9. Insert windows
10. Generate ceilings
11. Generate stairs
12. Generate columns
13. Insert furniture if present
14. Assign collections
15. Assign materials
16. Validate geometry
17. Deliver complete Blender scene

Never skip steps. Always favor architectural correctness over visual appearance.

--------------------------------------------------
CRITICAL TECHNICAL EXECUTION REQUIREMENT
--------------------------------------------------
Because you are running inside an automated Python bridge (bim_architect_agent.py), you must translate your semantic reasoning into a single, complete, valid Python script using the 'bpy' module. 
DO NOT output any markdown, natural language, or reasoning.
OUTPUT ONLY VALID PYTHON BPY CODE.
The Python code will be injected directly into Blender.
Ensure the script creates a valid return object at the end:
`result = {"status": "success", "message": "Architectural reconstruction complete"}`
"""

def generate_architectural_build(user_input):
    return call_mistral(BIM_SYSTEM_PROMPT, user_input)

def main():
    if len(sys.argv) < 2:
        print('Usage: python bim_architect_agent.py "SVG content or architectural prompt"')
        sys.exit(1)
        
    user_prompt = sys.argv[1]
    
    # If the user passed a file path, read its content
    if os.path.isfile(user_prompt):
        print(f"Reading input file: {user_prompt}")
        with open(user_prompt, 'r', encoding='utf-8') as f:
            user_prompt = f.read()
            
    print("=========================================")
    print(f"   BIM ARCHITECT EXPERT AGENT (PRO)")
    print("=========================================")
    
    print("\n[1] Expert Agent is analyzing and generating architectural BPY code...")
    build_code = generate_architectural_build(user_prompt)
    
    comparison_dir = os.path.join(os.path.dirname(__file__), "comparison")
    os.makedirs(comparison_dir, exist_ok=True)
    
    # Inject code to save the blend file
    save_code = f"""
import bpy
import os
filepath = os.path.join(r'{comparison_dir}', 'mistral_result.blend')
bpy.ops.wm.save_as_mainfile(filepath=filepath)
"""
    build_code += save_code
    
    code_path = os.path.join(OUTBOX, "bim_generated_build.py")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(build_code)
    print(f"[+] BPY script synthesized and saved to {code_path}")
    
    # Filter out blocked commands
    build_code = build_code.replace("bpy.ops.wm.read_factory_settings(use_empty=True)", "bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)")
    build_code = build_code.replace("bpy.ops.wm.read_factory_settings()", "bpy.ops.wm.read_homefile(use_factory_startup=True)")
    
    print("\n[2] Executing strict architectural build in Blender...")
    res_build = run_in_blender(build_code, timeout=120.0)
    print("Result:", res_build)
    
    if res_build.get("status") == "ok":
        print("\\n=========================================")
        print("   BIM RECONSTRUCTION SUCCESSFUL         ")
        print("=========================================")
    else:
        print("\\nReconstruction failed or timed out.")

if __name__ == "__main__":
    main()
