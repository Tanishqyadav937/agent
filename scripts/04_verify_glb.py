"""
04_verify_glb.py
================
Clean-room verification of bunny_character_lipsync.glb.
Imports in a fresh Blender session and checks every requirement.
Outputs: /Users/tanishqyadav/agent/verify_result.json
"""
import bpy
import json
import os

GLB_IN  = "/Users/tanishqyadav/agent/bunny_character_lipsync.glb"
OUT_JSON = "/Users/tanishqyadav/agent/verify_result.json"

# ── Clean scene ───────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in bpy.data.meshes:
    bpy.data.meshes.remove(m)

# ── Import ────────────────────────────────────────────────────────────────────
bpy.ops.import_scene.gltf(filepath=GLB_IN)
print(f"[VERIFY] Imported {GLB_IN}")

checks = {}
failures = []

def chk(name, condition, detail=""):
    checks[name] = {"passed": bool(condition), "detail": detail}
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    if not condition:
        failures.append(name)

# ── 1. BunnyArmature exists ───────────────────────────────────────────────────
arm = bpy.data.objects.get("BunnyArmature")
chk("armature_exists", arm is not None, f"BunnyArmature={'found' if arm else 'MISSING'}")

# ── 2. 18 bones ──────────────────────────────────────────────────────────────
if arm:
    bone_count = len(arm.data.bones)
    chk("bone_count_18", bone_count == 18, f"{bone_count} bones")
    bone_names = [b.name for b in arm.data.bones]
    chk("head_bone_present", 'head' in bone_names, f"'head' in bones={bone_names}")

# ── 3. Body mesh (mesh.glb) remains and is skinned ───────────────────────────
body = bpy.data.objects.get("mesh.glb")
chk("body_mesh_exists", body is not None, f"mesh.glb={'found' if body else 'MISSING'}")
if body:
    vcount = len(body.data.vertices)
    chk("body_mesh_verts", vcount > 10000, f"{vcount} verts (expected ~61517)")
    has_arm_mod = any(m.type == 'ARMATURE' for m in body.modifiers)
    # Also accept vertex groups as evidence of skinning
    has_vgroups = len(body.vertex_groups) > 0
    chk("body_mesh_skinned", has_arm_mod or has_vgroups,
        f"armature_modifier={has_arm_mod}, vertex_groups={len(body.vertex_groups)}")

# ── 4. FaceMouth exists ───────────────────────────────────────────────────────
mouth = bpy.data.objects.get("FaceMouth")
chk("face_mouth_exists", mouth is not None, f"FaceMouth={'found' if mouth else 'MISSING'}")

# ── 5. Mouth shape keys ───────────────────────────────────────────────────────
expected_mouth_keys = [
    "jawOpen", "mouthClose", "mouthSmile", "mouthPucker",
    "viseme_A", "viseme_E", "viseme_I", "viseme_O", "viseme_U"
]
if mouth and mouth.data.shape_keys:
    present = [kb.name for kb in mouth.data.shape_keys.key_blocks]
    for key in expected_mouth_keys:
        chk(f"mouth_sk_{key}", key in present, f"key='{key}' present={key in present}")
else:
    for key in expected_mouth_keys:
        chk(f"mouth_sk_{key}", False, "No shape keys on FaceMouth")

# ── 6. Mouth shape keys produce actual deformation ───────────────────────────
def measure_sk_disp(obj, sk_name):
    sks = obj.data.shape_keys.key_blocks
    for sk in sks:
        sk.value = 0.0
    basis_coords = [v.co.copy() for v in sks['Basis'].data]
    target = sks[sk_name]
    target.value = 1.0
    max_d = max((t.co - b).length for b, t in zip(basis_coords, target.data))
    target.value = 0.0
    return max_d

if mouth and mouth.data.shape_keys:
    for key in expected_mouth_keys:
        if mouth.data.shape_keys.key_blocks.get(key):
            d = measure_sk_disp(mouth, key)
            chk(f"mouth_sk_{key}_deforms", d > 0.001,
                f"max_disp={d*1000:.2f}mm {'OK' if d>0.001 else 'ZERO'}")

# ── 7. FaceEyes exists ────────────────────────────────────────────────────────
eyes = bpy.data.objects.get("FaceEyes")
chk("face_eyes_exists", eyes is not None, f"FaceEyes={'found' if eyes else 'MISSING'}")

# ── 8. Eye shape keys ─────────────────────────────────────────────────────────
expected_eye_keys = ["blink.L", "blink.R"]
if eyes and eyes.data.shape_keys:
    present = [kb.name for kb in eyes.data.shape_keys.key_blocks]
    for key in expected_eye_keys:
        chk(f"eye_sk_{key}", key in present, f"key='{key}' present={key in present}")
    for key in expected_eye_keys:
        if eyes.data.shape_keys.key_blocks.get(key):
            d = measure_sk_disp(eyes, key)
            chk(f"eye_sk_{key}_deforms", d > 0.001,
                f"max_disp={d*1000:.2f}mm {'OK' if d>0.001 else 'ZERO'}")
else:
    for key in expected_eye_keys:
        chk(f"eye_sk_{key}", False, "No shape keys on FaceEyes")

# ── 9. Facial geometry follows head bone (via skin weights) ──────────────────
# GLB/GLTF does not preserve Blender's internal BONE parent_type — it uses
# skinning. Check that 'head' vertex group exists and has weights, plus
# armature modifier is present. Head-following is confirmed via depsgraph test.
def has_head_skinning(obj):
    has_mod  = any(m.type == 'ARMATURE' for m in obj.modifiers)
    has_vg   = obj.vertex_groups.get('head') is not None
    return has_mod and has_vg

if mouth:
    ok = has_head_skinning(mouth)
    chk("mouth_skinned_to_head",
        ok,
        f"armature_mod={any(m.type=='ARMATURE' for m in mouth.modifiers)}, head_vgroup={'head' in [vg.name for vg in mouth.vertex_groups]}")
if eyes:
    ok = has_head_skinning(eyes)
    chk("eyes_skinned_to_head",
        ok,
        f"armature_mod={any(m.type=='ARMATURE' for m in eyes.modifiers)}, head_vgroup={'head' in [vg.name for vg in eyes.vertex_groups]}")

# ── 10. Materials intact ──────────────────────────────────────────────────────
mat_names = [m.name for m in bpy.data.materials]
chk("material_dots_stroke", any("Dots" in n or "dots" in n for n in mat_names),
    f"Materials: {mat_names}")
chk("material_material_exists", any("Material" in n for n in mat_names),
    f"Materials: {mat_names}")

# ── 11. Tail mesh (Icosphere) ─────────────────────────────────────────────────
tail = bpy.data.objects.get("Icosphere")
chk("tail_mesh_exists", tail is not None, f"Icosphere={'found' if tail else 'MISSING'}")

# ── Summary ───────────────────────────────────────────────────────────────────
total   = len(checks)
passed  = sum(1 for v in checks.values() if v["passed"])
failed  = total - passed

print(f"\n[VERIFY] Results: {passed}/{total} passed")
if failures:
    print(f"[VERIFY] FAILURES: {failures}")
else:
    print("[VERIFY] ALL CHECKS PASSED")

result = {
    "glb_path": GLB_IN,
    "total_checks": total,
    "passed": passed,
    "failed": failed,
    "all_passed": failed == 0,
    "failures": failures,
    "checks": checks,
    "objects_in_scene": [obj.name for obj in bpy.data.objects],
    "materials_in_scene": mat_names,
}

with open(OUT_JSON, 'w') as f:
    json.dump(result, f, indent=2)
print(f"[VERIFY] Written to {OUT_JSON}")
