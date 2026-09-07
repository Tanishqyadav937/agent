#!/usr/bin/env blender --python
"""
Open the saved .blend file and check if rigging is present
"""

import bpy

BLEND_FILE = "/Users/tanishqyadav/agent/bunny_rigging.blend"

print("="*60)
print(f"Checking: {BLEND_FILE}")
print("="*60)

# Open the blend file
bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

print("\nObjects in scene:")
for obj in bpy.data.objects:
    print(f"  - {obj.name} (type: {obj.type})")
    
    if obj.type == 'ARMATURE':
        print(f"    Bones: {len(obj.data.bones)}")
        for bone in obj.data.bones:
            print(f"      • {bone.name}")
    
    if obj.type == 'MESH':
        print(f"    Vertices: {len(obj.data.vertices)}")
        print(f"    Vertex Groups: {len(obj.vertex_groups)}")
        if obj.vertex_groups:
            print(f"    Groups: {[vg.name for vg in obj.vertex_groups]}")
        
        print(f"    Modifiers:")
        for mod in obj.modifiers:
            print(f"      • {mod.name} (type: {mod.type})")
            if mod.type == 'ARMATURE':
                print(f"        Target: {mod.object.name if mod.object else 'None'}")
                print(f"        Use vertex groups: {mod.use_vertex_groups}")
        
        print(f"    Parent: {obj.parent.name if obj.parent else 'None'}")
        if obj.parent:
            print(f"    Parent type: {obj.parent.type}")

print("\n" + "="*60)
print("Rigging present in .blend file!" if any(obj.type == 'ARMATURE' for obj in bpy.data.objects) else "No armature found!")
print("="*60)
