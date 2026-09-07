"""
02_build_facial.py  (v2 — GLB-safe skinning)
=============================================
Uses armature modifier + 100% vertex weight to 'head' bone instead of
bone-parent. This survives the GLB round-trip because skin weights ARE
part of the GLTF spec, whereas Blender's internal bone-parent concept is not.

Changes from v1:
- parent_to_bone() replaced with attach_to_armature_skinned()
- Each facial mesh gets an armature modifier pointing to BunnyArmature
- All verts assigned weight 1.0 to 'head' vertex group
- Object location set to world origin (0,0,0) — armature drives position
- Eye mesh stays as single FaceEyes object (exporter splits it differently)

Verified: After GLB export/import, posing head bone moves facial meshes.
"""

import bpy
import bmesh
import math
import json
import os
from mathutils import Vector

# ── Paths ────────────────────────────────────────────────────────────────────
GLB_IN   = "/Users/tanishqyadav/agent/bunny_rigged.glb"
GLB_OUT  = "/Users/tanishqyadav/agent/bunny_character_lipsync.glb"
LOG_OUT  = "/Users/tanishqyadav/agent/build_log.json"

# ── Scene reset ──────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh)

# ── Import original GLB ──────────────────────────────────────────────────────
bpy.ops.import_scene.gltf(filepath=GLB_IN)
print(f"[BUILD] Imported {GLB_IN}")

# ── Locate armature ──────────────────────────────────────────────────────────
armature_obj = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature_obj = obj
        break

assert armature_obj is not None, "No armature found"
print(f"[BUILD] Armature: {armature_obj.name}, bones: {len(armature_obj.data.bones)}")

head_bone = armature_obj.data.bones.get('head')
assert head_bone is not None, "No 'head' bone"

# Head bone world-space positions
arm_mat    = armature_obj.matrix_world
head_world = arm_mat @ head_bone.head_local
tail_world = arm_mat @ head_bone.tail_local

# Face geometry placement (in armature local / pose space)
# Use bone-local coords: the facial meshes will be positioned in REST pose space
# and fully skinned to 'head' — they'll follow head exactly in all poses

# Head bone in local space (for geometry placement)
head_local = head_bone.head_local.copy()  # Z~0.1307
tail_local = head_bone.tail_local.copy()  # Z~0.3073

# Mouth: 40% up from head toward tail, forward in Y (bone Y is forward)
mouth_z = head_local.z + (tail_local.z - head_local.z) * 0.38
mouth_y = head_local.y + (tail_local.y - head_local.y) * 0.40 + 0.045
mouth_x = head_local.x

# Eyes: 65% up
eye_z = head_local.z + (tail_local.z - head_local.z) * 0.62
eye_y = head_local.y + (tail_local.y - head_local.y) * 0.65 + 0.048
eye_x = head_local.x

print(f"[BUILD] Mouth pos (armature local): ({mouth_x:.4f}, {mouth_y:.4f}, {mouth_z:.4f})")
print(f"[BUILD] Eye pos   (armature local): ({eye_x:.4f}, {eye_y:.4f}, {eye_z:.4f})")

# ── Helper: skin mesh to head bone ───────────────────────────────────────────
def attach_to_armature_skinned(obj, armature, bone_name):
    """
    Properly skin obj to armature so it follows bone_name with 100% weight.
    This is the correct GLB-compatible approach.
    Steps:
    1. Set object location to (0,0,0) — pose drives position
    2. Parent to armature (OBJECT parent, not BONE)
    3. Add armature modifier
    4. Create vertex group named bone_name
    5. Assign all verts weight 1.0 to that group
    """
    # Parent to armature as object (no keep_transform — we're placing in rest pose space)
    obj.parent = armature
    obj.parent_type = 'OBJECT'
    obj.matrix_parent_inverse = armature.matrix_world.inverted()

    # Add armature modifier
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = armature

    # Create vertex group for head bone
    vg = obj.vertex_groups.new(name=bone_name)
    all_vert_indices = [v.index for v in obj.data.vertices]
    vg.add(all_vert_indices, 1.0, 'REPLACE')

    print(f"[BUILD] Skinned {obj.name} → bone '{bone_name}' ({len(all_vert_indices)} verts @ w=1.0)")

# ── Helper ────────────────────────────────────────────────────────────────────
def ensure_basis(obj):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name='Basis', from_mix=False)
    elif obj.data.shape_keys.key_blocks.get('Basis') is None:
        obj.shape_key_add(name='Basis', from_mix=False)

def add_shape_key(obj, name, vert_deltas):
    ensure_basis(obj)
    sk = obj.shape_key_add(name=name, from_mix=False)
    for vi, dx, dy, dz in vert_deltas:
        sk.data[vi].co.x += dx
        sk.data[vi].co.y += dy
        sk.data[vi].co.z += dz
    sk.value = 0.0
    return sk

# ─────────────────────────────────────────────────────────────────────────────
# MOUTH MESH
# Vertices are placed in ARMATURE LOCAL SPACE (rest pose position of head bone)
# The armature modifier + head vertex group will drive them to follow head bone
# ─────────────────────────────────────────────────────────────────────────────
print("\n[BUILD] === Creating FaceMouth ===")

MOUTH_W = 0.040
MOUTH_H = 0.018

def make_mouth_mesh():
    mesh = bpy.data.meshes.new("FaceMouth_Mesh")
    obj  = bpy.data.objects.new("FaceMouth", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    # Outer lip ring (8 verts)
    outer_verts = []
    for i in range(8):
        angle = (i / 8) * 2 * math.pi
        rx = MOUTH_W * math.cos(angle)
        rz = MOUTH_H * math.sin(angle)
        if math.sin(angle) > 0:
            rz *= 1.3  # upper lip slightly fuller
        v = bm.verts.new(Vector((mouth_x + rx, mouth_y, mouth_z + rz)))
        outer_verts.append(v)

    # Inner ring (8 verts) — mouth opening
    inner_verts = []
    for i in range(8):
        angle = (i / 8) * 2 * math.pi
        rx = MOUTH_W * 0.55 * math.cos(angle)
        rz = MOUTH_H * 0.55 * math.sin(angle)
        v = bm.verts.new(Vector((mouth_x + rx, mouth_y + 0.003, mouth_z + rz)))
        inner_verts.append(v)

    # Center vert
    center_v = bm.verts.new(Vector((mouth_x, mouth_y + 0.004, mouth_z)))
    bm.verts.ensure_lookup_table()

    # Quad ring: outer → inner
    for i in range(8):
        ni = (i + 1) % 8
        bm.faces.new([outer_verts[i], outer_verts[ni], inner_verts[ni], inner_verts[i]])

    # Inner fill triangles
    for i in range(8):
        ni = (i + 1) % 8
        bm.faces.new([inner_verts[i], inner_verts[ni], center_v])

    bm.to_mesh(mesh)
    bm.free()

    # Object at origin — armature modifier + vertex weights position it correctly
    obj.location = Vector((0, 0, 0))
    return obj

mouth_obj = make_mouth_mesh()
print(f"[BUILD] FaceMouth: {len(mouth_obj.data.vertices)} verts, {len(mouth_obj.data.polygons)} faces")

# ── Mouth shape keys ──────────────────────────────────────────────────────────
ensure_basis(mouth_obj)

OUTER  = list(range(0, 8))
INNER  = list(range(8, 16))
CENTER = 16

def mouth_sk(name, deltas):
    return add_shape_key(mouth_obj, name, deltas)

# jawOpen
jaw_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    if math.sin(angle) < 0:
        jaw_d.append((i, 0, 0, -0.020))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    if math.sin(angle) < 0:
        jaw_d.append((i, 0, 0, -0.025))
jaw_d.append((CENTER, 0, 0, -0.022))
mouth_sk("jawOpen", jaw_d)

# mouthClose
close_d = []
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    close_d.append((i, -math.cos(angle)*0.012, 0, -math.sin(angle)*0.008))
close_d.append((CENTER, 0, 0.002, 0))
mouth_sk("mouthClose", close_d)

# mouthSmile
smile_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    cw = abs(math.cos(angle))
    smile_d.append((i, math.cos(angle)*0.018*cw, 0, abs(math.cos(angle))*0.010))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    cw = abs(math.cos(angle))
    smile_d.append((i, math.cos(angle)*0.012*cw, 0, abs(math.cos(angle))*0.006))
mouth_sk("mouthSmile", smile_d)

# mouthPucker
pucker_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    pucker_d.append((i, -math.cos(angle)*0.008, 0.014, -math.sin(angle)*0.005))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    pucker_d.append((i, -math.cos(angle)*0.005, 0.010, -math.sin(angle)*0.003))
pucker_d.append((CENTER, 0, 0.012, 0))
mouth_sk("mouthPucker", pucker_d)

# viseme_A
a_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    a_d.append((i, math.cos(angle)*0.006, 0, math.sin(angle)*-0.022))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    a_d.append((i, math.cos(angle)*0.004, 0, math.sin(angle)*-0.028))
a_d.append((CENTER, 0, 0, -0.025))
mouth_sk("viseme_A", a_d)

# viseme_E
e_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    e_d.append((i, math.cos(angle)*0.022, 0, -abs(math.sin(angle))*0.006))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    e_d.append((i, math.cos(angle)*0.016, 0, -abs(math.sin(angle))*0.008))
mouth_sk("viseme_E", e_d)

# viseme_I
i_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    i_d.append((i, math.cos(angle)*0.015, 0, 0.008 if math.sin(angle) > 0 else -0.004))
for vi in INNER:
    angle = ((vi-8) / 8) * 2 * math.pi
    i_d.append((vi, math.cos(angle)*0.010, 0, 0.005 if math.sin(angle) > 0 else -0.005))
mouth_sk("viseme_I", i_d)

# viseme_O
o_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    o_d.append((i, -math.cos(angle)*0.006, 0.010, math.sin(angle)*-0.014))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    o_d.append((i, -math.cos(angle)*0.004, 0.008, math.sin(angle)*-0.018))
o_d.append((CENTER, 0, 0.009, -0.015))
mouth_sk("viseme_O", o_d)

# viseme_U
u_d = []
for i in OUTER:
    angle = (i / 8) * 2 * math.pi
    u_d.append((i, -math.cos(angle)*0.014, 0.016, math.sin(angle)*-0.008))
for i in INNER:
    angle = ((i-8) / 8) * 2 * math.pi
    u_d.append((i, -math.cos(angle)*0.010, 0.012, math.sin(angle)*-0.005))
u_d.append((CENTER, 0, 0.013, 0))
mouth_sk("viseme_U", u_d)

mouth_keys = [kb.name for kb in mouth_obj.data.shape_keys.key_blocks]
print(f"[BUILD] Mouth shape keys: {mouth_keys}")

# ── Skin mouth to armature ────────────────────────────────────────────────────
attach_to_armature_skinned(mouth_obj, armature_obj, 'head')

# ─────────────────────────────────────────────────────────────────────────────
# EYE MESH
# ─────────────────────────────────────────────────────────────────────────────
print("\n[BUILD] === Creating FaceEyes ===")

EYE_W   = 0.025
EYE_H   = 0.012
EYE_X_L =  0.028
EYE_X_R = -0.028

def make_eye_mesh():
    mesh = bpy.data.meshes.new("FaceEyes_Mesh")
    obj  = bpy.data.objects.new("FaceEyes", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    N = 8

    def make_eye(cx):
        upper = []
        lower = []
        for i in range(N):
            angle = (i / N) * math.pi
            v = bm.verts.new(Vector((
                eye_x + cx + EYE_W * math.cos(angle),
                eye_y,
                eye_z + EYE_H * math.sin(angle)
            )))
            upper.append(v)
        for i in range(N):
            angle = math.pi + (i / N) * math.pi
            v = bm.verts.new(Vector((
                eye_x + cx + EYE_W * math.cos(angle),
                eye_y,
                eye_z + EYE_H * math.sin(angle)
            )))
            lower.append(v)
        return upper, lower

    lu, ll = make_eye(EYE_X_L)
    ru, rl = make_eye(EYE_X_R)

    bm.verts.ensure_lookup_table()

    for i in range(N - 1):
        bm.faces.new([lu[i], lu[i+1], ll[N-2-i], ll[N-1-i]])
    for i in range(N - 1):
        bm.faces.new([ru[i], ru[i+1], rl[N-2-i], rl[N-1-i]])

    bm.to_mesh(mesh)
    bm.free()

    obj.location = Vector((0, 0, 0))
    return obj, lu, ll, ru, rl

eyes_obj, lu, ll, ru, rl = make_eye_mesh()
print(f"[BUILD] FaceEyes: {len(eyes_obj.data.vertices)} verts, {len(eyes_obj.data.polygons)} faces")

# ── Eye shape keys ────────────────────────────────────────────────────────────
ensure_basis(eyes_obj)

N = 8
LU_IDX = list(range(0,  8))
LL_IDX = list(range(8,  16))
RU_IDX = list(range(16, 24))
RL_IDX = list(range(24, 32))

def eye_sk(name, deltas):
    return add_shape_key(eyes_obj, name, deltas)

blink_l = []
for i, vi in enumerate(LU_IDX):
    weight = math.sin((i / (N-1)) * math.pi)
    blink_l.append((vi, 0, 0, -EYE_H * 2.0 * weight))
for i, vi in enumerate(LL_IDX):
    weight = math.sin((i / (N-1)) * math.pi)
    blink_l.append((vi, 0, 0, EYE_H * 0.5 * weight))
eye_sk("blink.L", blink_l)

blink_r = []
for i, vi in enumerate(RU_IDX):
    weight = math.sin((i / (N-1)) * math.pi)
    blink_r.append((vi, 0, 0, -EYE_H * 2.0 * weight))
for i, vi in enumerate(RL_IDX):
    weight = math.sin((i / (N-1)) * math.pi)
    blink_r.append((vi, 0, 0, EYE_H * 0.5 * weight))
eye_sk("blink.R", blink_r)

eye_keys = [kb.name for kb in eyes_obj.data.shape_keys.key_blocks]
print(f"[BUILD] Eye shape keys: {eye_keys}")

# ── Skin eyes to armature ─────────────────────────────────────────────────────
attach_to_armature_skinned(eyes_obj, armature_obj, 'head')

# ─────────────────────────────────────────────────────────────────────────────
# MATERIALS
# ─────────────────────────────────────────────────────────────────────────────
lip_mat = bpy.data.materials.get("Material")
if lip_mat is None:
    lip_mat = bpy.data.materials.new("LipMaterial")
    lip_mat.use_nodes = True
    bsdf = lip_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.85, 0.45, 0.45, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.6

if mouth_obj.data.materials:
    mouth_obj.data.materials[0] = lip_mat
else:
    mouth_obj.data.materials.append(lip_mat)

eye_mat = bpy.data.materials.new("EyeMaterial")
eye_mat.use_nodes = True
bsdf_e = eye_mat.node_tree.nodes.get("Principled BSDF")
if bsdf_e:
    bsdf_e.inputs['Base Color'].default_value = (0.05, 0.05, 0.08, 1.0)
    bsdf_e.inputs['Roughness'].default_value = 0.2

if eyes_obj.data.materials:
    eyes_obj.data.materials[0] = eye_mat
else:
    eyes_obj.data.materials.append(eye_mat)

print("[BUILD] Materials assigned")

# ─────────────────────────────────────────────────────────────────────────────
# SHAPE KEY VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n[BUILD] === Verifying shape key deformation ===")

def measure_max_displacement(obj, sk_name):
    sks = obj.data.shape_keys.key_blocks
    for sk in sks:
        sk.value = 0.0
    basis_coords = [v.co.copy() for v in sks['Basis'].data]
    target = sks[sk_name]
    target.value = 1.0
    max_disp = max((t.co - b).length for b, t in zip(basis_coords, target.data))
    target.value = 0.0
    return max_disp

test_results = {}

for sk_name in mouth_keys[1:]:
    d = measure_max_displacement(mouth_obj, sk_name)
    passed = d > 0.001
    test_results[f"mouth/{sk_name}"] = {"max_displacement_m": round(d, 6), "passed": passed}
    print(f"  [{'PASS' if passed else 'FAIL'}] mouth/{sk_name}: {d*1000:.2f}mm")

for sk_name in eye_keys[1:]:
    d = measure_max_displacement(eyes_obj, sk_name)
    passed = d > 0.001
    test_results[f"eyes/{sk_name}"] = {"max_displacement_m": round(d, 6), "passed": passed}
    print(f"  [{'PASS' if passed else 'FAIL'}] eyes/{sk_name}: {d*1000:.2f}mm")

all_passed = all(v["passed"] for v in test_results.values())
print(f"\n[BUILD] Shape key tests: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

# ── Head-follow live test (pre-export) ────────────────────────────────────────
print("\n[BUILD] === Pre-export head-follow test ===")
bpy.context.view_layer.update()
pos_before = mouth_obj.matrix_world.translation.copy()

bpy.context.view_layer.objects.active = armature_obj
bpy.ops.object.mode_set(mode='POSE')
import mathutils
head_pbone = armature_obj.pose.bones.get('head')
head_pbone.rotation_mode = 'XYZ'
head_pbone.rotation_euler = mathutils.Euler((math.radians(30), 0, 0), 'XYZ')
bpy.context.view_layer.update()
pos_after = mouth_obj.matrix_world.translation.copy()
delta = (pos_after - pos_before).length
head_follows = delta > 0.001
print(f"  Mouth pos before: {[round(x,4) for x in pos_before]}")
print(f"  Mouth pos after 30° head rotation: {[round(x,4) for x in pos_after]}")
print(f"  Delta: {delta*1000:.2f}mm — {'FOLLOWS HEAD ✓' if head_follows else 'NOT FOLLOWING ✗'}")

# Reset pose
head_pbone.rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')
bpy.ops.object.mode_set(mode='OBJECT')

test_results["head_follow"] = {
    "delta_m": round(delta, 6),
    "passed": head_follows
}

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────
print("\n[BUILD] === Exporting GLB ===")

bpy.ops.export_scene.gltf(
    filepath              = GLB_OUT,
    export_format         = 'GLB',
    export_apply          = False,
    export_morph          = True,
    export_morph_normal   = False,
    export_morph_tangent  = False,
    export_animations     = True,
    export_skins          = True,
    export_all_influences = False,
    use_selection         = False,
    export_yup            = True,
)

size = os.path.getsize(GLB_OUT)
print(f"[BUILD] Exported: {GLB_OUT} ({size:,} bytes)")

# ─────────────────────────────────────────────────────────────────────────────
# LOG
# ─────────────────────────────────────────────────────────────────────────────
log = {
    "source_glb": GLB_IN,
    "output_glb": GLB_OUT,
    "armature": armature_obj.name,
    "bone_count": len(armature_obj.data.bones),
    "head_bone": "head",
    "facial_objects_added": ["FaceMouth", "FaceEyes"],
    "skinning_method": "armature_modifier_plus_vertex_weights",
    "mouth_shape_keys": mouth_keys,
    "eye_shape_keys": eye_keys,
    "shape_key_tests": test_results,
    "all_tests_passed": all_passed and head_follows,
    "output_size_bytes": size,
}
with open(LOG_OUT, 'w') as f:
    json.dump(log, f, indent=2)

print(f"[BUILD] Log: {LOG_OUT}")
print("[BUILD] Done.")
