#!/usr/bin/env blender --python
"""
Blender script to rig the bunny character with a posable skeleton.

Usage:
    blender --background --python blender_rig_bunny.py

Or run inside Blender's Scripting workspace for interactive weight painting.
"""

import bpy
import bmesh
import os
from mathutils import Vector

# Configuration
INPUT_GLB = "/Users/tanishqyadav/agent/bunny_character_fixed_tail.glb"
OUTPUT_GLB = "/Users/tanishqyadav/agent/bunny_rigged.glb"

# Armature configuration
ARMATURE_NAME = "BunnyArmature"


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    print("[Clear] Scene cleared")


def import_glb(filepath):
    """Import GLB file"""
    print(f"[Import] Loading {filepath}")
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    imported_objects = [obj for obj in bpy.context.selected_objects]
    print(f"[Import] Imported {len(imported_objects)} objects")
    
    return imported_objects


def find_mesh_object():
    """Find the main mesh object"""
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and len(obj.data.vertices) > 100:
            print(f"[Mesh] Found main mesh: {obj.name} ({len(obj.data.vertices)} vertices)")
            return obj
    return None


def analyze_mesh_proportions(obj):
    """Analyze mesh to determine bone placement"""
    mesh = obj.data
    vertices = mesh.vertices
    
    # Calculate bounds
    min_x = min(v.co.x for v in vertices)
    max_x = max(v.co.x for v in vertices)
    min_y = min(v.co.y for v in vertices)
    max_y = max(v.co.y for v in vertices)
    min_z = min(v.co.z for v in vertices)
    max_z = max(v.co.z for v in vertices)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    
    print(f"[Analysis] Mesh proportions:")
    print(f"  Width (X): {width:.3f}")
    print(f"  Depth (Y): {depth:.3f}")
    print(f"  Height (Z): {height:.3f}")
    print(f"  Center: ({center_x:.3f}, {center_y:.3f}, {center_z:.3f})")
    
    return {
        'bounds': {
            'min': Vector((min_x, min_y, min_z)),
            'max': Vector((max_x, max_y, max_z)),
            'center': Vector((center_x, center_y, center_z))
        },
        'dimensions': {
            'width': width,
            'depth': depth,
            'height': height
        }
    }


def create_bunny_armature(mesh_obj, proportions):
    """Create armature for bunny character"""
    print("[Armature] Creating bunny armature...")
    
    bounds = proportions['bounds']
    dims = proportions['dimensions']
    
    # Calculate key positions
    # Root at bottom center
    root_pos = Vector((bounds['center'].x, bounds['center'].y, bounds['min'].z))
    
    # Spine: from root to mid-body
    spine_bottom = root_pos
    spine_mid = Vector((bounds['center'].x, bounds['center'].y, bounds['min'].z + dims['height'] * 0.3))
    spine_top = Vector((bounds['center'].x, bounds['center'].y, bounds['min'].z + dims['height'] * 0.5))
    
    # Chest: upper body
    chest_pos = Vector((bounds['center'].x, bounds['center'].y, bounds['min'].z + dims['height'] * 0.7))
    
    # Head: at top
    head_base = Vector((bounds['center'].x, bounds['center'].y + dims['depth'] * 0.1, bounds['min'].z + dims['height'] * 0.75))
    head_tip = Vector((bounds['center'].x, bounds['center'].y + dims['depth'] * 0.15, bounds['max'].z))
    
    # Ears: on top of head
    ear_base_z = bounds['max'].z * 0.9
    ear_tip_z = bounds['max'].z * 1.1
    ear_left_pos = Vector((bounds['min'].x * 0.3, bounds['center'].y, ear_base_z))
    ear_right_pos = Vector((bounds['max'].x * 0.3, bounds['center'].y, ear_base_z))
    ear_left_tip = Vector((bounds['min'].x * 0.4, bounds['center'].y, ear_tip_z))
    ear_right_tip = Vector((bounds['max'].x * 0.4, bounds['center'].y, ear_tip_z))
    
    # Tail: behind body
    tail_base = Vector((bounds['center'].x, bounds['min'].y, bounds['min'].z + dims['height'] * 0.2))
    tail_tip = Vector((bounds['center'].x, bounds['min'].y, bounds['min'].z + dims['height'] * 0.25))
    
    # Arms: from shoulders
    shoulder_height = bounds['min'].z + dims['height'] * 0.6
    shoulder_left = Vector((bounds['min'].x * 0.5, bounds['center'].y, shoulder_height))
    shoulder_right = Vector((bounds['max'].x * 0.5, bounds['center'].y, shoulder_height))
    
    elbow_left = Vector((bounds['min'].x * 0.7, bounds['center'].y, shoulder_height - dims['height'] * 0.2))
    elbow_right = Vector((bounds['max'].x * 0.7, bounds['center'].y, shoulder_height - dims['height'] * 0.2))
    
    hand_left = Vector((bounds['min'].x * 0.8, bounds['center'].y, shoulder_height - dims['height'] * 0.4))
    hand_right = Vector((bounds['max'].x * 0.8, bounds['center'].y, shoulder_height - dims['height'] * 0.4))
    
    # Legs: from hips
    hip_height = bounds['min'].z + dims['height'] * 0.25
    hip_left = Vector((bounds['min'].x * 0.3, bounds['center'].y, hip_height))
    hip_right = Vector((bounds['max'].x * 0.3, bounds['center'].y, hip_height))
    
    knee_left = Vector((bounds['min'].x * 0.35, bounds['center'].y + dims['depth'] * 0.1, hip_height - dims['height'] * 0.15))
    knee_right = Vector((bounds['max'].x * 0.35, bounds['center'].y + dims['depth'] * 0.1, hip_height - dims['height'] * 0.15))
    
    foot_left = Vector((bounds['min'].x * 0.4, bounds['center'].y + dims['depth'] * 0.2, bounds['min'].z))
    foot_right = Vector((bounds['max'].x * 0.4, bounds['center'].y + dims['depth'] * 0.2, bounds['min'].z))
    
    # Create armature
    bpy.ops.object.armature_add(location=root_pos)
    armature_obj = bpy.context.active_object
    armature_obj.name = ARMATURE_NAME
    armature = armature_obj.data
    armature.name = ARMATURE_NAME
    
    # Enter edit mode to add bones
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.edit_bones
    
    # Remove default bone
    edit_bones.remove(edit_bones[0])
    
    # Create bones
    def add_bone(name, head, tail, parent=None):
        bone = edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        if parent:
            bone.parent = parent
        return bone
    
    # Root and spine
    root_bone = add_bone('root', root_pos, spine_bottom + Vector((0, 0, 0.01)))
    spine1 = add_bone('spine.001', spine_bottom, spine_mid, root_bone)
    spine2 = add_bone('spine.002', spine_mid, spine_top, spine1)
    chest = add_bone('chest', spine_top, chest_pos, spine2)
    
    # Head
    head = add_bone('head', head_base, head_tip, chest)
    
    # Ears
    ear_L = add_bone('ear.L', ear_left_pos, ear_left_tip, head)
    ear_R = add_bone('ear.R', ear_right_pos, ear_right_tip, head)
    
    # Tail
    tail = add_bone('tail', tail_base, tail_tip, root_bone)
    
    # Left arm
    shoulder_L = add_bone('shoulder.L', shoulder_left, elbow_left, chest)
    forearm_L = add_bone('forearm.L', elbow_left, hand_left, shoulder_L)
    
    # Right arm
    shoulder_R = add_bone('shoulder.R', shoulder_right, elbow_right, chest)
    forearm_R = add_bone('forearm.R', elbow_right, hand_right, shoulder_R)
    
    # Left leg
    thigh_L = add_bone('thigh.L', hip_left, knee_left, root_bone)
    shin_L = add_bone('shin.L', knee_left, foot_left, thigh_L)
    
    # Right leg
    thigh_R = add_bone('thigh.R', hip_right, knee_right, root_bone)
    shin_R = add_bone('shin.R', knee_right, foot_right, thigh_R)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print(f"[Armature] Created {len(armature.bones)} bones")
    return armature_obj


def parent_mesh_to_armature(mesh_obj, armature_obj):
    """Parent mesh to armature with automatic weights"""
    print("[Parenting] Binding mesh to armature...")
    
    # Select mesh and armature
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    
    # Parent with automatic weights
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    
    print("[Parenting] Automatic weights applied")
    
    # Check if skinning was created
    if len(mesh_obj.vertex_groups) > 0:
        print(f"[Parenting] Created {len(mesh_obj.vertex_groups)} vertex groups")
        return True
    else:
        print("[Parenting] Warning: No vertex groups created!")
        return False


def test_pose(armature_obj):
    """Apply a test pose to verify rigging"""
    print("[Test] Applying test pose...")
    
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = armature_obj.pose.bones
    
    # Test rotations
    if 'head' in pose_bones:
        pose_bones['head'].rotation_euler[1] = 0.3  # Tilt head
    
    if 'ear.L' in pose_bones:
        pose_bones['ear.L'].rotation_euler[2] = 0.2  # Bend ear
    
    if 'shoulder.L' in pose_bones:
        pose_bones['shoulder.L'].rotation_euler[0] = 0.5  # Raise arm
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print("[Test] Test pose applied")


def export_glb(filepath):
    """Export as GLB with skinning"""
    print(f"[Export] Saving to {filepath}")
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        export_materials='EXPORT',
        export_attributes=True,
        export_skins=True,  # Include skinning/rigging
        export_morph=False,
        export_animations=False,
        export_normals=True,
        export_apply=False
    )
    
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"[Export] Exported {filepath} ({size / 1024 / 1024:.2f} MB)")
        return True
    else:
        print(f"[Export] Error: File not created!")
        return False


def main():
    """Main execution"""
    print("="*60)
    print("Bunny Rigging - Automated Script")
    print("="*60)
    
    # Step 1: Import
    clear_scene()
    import_glb(INPUT_GLB)
    
    # Step 2: Find mesh
    bunny = find_mesh_object()
    if not bunny:
        print("[Error] Could not find bunny mesh!")
        return
    
    # Step 3: Analyze proportions
    proportions = analyze_mesh_proportions(bunny)
    
    # Step 4: Create armature
    armature = create_bunny_armature(bunny, proportions)
    
    # Step 5: Parent mesh to armature
    success = parent_mesh_to_armature(bunny, armature)
    if not success:
        print("[Error] Failed to create skinning!")
        return
    
    # Step 6: Test pose (optional)
    # test_pose(armature)
    
    # Step 7: Export
    if export_glb(OUTPUT_GLB):
        print("="*60)
        print("✅ Rigging complete!")
        print(f"   Input:  {INPUT_GLB}")
        print(f"   Output: {OUTPUT_GLB}")
        print("="*60)
        print("\nNext steps:")
        print("1. Open in Blender to verify rigging")
        print("2. Enter Pose Mode (Ctrl+Tab) and test poses")
        print("3. If weights need adjustment, use Weight Paint mode")
        print("4. Export to game engine or animation tool")
    else:
        print("[Error] Export failed!")


if __name__ == "__main__":
    main()
