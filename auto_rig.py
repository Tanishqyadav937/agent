import bpy
import math

# 1. Clean default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# File paths
input_glb = "./bunny_output/0/mesh.glb"
output_glb = "./bunny_output/bunny_rigged.glb"

# 2. Import GLB mesh
bpy.ops.import_scene.gltf(filepath=input_glb)

mesh_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
if not mesh_objs:
    mesh_objs = [obj for obj in bpy.data.objects if obj.type == 'MESH']

bunny = mesh_objs[0]

bpy.ops.object.select_all(action='DESELECT')
bunny.select_set(True)
bpy.context.view_layer.objects.active = bunny

# Rotate -90 degrees on X axis to stand upright
bunny.rotation_euler = (math.radians(-90), 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 3. Decimate mesh for WebGL performance
decimate_mod = bunny.modifiers.new(name="Decimate", type='DECIMATE')
decimate_mod.ratio = 0.25
bpy.ops.object.modifier_apply(modifier=decimate_mod.name)

# 4. Generate Armature Bones
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
armature = bpy.context.object
armature.name = "Bunny_Rig"
bones = armature.data.edit_bones

root = bones['Bone']
root.name = 'Spine'
root.head = (0, 0, 0.2)
root.tail = (0, 0, 0.6)

head = bones.new('Head')
head.head = (0, 0, 0.6)
head.tail = (0, 0, 1.1)
head.parent = root

ear_L = bones.new('Ear.L')
ear_L.head = (0.1, 0, 1.0)
ear_L.tail = (0.2, 0, 1.4)
ear_L.parent = head

ear_R = bones.new('Ear.R')
ear_R.head = (-0.1, 0, 1.0)
ear_R.tail = (-0.2, 0, 1.4)
ear_R.parent = head

arm_L = bones.new('Arm.L')
arm_L.head = (0.15, 0, 0.55)
arm_L.tail = (0.45, 0, 0.4)
arm_L.parent = root

arm_R = bones.new('Arm.R')
arm_R.head = (-0.15, 0, 0.55)
arm_R.tail = (-0.45, 0, 0.4)
arm_R.parent = root

bpy.ops.object.mode_set(mode='OBJECT')

# 5. Parent mesh to armature with automatic weights
bunny.select_set(True)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# 6. Add Lip-Sync Shape Keys (Viseme morph target)
bpy.context.view_layer.objects.active = bunny
bunny.shape_key_add(name="Basis", from_mix=False)

key_aa = bunny.shape_key_add(name="viseme_AA", from_mix=False)
for v in bunny.data.vertices:
    if v.co.z < 0.65 and v.co.z > 0.45 and abs(v.co.x) < 0.15 and v.co.y < 0.1:
        key_aa.data[v.index].co.z -= 0.05

# 7. Export ready-to-use GLB
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=output_glb,
    export_format='GLB',
    export_morph=True,
    export_skins=True
)

print(f"Rigging successfully completed: {output_glb}")
