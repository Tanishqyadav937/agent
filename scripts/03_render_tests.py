"""
03_render_tests.py
==================
Re-import bunny_character_lipsync.glb and render 6 test images:
  neutral, jawOpen, mouthSmile, mouthPucker, blink, viseme_A

Each render: 512x512, simple Eevee, camera positioned at head level.
Output: /Users/tanishqyadav/agent/renders/
"""
import bpy
import math
import os
from mathutils import Vector, Euler

RENDERS_DIR = "/Users/tanishqyadav/agent/renders"
GLB_IN      = "/Users/tanishqyadav/agent/bunny_character_lipsync.glb"
os.makedirs(RENDERS_DIR, exist_ok=True)

# ── Clean scene ───────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh)

# ── Import ────────────────────────────────────────────────────────────────────
bpy.ops.import_scene.gltf(filepath=GLB_IN)
print(f"[RENDER] Imported {GLB_IN}")

# ── Find objects ──────────────────────────────────────────────────────────────
mouth_obj = bpy.data.objects.get("FaceMouth")
eyes_obj  = bpy.data.objects.get("FaceEyes")
arm_obj   = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm_obj = obj
        break

assert mouth_obj, "FaceMouth not found in imported GLB"
assert eyes_obj,  "FaceEyes not found in imported GLB"
print(f"[RENDER] Found: FaceMouth, FaceEyes, armature={arm_obj.name if arm_obj else 'None'}")

# ── Setup camera ──────────────────────────────────────────────────────────────
cam_data = bpy.data.cameras.new("TestCam")
cam_obj  = bpy.data.objects.new("TestCam", cam_data)
bpy.context.collection.objects.link(cam_obj)

# Position camera: slightly in front of face, at face height
# Head bone tip is at ~Z=0.307, face center ~Z=0.22
# Camera at Y=-0.25 (in front), Z=0.26 (face level), looking toward origin
cam_obj.location = Vector((0.005, -0.28, 0.25))
# Point at face center
cam_obj.rotation_euler = Euler((math.radians(80), 0, 0), 'XYZ')
cam_data.lens = 85  # portrait focal length

bpy.context.scene.camera = cam_obj

# ── Lighting ──────────────────────────────────────────────────────────────────
# Key light
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun_obj  = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.location = Vector((0.5, -0.5, 1.0))
sun_obj.rotation_euler = Euler((math.radians(45), 0, math.radians(45)), 'XYZ')

# Fill light
fill_data = bpy.data.lights.new("Fill", type='POINT')
fill_data.energy = 30.0
fill_obj  = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-0.3, -0.2, 0.3))

# ── Render settings ──────────────────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine        = 'BLENDER_EEVEE'
scene.render.resolution_x  = 512
scene.render.resolution_y  = 512
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 16
except AttributeError:
    pass

# ── Helper: set shape key value ───────────────────────────────────────────────
def set_sk(obj, name, value):
    if obj.data.shape_keys:
        sk = obj.data.shape_keys.key_blocks.get(name)
        if sk:
            sk.value = value

def reset_all(obj):
    if obj.data.shape_keys:
        for sk in obj.data.shape_keys.key_blocks:
            if sk.name != 'Basis':
                sk.value = 0.0

# ── Render poses ─────────────────────────────────────────────────────────────
poses = [
    ("neutral",    {}),
    ("jaw_open",   {"FaceMouth": {"jawOpen": 1.0}}),
    ("smile",      {"FaceMouth": {"mouthSmile": 1.0}}),
    ("pucker",     {"FaceMouth": {"mouthPucker": 1.0}}),
    ("blink",      {"FaceEyes": {"blink.L": 1.0, "blink.R": 1.0}}),
    ("viseme_A",   {"FaceMouth": {"viseme_A": 1.0}}),
]

object_map = {"FaceMouth": mouth_obj, "FaceEyes": eyes_obj}

rendered = []
for pose_name, controls in poses:
    # Reset all
    reset_all(mouth_obj)
    reset_all(eyes_obj)

    # Apply pose
    for obj_name, keys in controls.items():
        obj = object_map[obj_name]
        for sk_name, val in keys.items():
            set_sk(obj, sk_name, val)

    # Update scene
    bpy.context.view_layer.update()

    # Render
    out_path = os.path.join(RENDERS_DIR, f"{pose_name}.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    size = os.path.getsize(out_path)
    rendered.append({"pose": pose_name, "path": out_path, "size_bytes": size})
    print(f"[RENDER] {pose_name}: {out_path} ({size:,} bytes)")

# Reset
reset_all(mouth_obj)
reset_all(eyes_obj)

print(f"\n[RENDER] Done. {len(rendered)} images in {RENDERS_DIR}")
for r in rendered:
    print(f"  {r['pose']:15s}: {r['size_bytes']:,} bytes")
