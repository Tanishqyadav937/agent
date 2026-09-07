"""
check_head_follow_v2.py
Proper head-follow test using depsgraph evaluated mesh positions.
In background mode, matrix_world on the original object won't update from pose.
Use depsgraph.objects[name].evaluated_get(depsgraph).matrix_world instead.
"""
import bpy, json, math
from mathutils import Euler

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for m in bpy.data.meshes: bpy.data.meshes.remove(m)

bpy.ops.import_scene.gltf(filepath="/Users/tanishqyadav/agent/bunny_character_lipsync.glb")

arm   = bpy.data.objects.get("BunnyArmature")
mouth = bpy.data.objects.get("FaceMouth")
eyes  = bpy.data.objects.get("FaceEyes")

assert arm,   "BunnyArmature not found"
assert mouth, "FaceMouth not found"
assert eyes,  "FaceEyes not found"

print(f"[FOLLOW] Armature: {arm.name}")
print(f"[FOLLOW] FaceMouth vertex_groups: {[vg.name for vg in mouth.vertex_groups]}")
print(f"[FOLLOW] FaceEyes  vertex_groups: {[vg.name for vg in eyes.vertex_groups]}")
print(f"[FOLLOW] FaceMouth armature_mod:  {[m.type for m in mouth.modifiers]}")

# ── Helper: get evaluated world position of first vertex ─────────────────────
def get_eval_vert0_world(obj, depsgraph):
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    if mesh_eval and len(mesh_eval.vertices) > 0:
        # Transform vertex 0 by the evaluated world matrix
        v_local = mesh_eval.vertices[0].co
        v_world = obj_eval.matrix_world @ v_local
        obj_eval.to_mesh_clear()
        return v_world.copy()
    return None

# ── Test 1: rest pose ─────────────────────────────────────────────────────────
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()

pos_rest_mouth = get_eval_vert0_world(mouth, depsgraph)
pos_rest_eyes  = get_eval_vert0_world(eyes,  depsgraph)

print(f"\n[FOLLOW] REST pose:")
print(f"  FaceMouth vert0 world: {[round(x,4) for x in pos_rest_mouth] if pos_rest_mouth else 'None'}")
print(f"  FaceEyes  vert0 world: {[round(x,4) for x in pos_rest_eyes]  if pos_rest_eyes  else 'None'}")

# ── Test 2: pose head bone ────────────────────────────────────────────────────
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

head_pbone = arm.pose.bones.get('head')
head_pbone.rotation_mode = 'XYZ'
head_pbone.rotation_euler = Euler((math.radians(30), 0, 0), 'XYZ')

bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()

pos_posed_mouth = get_eval_vert0_world(mouth, depsgraph)
pos_posed_eyes  = get_eval_vert0_world(eyes,  depsgraph)

print(f"\n[FOLLOW] HEAD +30° rotation:")
print(f"  FaceMouth vert0 world: {[round(x,4) for x in pos_posed_mouth] if pos_posed_mouth else 'None'}")
print(f"  FaceEyes  vert0 world: {[round(x,4) for x in pos_posed_eyes]  if pos_posed_eyes  else 'None'}")

delta_mouth = (pos_posed_mouth - pos_rest_mouth).length if (pos_posed_mouth and pos_rest_mouth) else 0
delta_eyes  = (pos_posed_eyes  - pos_rest_eyes ).length if (pos_posed_eyes  and pos_rest_eyes ) else 0

print(f"\n  Mouth delta: {delta_mouth*1000:.2f}mm — {'FOLLOWS HEAD ✓' if delta_mouth > 0.001 else 'STATIC ✗'}")
print(f"  Eyes  delta: {delta_eyes*1000:.2f}mm  — {'FOLLOWS HEAD ✓' if delta_eyes  > 0.001 else 'STATIC ✗'}")

# Reset
head_pbone.rotation_euler = Euler((0, 0, 0), 'XYZ')
bpy.ops.object.mode_set(mode='OBJECT')

result = {
    "mouth_follows_head": delta_mouth > 0.001,
    "eyes_follow_head": delta_eyes > 0.001,
    "mouth_delta_mm": round(delta_mouth * 1000, 2),
    "eyes_delta_mm": round(delta_eyes * 1000, 2),
}
with open("/Users/tanishqyadav/agent/head_follow_result.json", 'w') as f:
    json.dump(result, f, indent=2)
print(f"\n[FOLLOW] Done: {result}")
