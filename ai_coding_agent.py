import os
import sys
import json
import urllib.request
import time
from mcp_client import run_in_blender

OUTBOX = os.path.join(os.path.dirname(__file__), "outbox")
os.makedirs(OUTBOX, exist_ok=True)

API_KEY = os.getenv("GEMINI_API_KEY")

def call_gemini(system_prompt, user_prompt):
    if not API_KEY:
        print("ERROR: Please set the GEMINI_API_KEY environment variable.")
        sys.exit(1)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={API_KEY}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [{
            "parts": [{"text": user_prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    print("Calling Gemini API...")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up markdown code blocks if present
            if text.startswith("```python"):
                text = text.split("```python")[1]
            elif text.startswith("```"):
                text = text.split("```")[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
                
            return text.strip()
    except Exception as e:
        print(f"API Error: {e}")
        sys.exit(1)

def generate_building_script(prompt):
    blend_path = os.path.join(OUTBOX, "ai_building.blend").replace('\\', '\\\\')
    
    system_prompt = f"""You are an expert Python Blender developer.
Write a script that uses the 'bpy' module to construct a 3D model based on the user's prompt.
RULES:
1. Output ONLY valid Python code, no markdown, no explanations.
2. The script must clean the scene first.
3. The script must save the file to `{blend_path}` at the end using `bpy.ops.wm.save_as_mainfile(filepath=out_path)`.
4. The script MUST end with: `result = {{"status": "success", "file": out_path}}`
"""
    return call_gemini(system_prompt, prompt)

def generate_render_script(prompt):
    blend_path = os.path.join(OUTBOX, "ai_building.blend").replace('\\', '\\\\')
    out_img1 = os.path.join(OUTBOX, "render_top.png").replace('\\', '\\\\')
    out_img2 = os.path.join(OUTBOX, "render_persp.png").replace('\\', '\\\\')
    
    system_prompt = f"""You are an expert Python Blender developer.
Write a script that uses the 'bpy' module to open a `.blend` file, set up cameras/lighting, and render images based on the user's concept.
RULES:
1. Output ONLY valid Python code, no markdown, no explanations.
2. The script MUST start by opening: `bpy.ops.wm.open_mainfile(filepath=r"{blend_path}")`
3. Set up a Top-Down orthographic camera and render to `{out_img1}`
4. Set up a Perspective camera and render to `{out_img2}`
5. The script MUST end with: `result = {{"status": "success", "images": [r"{out_img1}", r"{out_img2}"]}}`
"""
    return call_gemini(system_prompt, prompt)

def main():
    if len(sys.argv) < 2:
        print('Usage: python ai_coding_agent.py "Describe what you want to build"')
        sys.exit(1)
        
    user_prompt = sys.argv[1]
    print("=========================================")
    print(f"   AI CODING AGENT STARTED")
    print(f"   Prompt: {user_prompt}")
    print("=========================================")
    
    # 1. Generate Building Script
    print("\\n[1] AI is writing Building Script...")
    build_code = generate_building_script(user_prompt)
    with open(os.path.join(OUTBOX, "step1_build.py"), "w", encoding="utf-8") as f:
        f.write(build_code)
    
    # 2. Execute Building Script
    print("[2] Executing Building Script in Blender...")
    res_build = run_in_blender(build_code, timeout=60.0)
    print("Result:", res_build)
    
    if res_build.get("status") != "ok":
        print("Build failed. Exiting.")
        return
        
    time.sleep(1.0)
    
    # 3. Generate Render Script
    print("\\n[3] AI is writing Render Script...")
    render_code = generate_render_script(user_prompt)
    with open(os.path.join(OUTBOX, "step2_render.py"), "w", encoding="utf-8") as f:
        f.write(render_code)
    
    # 4. Execute Render Script
    print("[4] Executing Render Script in Blender...")
    res_render = run_in_blender(render_code, timeout=120.0)
    print("Result:", res_render)
    
    if res_render.get("status") == "ok":
        print("\\n=========================================")
        print("   PIPELINE COMPLETED SUCCESSFULLY       ")
        print("=========================================")
        print("Outputs saved in:", OUTBOX)
    else:
        print("\\nPipeline failed during rendering.")

if __name__ == "__main__":
    main()
