#!/usr/bin/env blender --python
"""
Automated rig deformation test for bunny_rigged.glb

Tests bone rotations and checks for deformation problems.
"""

import bpy
import bmesh
import json
import os
import math
from mathutils import Vector, Euler

# Configuration
INPUT_GLB = "/Users/tanishqyadav/agent/bunny_rigged.glb"
REPORT_FILE = "/Users/tanishqyadav/agent/rig_deformation_test.json"
RENDER_DIR = "/Users/tanishqyadav/agent/rig_test_renders"

# Test configuration
TEST_BONES = [
    'head',
    'upper_arm.L',
    'upper_arm.R',
    'thigh.L',
    'thigh.R',
    'tail'
]

TEST_ROTATION_DEGREES = 15  # Rotation amount in degrees


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    print("[Clear] Scene cleared")


def import_glb(filepath):
    """Import GLB file"""
    print(f"[Import] Loading {filepath}")
    if not os.path.exists(filepath):
        print(f"[Error] File not found: {filepath}")
        return False
    
    try:
        bpy.ops.import_scene.gltf(filepath=filepath)
        print(f"[Import] Successfully imported")
        return True
    except Exception as e:
        print(f"[Error] Import failed: {e}")
        return False


def find_armature():
    """Find the BunnyArmature object"""
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and 'Bunny' in obj.name:
            return obj
    
    # Fallback: find any armature
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            return obj
    
    return None


def find_mesh():
    """Find the main mesh object"""
    meshes = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and len(obj.data.vertices) > 100:
            meshes.append(obj)
    
    # Return largest mesh
    if meshes:
        return max(meshes, key=lambda m: len(m.data.vertices))
    return None


def verify_rig_setup(armature_obj, mesh_obj):
    """Verify the rig is properly set up"""
    print("\n[Verify] Checking rig setup...")
    
    issues = []
    
    # Check armature type
    if armature_obj.type != 'ARMATURE':
        issues.append(f"Armature object type is {armature_obj.type}, not ARMATURE")
        return False, issues
    
    print(f"  ✅ Armature type: {armature_obj.type}")
    
    # Check bone count
    bone_count = len(armature_obj.data.bones)
    if bone_count < 18:
        issues.append(f"Expected 18 bones, found {bone_count}")
    
    print(f"  ✅ Bones: {bone_count}")
    
    # List bones
    bone_names = [bone.name for bone in armature_obj.data.bones]
    print(f"  Bones: {bone_names}")
    
    # Check vertex groups
    vg_count = len(mesh_obj.vertex_groups)
    if vg_count == 0:
        issues.append("Mesh has no vertex groups")
        return False, issues
    
    print(f"  ✅ Vertex groups: {vg_count}")
    
    # Check armature modifier
    armature_mod = None
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            armature_mod = mod
            break
    
    if not armature_mod:
        issues.append("Mesh has no ARMATURE modifier")
        return False, issues
    
    if armature_mod.object != armature_obj:
        issues.append("ARMATURE modifier points to wrong object")
        return False, issues
    
    print(f"  ✅ Armature modifier: {armature_mod.name}")
    print(f"  ✅ Modifier target: {armature_mod.object.name}")
    
    if issues:
        return False, issues
    
    return True, []


def get_mesh_bounds(mesh_obj):
    """Get mesh bounding box"""
    coords = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
    
    min_x = min(v.x for v in coords)
    max_x = max(v.x for v in coords)
    min_y = min(v.y for v in coords)
    max_y = max(v.y for v in coords)
    min_z = min(v.z for v in coords)
    max_z = max(v.z for v in coords)
    
    return {
        'min': (min_x, min_y, min_z),
        'max': (max_x, max_y, max_z),
        'center': ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2),
        'size': (max_x - min_x, max_y - min_y, max_z - min_z)
    }


def check_mesh_deformation(mesh_obj, baseline_bounds):
    """Check if mesh deformation is reasonable"""
    current_bounds = get_mesh_bounds(mesh_obj)
    
    issues = []
    
    # Check for extreme scaling
    for axis, baseline_size in zip(['X', 'Y', 'Z'], baseline_bounds['size']):
        current_size = current_bounds['size'][['X', 'Y', 'Z'].index(axis)]
        
        if baseline_size > 0:
            ratio = current_size / baseline_size
            
            # If mesh dimension changed by more than 50%, something is wrong
            if ratio > 1.5 or ratio < 0.5:
                issues.append(f"Extreme deformation on {axis} axis: {ratio:.2f}x baseline")
    
    # Check for detached vertices (vertices that moved too far)
    max_displacement = 0
    for v in mesh_obj.data.vertices:
        pos = mesh_obj.matrix_world @ v.co
        center = Vector(baseline_bounds['center'])
        distance = (pos - center).length
        
        # If any vertex is more than 2x the mesh size away, it's probably detached
        max_mesh_size = max(baseline_bounds['size'])
        if distance > max_mesh_size * 2:
            max_displacement = max(max_displacement, distance)
    
    if max_displacement > 0:
        issues.append(f"Possible detached vertices: max displacement {max_displacement:.3f}")
    
    return len(issues) == 0, issues


def test_bone_rotation(armature_obj, mesh_obj, bone_name, rotation_degrees, baseline_bounds):
    """Test a bone rotation and check deformation"""
    print(f"\n[Test] Testing bone: {bone_name}")
    
    result = {
        'bone': bone_name,
        'rotation_degrees': rotation_degrees,
        'rotation_applied': False,
        'mesh_remained_attached': False,
        'deformation_issues': [],
        'passed': False
    }
    
    # Check if bone exists
    if bone_name not in armature_obj.pose.bones:
        print(f"  ❌ Bone '{bone_name}' not found")
        result['deformation_issues'].append(f"Bone '{bone_name}' not found")
        return result
    
    # Enter pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    
    # Get pose bone
    pose_bone = armature_obj.pose.bones[bone_name]
    
    # Store original rotation
    original_rotation = pose_bone.rotation_euler.copy()
    
    # Apply test rotation (rotate around Z axis)
    rotation_radians = math.radians(rotation_degrees)
    pose_bone.rotation_euler.z = rotation_radians
    result['rotation_applied'] = True
    
    print(f"  Applied rotation: {rotation_degrees}° around Z axis")
    
    # Update scene
    bpy.context.view_layer.update()
    
    # Force dependency graph evaluation
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh_eval = mesh_obj.evaluated_get(depsgraph)
    
    # Check deformation
    passed, issues = check_mesh_deformation(mesh_eval, baseline_bounds)
    
    result['mesh_remained_attached'] = passed
    result['deformation_issues'] = issues
    result['passed'] = passed
    
    if passed:
        print(f"  ✅ Deformation test passed")
    else:
        print(f"  ❌ Deformation issues detected:")
        for issue in issues:
            print(f"     - {issue}")
    
    # Restore original rotation
    pose_bone.rotation_euler = original_rotation
    bpy.context.view_layer.update()
    
    # Return to object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return result


def setup_render_scene(armature_obj, mesh_obj):
    """Setup scene for rendering test poses"""
    # Add camera
    bpy.ops.object.camera_add(location=(2, -2, 1.5))
    camera = bpy.context.active_object
    camera.data.lens = 50
    
    # Point camera at mesh center
    mesh_center = Vector(get_mesh_bounds(mesh_obj)['center'])
    direction = mesh_center - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    bpy.context.scene.camera = camera
    
    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    light = bpy.context.active_object
    light.data.energy = 2
    
    # Setup render settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 800
    bpy.context.scene.render.film_transparent = False
    
    print("[Render] Scene setup complete")


def render_pose(armature_obj, bone_name, pose_index):
    """Render current pose"""
    if not os.path.exists(RENDER_DIR):
        os.makedirs(RENDER_DIR)
    
    output_path = os.path.join(RENDER_DIR, f"test_pose_{bone_name}_{pose_index:02d}.png")
    bpy.context.scene.render.filepath = output_path
    
    try:
        bpy.ops.render.render(write_still=True)
        print(f"  📷 Rendered: {output_path}")
        return output_path
    except Exception as e:
        print(f"  ⚠️  Render failed: {e}")
        return None


def main():
    """Main execution"""
    print("="*60)
    print("Automated Rig Deformation Test")
    print("="*60)
    
    report = {
        'input_file': INPUT_GLB,
        'test_date': None,
        'rig_verification': {},
        'bone_tests': [],
        'overall_result': 'UNKNOWN',
        'summary': {}
    }
    
    # Import datetime for timestamp
    from datetime import datetime
    report['test_date'] = datetime.now().isoformat()
    
    # Step 1: Import
    print("\n[Step 1] Import GLB")
    clear_scene()
    if not import_glb(INPUT_GLB):
        report['overall_result'] = 'FAIL'
        report['rig_verification']['error'] = 'Failed to import GLB'
        save_report(report)
        return False
    
    # Step 2: Find armature and mesh
    print("\n[Step 2] Find armature and mesh")
    armature_obj = find_armature()
    mesh_obj = find_mesh()
    
    if not armature_obj:
        print("❌ No armature found!")
        report['overall_result'] = 'FAIL'
        report['rig_verification']['error'] = 'No armature found'
        save_report(report)
        return False
    
    if not mesh_obj:
        print("❌ No mesh found!")
        report['overall_result'] = 'FAIL'
        report['rig_verification']['error'] = 'No mesh found'
        save_report(report)
        return False
    
    print(f"  ✅ Armature: {armature_obj.name}")
    print(f"  ✅ Mesh: {mesh_obj.name}")
    
    # Step 3: Verify rig setup
    print("\n[Step 3] Verify rig setup")
    verified, issues = verify_rig_setup(armature_obj, mesh_obj)
    
    report['rig_verification'] = {
        'armature_name': armature_obj.name,
        'mesh_name': mesh_obj.name,
        'bone_count': len(armature_obj.data.bones),
        'vertex_group_count': len(mesh_obj.vertex_groups),
        'verified': verified,
        'issues': issues
    }
    
    if not verified:
        print("❌ Rig verification failed!")
        for issue in issues:
            print(f"   - {issue}")
        report['overall_result'] = 'FAIL'
        save_report(report)
        return False
    
    print("✅ Rig verification passed")
    
    # Step 4: Get baseline mesh bounds
    print("\n[Step 4] Get baseline mesh bounds")
    baseline_bounds = get_mesh_bounds(mesh_obj)
    print(f"  Baseline bounds: {baseline_bounds}")
    
    # Step 5: Setup rendering (optional)
    print("\n[Step 5] Setup render scene")
    try:
        setup_render_scene(armature_obj, mesh_obj)
        rendering_enabled = True
    except Exception as e:
        print(f"  ⚠️  Render setup failed: {e}")
        rendering_enabled = False
    
    # Step 6: Test each bone
    print("\n[Step 6] Test bone rotations")
    
    all_tests_passed = True
    tested_bones = []
    failed_bones = []
    
    for bone_name in TEST_BONES:
        result = test_bone_rotation(
            armature_obj,
            mesh_obj,
            bone_name,
            TEST_ROTATION_DEGREES,
            baseline_bounds
        )
        
        report['bone_tests'].append(result)
        
        if result['rotation_applied']:
            tested_bones.append(bone_name)
            
            if not result['passed']:
                all_tests_passed = False
                failed_bones.append(bone_name)
            
            # Optionally render the pose
            if rendering_enabled and result['rotation_applied']:
                # Re-apply rotation for render
                bpy.context.view_layer.objects.active = armature_obj
                bpy.ops.object.mode_set(mode='POSE')
                pose_bone = armature_obj.pose.bones[bone_name]
                pose_bone.rotation_euler.z = math.radians(TEST_ROTATION_DEGREES)
                bpy.context.view_layer.update()
                
                # Render
                render_path = render_pose(armature_obj, bone_name, len(report['bone_tests']))
                if render_path:
                    result['render_path'] = render_path
                
                # Reset
                pose_bone.rotation_euler.z = 0
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.context.view_layer.update()
    
    # Step 7: Reset to rest pose
    print("\n[Step 7] Reset to rest pose")
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()
    bpy.ops.object.mode_set(mode='OBJECT')
    print("  ✅ Armature reset to rest pose")
    
    # Step 8: Generate summary
    print("\n[Step 8] Generate summary")
    
    report['summary'] = {
        'total_bones_tested': len(tested_bones),
        'bones_passed': len(tested_bones) - len(failed_bones),
        'bones_failed': len(failed_bones),
        'failed_bone_names': failed_bones,
        'all_tests_passed': all_tests_passed
    }
    
    if all_tests_passed:
        report['overall_result'] = 'PASS'
    else:
        report['overall_result'] = 'FAIL'
    
    # Save report
    save_report(report)
    
    # Print final result
    print("\n" + "="*60)
    if all_tests_passed:
        print("RIG DEFORMATION TEST: PASS")
        print("="*60)
        print(f"✅ All {len(tested_bones)} bone tests passed")
        print(f"   Tested bones: {', '.join(tested_bones)}")
    else:
        print("RIG DEFORMATION TEST: FAIL")
        print("="*60)
        print(f"❌ {len(failed_bones)} out of {len(tested_bones)} bones failed")
        print(f"   Failed bones: {', '.join(failed_bones)}")
        print("\nIssues detected:")
        for test in report['bone_tests']:
            if not test['passed'] and test['deformation_issues']:
                print(f"\n  {test['bone']}:")
                for issue in test['deformation_issues']:
                    print(f"    - {issue}")
    
    if rendering_enabled:
        print(f"\n📷 Test renders saved to: {RENDER_DIR}")
    
    print(f"\n📄 Report saved to: {REPORT_FILE}")
    print("="*60)
    
    return all_tests_passed


def save_report(report):
    """Save report to JSON file"""
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[Report] Saved to {REPORT_FILE}")
    except Exception as e:
        print(f"[Report] Failed to save: {e}")


if __name__ == "__main__":
    success = main()
    if not success:
        import sys
        sys.exit(1)
