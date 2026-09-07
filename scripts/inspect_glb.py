import bpy, json
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for m in bpy.data.meshes: bpy.data.meshes.remove(m)
bpy.ops.import_scene.gltf(filepath="/Users/tanishqyadav/agent/bunny_character_lipsync.glb")
print("=== OBJECTS IN EXPORTED GLB ===")
for obj in bpy.data.objects:
    sk_names = []
    if obj.type == 'MESH' and obj.data.shape_keys:
        sk_names = [sk.name for sk in obj.data.shape_keys.key_blocks]
    print(f"  {obj.type:10s} | {obj.name:40s} | parent_type={obj.parent_type:6s} | parent_bone={obj.parent_bone:10s} | sk={sk_names}")
