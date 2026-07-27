import os
import time
from mcp_client import run_in_blender

OUTBOX = os.path.join(os.path.dirname(__file__), "outbox")
os.makedirs(OUTBOX, exist_ok=True)

def generate_building_script():
    blend_path = os.path.join(OUTBOX, "auto_building.blend").replace('\\', '\\\\')
    
    code = f"""import bpy
import math
from mathutils import Euler

# 1. Clean Scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in list(bpy.data.collections): bpy.data.collections.remove(coll)
for mat in list(bpy.data.materials): bpy.data.materials.remove(mat)

# 2. Add simple walls and floor for testing
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.1))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (10, 8, 0.2)
bpy.ops.object.transform_apply(scale=True)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 4, 1.5))
wall1 = bpy.context.active_object
wall1.scale = (10, 0.2, 3)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5, 0, 1.5))
wall2 = bpy.context.active_object
wall2.scale = (0.2, 8, 3)

# 3. Add light
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = Euler((math.radians(45), math.radians(45), 0), 'XYZ')

out_path = r"{blend_path}"
bpy.ops.wm.save_as_mainfile(filepath=out_path)
result = {{"status": "success", "file": out_path, "message": "Building generated"}}
"""
    return code

def generate_render_script():
    blend_path = os.path.join(OUTBOX, "auto_building.blend").replace('\\', '\\\\')
    out_img1 = os.path.join(OUTBOX, "render_top.png").replace('\\', '\\\\')
    out_img2 = os.path.join(OUTBOX, "render_persp.png").replace('\\', '\\\\')
    
    code = f"""import bpy
import math
from mathutils import Euler
import os

# Ensure we are in the right file
bpy.ops.wm.open_mainfile(filepath=r"{blend_path}")

# Delete existing cameras to be safe
for obj in bpy.data.objects:
    if obj.type == 'CAMERA':
        bpy.data.objects.remove(obj, do_unlink=True)

# Create Top-Down Camera
bpy.ops.object.camera_add(location=(0, 0, 15))
cam_top = bpy.context.active_object
cam_top.name = "Cam_Top"
cam_top.data.type = 'ORTHO'
cam_top.data.ortho_scale = 12.0

# Create Perspective Camera
bpy.ops.object.camera_add(location=(12, -10, 8))
cam_persp = bpy.context.active_object
cam_persp.name = "Cam_Persp"
cam_persp.rotation_euler = Euler((math.radians(60), 0, math.radians(45)), 'XYZ')

scene = bpy.context.scene
scene.render.engine = 'CYCLES' if hasattr(bpy.types, 'CyclesRenderSettings') and bpy.context.preferences.addons.get('cycles') else 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 768

# Render Top
scene.camera = cam_top
scene.render.filepath = r"{out_img1}"
bpy.ops.render.render(write_still=True)

# Render Perspective
scene.camera = cam_persp
scene.render.filepath = r"{out_img2}"
bpy.ops.render.render(write_still=True)

result = {{"status": "success", "images": [r"{out_img1}", r"{out_img2}"]}}
"""
    return code

def main():
    print("=========================================")
    print("   AUTOMATED PIPELINE AGENT STARTED      ")
    print("=========================================")
    
    # 1. Generate Building Script
    print("\\n[1] Generating Building Script (Geometry + Lights)...")
    build_code = generate_building_script()
    with open(os.path.join(OUTBOX, "step1_build.py"), "w", encoding="utf-8") as f:
        f.write(build_code)
    
    # 2. Execute Building Script
    print("[2] Executing Building Script in Blender...")
    res_build = run_in_blender(build_code, timeout=60.0)
    print("Result:", res_build)
    
    if res_build.get("status") != "ok":
        print("Build failed. Exiting.")
        return
        
    time.sleep(1.0) # Small pause
    
    # 3. Generate Render Script
    print("\\n[3] Generating Render Script (Cameras + Rendering)...")
    render_code = generate_render_script()
    with open(os.path.join(OUTBOX, "step2_render.py"), "w", encoding="utf-8") as f:
        f.write(render_code)
    
    # 4. Execute Render Script
    print("[4] Executing Render Script in Blender...")
    res_render = run_in_blender(render_code, timeout=120.0) # Rendering takes longer
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
