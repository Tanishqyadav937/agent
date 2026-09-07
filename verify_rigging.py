#!/usr/bin/env blender --python
"""
Verify that GLB file has proper skinning/rigging data.

Usage:
    blender --background --python verify_rigging.py
"""

import bpy
import json

FILES_TO_CHECK = [
    "/Users/tanishqyadav/agent/bunny_character_triposr.glb",
    "/Users/tanishqyadav/agent/bunny_character_fixed_tail.glb",
    "/Users/tanishqyadav/agent/bunny_rigged.glb"
]

def check_file(filepath):
    """Check GLB file for rigging data"""
    print(f"\n{'='*60}")
    print(f"Checking: {filepath}")
    print('='*60)
    
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    try:
        # Import
        bpy.ops.import_scene.gltf(filepath=filepath)
        
        # Check for armatures
        armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
        print(f"Armatures found: {len(armatures)}")
        
        for arm in armatures:
            print(f"  - {arm.name}: {len(arm.data.bones)} bones")
            for bone in arm.data.bones:
                print(f"    • {bone.name}")
        
        # Check for skinned meshes
        meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        print(f"\nMeshes found: {len(meshes)}")
        
        for mesh in meshes:
            print(f"  - {mesh.name}:")
            print(f"    Vertices: {len(mesh.data.vertices)}")
            print(f"    Vertex Groups: {len(mesh.vertex_groups)}")
            
            if mesh.vertex_groups:
                print(f"    Groups:")
                for vg in mesh.vertex_groups:
                    print(f"      • {vg.name}")
            
            # Check for armature modifier
            has_armature_mod = any(mod.type == 'ARMATURE' for mod in mesh.modifiers)
            print(f"    Armature Modifier: {'Yes' if has_armature_mod else 'No'}")
            
            # Check parent
            if mesh.parent:
                print(f"    Parent: {mesh.parent.name} ({mesh.parent.type})")
        
        # Check if skinning exists
        has_rigging = len(armatures) > 0 and any(len(m.vertex_groups) > 0 for m in meshes)
        
        print(f"\n{'✅' if has_rigging else '❌'} Rigging Status: {'RIGGED' if has_rigging else 'NOT RIGGED'}")
        
        return has_rigging
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("GLB Rigging Verification")
    print("="*60)
    
    results = {}
    for filepath in FILES_TO_CHECK:
        try:
            results[filepath] = check_file(filepath)
        except Exception as e:
            print(f"Failed to check {filepath}: {e}")
            results[filepath] = False
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    for filepath, rigged in results.items():
        filename = filepath.split('/')[-1]
        status = "✅ RIGGED" if rigged else "❌ NOT RIGGED"
        print(f"{status}: {filename}")


if __name__ == "__main__":
    main()
