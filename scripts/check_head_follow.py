"""
Check head-following by:
1. Verifying facial meshes have skin data OR are in armature node hierarchy
2. Posing the head bone and checking if facial mesh world positions change
"""
import bpy
import json
from mathutils import Vector, Matrix
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for m in bpy.data.meshes: bpy.data.meshes.remove(m)
bpy.ops.import_scene.gltf(filepath="/Users/tanishqyadav/agent/bunny_character_lipsync.glb")

arm = bpy.data.objects.get("BunnyArmature")
mouth = bpy.data.objects.get("BunnyMouth")
eye_l = bpy.data.objects.get("BunnyEye.L")
eye_r = bpy.data.objects.get("BunnyEye.R")

result = {}

print("=== HEAD FOLLOWING CHECK ===")

for obj in [mouth, eye_l, eye_r]:
    if obj is None:
        continue
    name = obj.name
    info = {
        "parent": obj.parent.name if obj.parent else None,
        "parent_type": obj.parent_type,
        "parent_bone": obj.parent_bone,
        "has_armature_modifier": any(m.type == 'ARMATURE' for m in obj.modifiers),
        "vertex_groups": [vg.name for vg in obj.vertex_groups],
        "world_location_rest": list(obj.matrix_world.translation),
    }
    print(f"\n  {name}:")
    for k,v in info.items():
        print(f"    {k}: {v}")
    result[name] = info

# Now pose the head bone and check if facial meshes move
print("\n=== POSE TEST: rotate head 30deg, check mouth world pos changes ===")

if arm and mouth:
    bpy.context.view_layer.update()
    
    # Record initial world position
    pos_before = mouth.matrix_world.translation.copy()
    
    # Pose the head bone
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    head_pbone = arm.pose.bones.get('head')
    if head_pbone:
        import mathutils
        head_pbone.rotation_mode = 'XYZ'
        head_pbone.rotation_euler = mathutils.Euler((math.radians(30), 0, 0), 'XYZ')
        bpy.context.view_layer.update()
        
        pos_after = mouth.matrix_world.translation.copy()
        delta = (pos_after - pos_before).length
        
        print(f"  Mouth world pos BEFORE: {[round(x,4) for x in pos_before]}")
        print(f"  Mouth world pos AFTER:  {[round(x,4) for x in pos_after]}")
        print(f"  Delta: {delta*1000:.2f}mm")
        
        moved = delta > 0.001
        result["head_pose_test"] = {
            "pos_before": list(pos_before),
            "pos_after": list(pos_after),
            "delta_m": round(delta, 6),
            "mouth_follows_head": moved
        }
        print(f"  Mouth follows head bone: {'YES' if moved else 'NO - PARENTING NOT WORKING'}")
        
        # Reset
        head_pbone.rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')
    bpy.ops.object.mode_set(mode='OBJECT')

with open("/Users/tanishqyadav/agent/head_follow_check.json", 'w') as f:
    json.dump(result, f, indent=2)
print("\n[CHECK] Done")
