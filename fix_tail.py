import bpy
import bmesh
import math
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
glb_input = '/Users/tanishqyadav/agent/bunny_character_triposr.glb'
glb_output = '/Users/tanishqyadav/agent/bunny_character_tail_fixed.glb'

bpy.ops.import_scene.gltf(filepath=glb_input)

mesh_obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = mesh_obj

# Select mesh object and switch to Edit Mode
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh_obj.data)

# Delete old elongated tail faces (Y > 0.11 and X < -0.25)
faces_to_delete = []
for f in bm.faces:
    center = f.calc_center_median()
    if center.y > 0.11 and center.x < -0.25:
        faces_to_delete.append(f)

print(f"Deleting {len(faces_to_delete)} faces belonging to old tail...")
bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')

# Delete orphan vertices
orphan_verts = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=orphan_verts, context='VERTS')

# Fill holes
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)

bmesh.update_edit_mesh(mesh_obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

print("Old tail deleted successfully!")

# Add compact rounded pom-pom tail
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=16, 
    ring_count=12, 
    radius=0.048, 
    location=(-0.31, 0.09, 0.0)
)
tail_obj = bpy.context.active_object
tail_obj.name = "bunny_pom_pom_tail"
tail_obj.scale = (0.85, 0.9, 0.85)
bpy.ops.object.transform_apply(scale=True)

if mesh_obj.data.materials:
    tail_obj.data.materials.append(mesh_obj.data.materials[0])

bpy.ops.object.mode_set(mode='EDIT')
bm_tail = bmesh.from_edit_mesh(tail_obj.data)
uv_layer = bm_tail.loops.layers.uv.verify()

for face in bm_tail.faces:
    for loop in face.loops:
        orig_u, orig_v = loop[uv_layer].uv
        loop[uv_layer].uv = (0.5 + (orig_u - 0.5) * 0.15, 0.5 + (orig_v - 0.5) * 0.15)

bmesh.update_edit_mesh(tail_obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='DESELECT')
mesh_obj.select_set(True)
tail_obj.select_set(True)
bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.join()

print("Joined pom-pom tail into main mesh!")

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=glb_output,
    export_format='GLB'
)

print(f"Corrected GLB saved to: {glb_output}")
