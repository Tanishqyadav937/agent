#!/usr/bin/env blender --python
"""
Automated facial animation and lip-sync setup for bunny_rigged.glb

Creates shape keys for facial expressions and visemes.
"""

import bpy
import bmesh
import json
import os
import math
from mathutils import Vector

# Configuration
INPUT_GLB = "/Users/tanishqyadav/agent/bunny_rigged.glb"
OUTPUT_GLB = "/Users/tanishqyadav/agent/bunny_rigged_facial.glb"
REPORT_FILE = "/Users/tanishqyadav/agent/facial_animation_test.json"
RENDER_DIR = "/Users/tanishqyadav/agent/facial_test_renders"

# Shape keys to create
SHAPE_KEYS = {
    'facial_expressions': [
        'jawOpen',
        'mouthClose',
        'mouthSmile',
        'mouthFrown',
        'mouthPucker',
        'mouthFunnel'
    ],
    'visemes': [
        'viseme_A',
        'viseme_E',
        'viseme_I',
        'viseme_O',
        'viseme_U'
    ],
    'eye_controls': [
        'blink.L',
        'blink.R'
    ]
}


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


def find_mesh():
    """Find the main mesh object"""
    meshes = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and len(obj.data.vertices) > 100:
            meshes.append(obj)
    
    if meshes:
        return max(meshes, key=lambda m: len(m.data.vertices))
    return None


def find_armature():
    """Find the armature object"""
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def analyze_face_topology(mesh_obj):
    """Analyze mesh topology to determine if it's suitable for facial animation"""
    print("\n[Analysis] Analyzing face topology...")
    
    mesh = mesh_obj.data
    vertices = mesh.vertices
    
    # Get mesh bounds
    coords = [mesh_obj.matrix_world @ v.co for v in vertices]
    
    min_x = min(v.x for v in coords)
    max_x = max(v.x for v in coords)
    min_y = min(v.y for v in coords)
    max_y = max(v.y for v in coords)
    min_z = min(v.z for v in coords)
    max_z = max(v.z for v in coords)
    
    center = Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2))
    
    # Identify face region (front upper area)
    # For a bunny: face is front (positive Y) and upper (high Z)
    face_threshold_y = min_y + (max_y - min_y) * 0.6  # Front 40%
    face_threshold_z = min_z + (max_z - min_z) * 0.5  # Upper 50%
    
    face_verts = [
        v for v in vertices 
        if (mesh_obj.matrix_world @ v.co).y > face_threshold_y 
        and (mesh_obj.matrix_world @ v.co).z > face_threshold_z
    ]
    
    # Identify mouth region (center front, mid-height)
    mouth_threshold_z_min = min_z + (max_z - min_z) * 0.5
    mouth_threshold_z_max = min_z + (max_z - min_z) * 0.7
    mouth_threshold_y = max_y * 0.8
    mouth_radius = (max_x - min_x) * 0.15
    
    mouth_center = Vector((center.x, max_y * 0.9, (mouth_threshold_z_min + mouth_threshold_z_max) / 2))
    
    mouth_verts = [
        v for v in vertices
        if (mesh_obj.matrix_world @ v.co - mouth_center).length < mouth_radius
        and (mesh_obj.matrix_world @ v.co).y > mouth_threshold_y
    ]
    
    # Identify eye regions (left and right)
    eye_z = min_z + (max_z - min_z) * 0.75
    eye_y = min_y + (max_y - min_y) * 0.7
    eye_offset_x = (max_x - min_x) * 0.2
    
    left_eye_center = Vector((center.x - eye_offset_x, max_y * 0.85, eye_z))
    right_eye_center = Vector((center.x + eye_offset_x, max_y * 0.85, eye_z))
    eye_radius = (max_x - min_x) * 0.1
    
    left_eye_verts = [
        v for v in vertices
        if (mesh_obj.matrix_world @ v.co - left_eye_center).length < eye_radius
    ]
    
    right_eye_verts = [
        v for v in vertices
        if (mesh_obj.matrix_world @ v.co - right_eye_center).length < eye_radius
    ]
    
    # Identify jaw vertices (lower front part)
    jaw_threshold_z = min_z + (max_z - min_z) * 0.45
    jaw_verts = [
        v for v in vertices
        if (mesh_obj.matrix_world @ v.co).z < jaw_threshold_z
        and (mesh_obj.matrix_world @ v.co).y > face_threshold_y
    ]
    
    analysis = {
        'total_vertices': len(vertices),
        'face_vertices': len(face_verts),
        'mouth_vertices': len(mouth_verts),
        'left_eye_vertices': len(left_eye_verts),
        'right_eye_vertices': len(right_eye_verts),
        'jaw_vertices': len(jaw_verts),
        'bounds': {
            'min': (min_x, min_y, min_z),
            'max': (max_x, max_y, max_z),
            'center': (center.x, center.y, center.z)
        },
        'regions': {
            'mouth_center': (mouth_center.x, mouth_center.y, mouth_center.z),
            'left_eye_center': (left_eye_center.x, left_eye_center.y, left_eye_center.z),
            'right_eye_center': (right_eye_center.x, right_eye_center.y, right_eye_center.z)
        },
        'suitable_for_facial': True,
        'limitations': []
    }
    
    print(f"  Total vertices: {analysis['total_vertices']}")
    print(f"  Face region vertices: {analysis['face_vertices']}")
    print(f"  Mouth region vertices: {analysis['mouth_vertices']}")
    print(f"  Left eye vertices: {analysis['left_eye_vertices']}")
    print(f"  Right eye vertices: {analysis['right_eye_vertices']}")
    print(f"  Jaw vertices: {analysis['jaw_vertices']}")
    
    # Check if topology is suitable
    if analysis['mouth_vertices'] < 20:
        analysis['suitable_for_facial'] = False
        analysis['limitations'].append(f"Mouth region has too few vertices ({analysis['mouth_vertices']}), need at least 20")
    
    if analysis['left_eye_vertices'] < 10 or analysis['right_eye_vertices'] < 10:
        analysis['limitations'].append(f"Eye regions have few vertices (L:{analysis['left_eye_vertices']}, R:{analysis['right_eye_vertices']})")
    
    if analysis['face_vertices'] < 100:
        analysis['suitable_for_facial'] = False
        analysis['limitations'].append(f"Face region has too few vertices ({analysis['face_vertices']}), need at least 100")
    
    if analysis['suitable_for_facial']:
        print("  ✅ Topology is suitable for facial animation")
    else:
        print("  ❌ Topology has limitations:")
        for limitation in analysis['limitations']:
            print(f"     - {limitation}")
    
    return analysis


def create_shape_key(mesh_obj, name, vertex_indices, deformation_func, analysis):
    """Create a shape key with specified deformation"""
    print(f"\n[Shape Key] Creating: {name}")
    
    # Ensure basis shape key exists
    if not mesh_obj.data.shape_keys:
        basis = mesh_obj.shape_key_add(name='Basis')
        basis.interpolation = 'KEY_LINEAR'
        print("  Created Basis shape key")
    
    # Create new shape key
    shape_key = mesh_obj.shape_key_add(name=name)
    shape_key.interpolation = 'KEY_LINEAR'
    
    # Apply deformation
    deformed_count = 0
    for idx in vertex_indices:
        if idx < len(shape_key.data):
            try:
                new_pos = deformation_func(
                    mesh_obj.data.vertices[idx].co.copy(),
                    mesh_obj.matrix_world @ mesh_obj.data.vertices[idx].co,
                    analysis
                )
                shape_key.data[idx].co = new_pos
                deformed_count += 1
            except Exception as e:
                print(f"  Warning: Failed to deform vertex {idx}: {e}")
    
    print(f"  ✅ Created shape key '{name}' (deformed {deformed_count} vertices)")
    return shape_key, deformed_count


def get_mouth_vertices(mesh_obj, analysis):
    """Get vertex indices for mouth region"""
    mouth_center = Vector(analysis['regions']['mouth_center'])
    mouth_radius = (analysis['bounds']['max'][0] - analysis['bounds']['min'][0]) * 0.15
    
    indices = []
    for i, v in enumerate(mesh_obj.data.vertices):
        world_pos = mesh_obj.matrix_world @ v.co
        if (world_pos - mouth_center).length < mouth_radius:
            indices.append(i)
    
    return indices


def get_jaw_vertices(mesh_obj, analysis):
    """Get vertex indices for jaw region"""
    jaw_threshold_z = analysis['bounds']['min'][2] + (analysis['bounds']['max'][2] - analysis['bounds']['min'][2]) * 0.45
    face_threshold_y = analysis['bounds']['min'][1] + (analysis['bounds']['max'][1] - analysis['bounds']['min'][1]) * 0.6
    
    indices = []
    for i, v in enumerate(mesh_obj.data.vertices):
        world_pos = mesh_obj.matrix_world @ v.co
        if world_pos.z < jaw_threshold_z and world_pos.y > face_threshold_y:
            indices.append(i)
    
    return indices


def get_eye_vertices(mesh_obj, analysis, side='left'):
    """Get vertex indices for eye region"""
    if side == 'left':
        eye_center = Vector(analysis['regions']['left_eye_center'])
    else:
        eye_center = Vector(analysis['regions']['right_eye_center'])
    
    eye_radius = (analysis['bounds']['max'][0] - analysis['bounds']['min'][0]) * 0.1
    
    indices = []
    for i, v in enumerate(mesh_obj.data.vertices):
        world_pos = mesh_obj.matrix_world @ v.co
        if (world_pos - eye_center).length < eye_radius:
            indices.append(i)
    
    return indices


def create_facial_shape_keys(mesh_obj, analysis):
    """Create all facial shape keys"""
    print("\n[Shape Keys] Creating facial shape keys...")
    
    results = []
    
    # Get vertex regions
    mouth_verts = get_mouth_vertices(mesh_obj, analysis)
    jaw_verts = get_jaw_vertices(mesh_obj, analysis)
    left_eye_verts = get_eye_vertices(mesh_obj, analysis, 'left')
    right_eye_verts = get_eye_vertices(mesh_obj, analysis, 'right')
    
    print(f"  Mouth vertices: {len(mouth_verts)}")
    print(f"  Jaw vertices: {len(jaw_verts)}")
    print(f"  Left eye vertices: {len(left_eye_verts)}")
    print(f"  Right eye vertices: {len(right_eye_verts)}")
    
    # Jaw Open - move jaw down
    def jaw_open_deform(local_pos, world_pos, analysis):
        new_pos = local_pos.copy()
        # Move down
        new_pos.z -= 0.05
        return new_pos
    
    sk, count = create_shape_key(mesh_obj, 'jawOpen', jaw_verts, jaw_open_deform, analysis)
    results.append({'name': 'jawOpen', 'created': True, 'deformed_vertices': count})
    
    # Mouth Close - bring mouth vertices closer together
    def mouth_close_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        direction = mouth_center - world_pos
        new_world = world_pos + direction * 0.3
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'mouthClose', mouth_verts, mouth_close_deform, analysis)
    results.append({'name': 'mouthClose', 'created': True, 'deformed_vertices': count})
    
    # Mouth Smile - move mouth corners up and out
    def mouth_smile_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        offset = world_pos - mouth_center
        new_world = world_pos.copy()
        # Move corners up and slightly out
        if abs(offset.x) > 0.01:  # Side vertices
            new_world.z += 0.02
            new_world.x += offset.x * 0.2
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'mouthSmile', mouth_verts, mouth_smile_deform, analysis)
    results.append({'name': 'mouthSmile', 'created': True, 'deformed_vertices': count})
    
    # Mouth Frown - move mouth corners down
    def mouth_frown_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        offset = world_pos - mouth_center
        new_world = world_pos.copy()
        if abs(offset.x) > 0.01:  # Side vertices
            new_world.z -= 0.02
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'mouthFrown', mouth_verts, mouth_frown_deform, analysis)
    results.append({'name': 'mouthFrown', 'created': True, 'deformed_vertices': count})
    
    # Mouth Pucker - bring mouth vertices forward and together
    def mouth_pucker_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        direction = mouth_center - world_pos
        new_world = world_pos + direction * 0.4
        new_world.y += 0.02  # Move forward
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'mouthPucker', mouth_verts, mouth_pucker_deform, analysis)
    results.append({'name': 'mouthPucker', 'created': True, 'deformed_vertices': count})
    
    # Mouth Funnel - mouth open in O shape
    def mouth_funnel_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        new_world = world_pos.copy()
        new_world.y += 0.015  # Forward
        offset = world_pos - mouth_center
        if abs(offset.x) > 0.01 or abs(offset.z) > 0.01:
            # Create circular opening
            new_world.z -= 0.01
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'mouthFunnel', mouth_verts, mouth_funnel_deform, analysis)
    results.append({'name': 'mouthFunnel', 'created': True, 'deformed_vertices': count})
    
    # Visemes - simplified mouth shapes for lip sync
    # Viseme A (ah) - mouth open
    def viseme_a_deform(local_pos, world_pos, analysis):
        new_pos = local_pos.copy()
        new_pos.z -= 0.03
        return new_pos
    
    sk, count = create_shape_key(mesh_obj, 'viseme_A', jaw_verts + mouth_verts, viseme_a_deform, analysis)
    results.append({'name': 'viseme_A', 'created': True, 'deformed_vertices': count})
    
    # Viseme E (eh) - mouth slightly open, wider
    def viseme_e_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        offset = world_pos - mouth_center
        new_world = world_pos.copy()
        if abs(offset.x) > 0.01:
            new_world.x += offset.x * 0.15
        new_world.z -= 0.015
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'viseme_E', mouth_verts, viseme_e_deform, analysis)
    results.append({'name': 'viseme_E', 'created': True, 'deformed_vertices': count})
    
    # Viseme I (ee) - mouth wide, corners back
    def viseme_i_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        offset = world_pos - mouth_center
        new_world = world_pos.copy()
        if abs(offset.x) > 0.01:
            new_world.x += offset.x * 0.25
            new_world.z += 0.01
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'viseme_I', mouth_verts, viseme_i_deform, analysis)
    results.append({'name': 'viseme_I', 'created': True, 'deformed_vertices': count})
    
    # Viseme O (oh) - round mouth
    def viseme_o_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        direction = mouth_center - world_pos
        new_world = world_pos + direction * 0.2
        new_world.y += 0.02
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'viseme_O', mouth_verts, viseme_o_deform, analysis)
    results.append({'name': 'viseme_O', 'created': True, 'deformed_vertices': count})
    
    # Viseme U (oo) - pucker
    def viseme_u_deform(local_pos, world_pos, analysis):
        mouth_center = Vector(analysis['regions']['mouth_center'])
        direction = mouth_center - world_pos
        new_world = world_pos + direction * 0.5
        new_world.y += 0.025
        return mesh_obj.matrix_world.inverted() @ new_world
    
    sk, count = create_shape_key(mesh_obj, 'viseme_U', mouth_verts, viseme_u_deform, analysis)
    results.append({'name': 'viseme_U', 'created': True, 'deformed_vertices': count})
    
    # Blink Left
    def blink_left_deform(local_pos, world_pos, analysis):
        eye_center = Vector(analysis['regions']['left_eye_center'])
        direction = eye_center - world_pos
        new_world = world_pos + direction * 0.8
        return mesh_obj.matrix_world.inverted() @ new_world
    
    if len(left_eye_verts) > 0:
        sk, count = create_shape_key(mesh_obj, 'blink.L', left_eye_verts, blink_left_deform, analysis)
        results.append({'name': 'blink.L', 'created': True, 'deformed_vertices': count})
    else:
        results.append({'name': 'blink.L', 'created': False, 'deformed_vertices': 0, 'reason': 'No left eye vertices found'})
    
    # Blink Right
    def blink_right_deform(local_pos, world_pos, analysis):
        eye_center = Vector(analysis['regions']['right_eye_center'])
        direction = eye_center - world_pos
        new_world = world_pos + direction * 0.8
        return mesh_obj.matrix_world.inverted() @ new_world
    
    if len(right_eye_verts) > 0:
        sk, count = create_shape_key(mesh_obj, 'blink.R', right_eye_verts, blink_right_deform, analysis)
        results.append({'name': 'blink.R', 'created': True, 'deformed_vertices': count})
    else:
        results.append({'name': 'blink.R', 'created': False, 'deformed_vertices': 0, 'reason': 'No right eye vertices found'})
    
    return results


def test_shape_key(mesh_obj, shape_key_name):
    """Test if a shape key actually deforms the mesh"""
    print(f"\n[Test] Testing shape key: {shape_key_name}")
    
    if not mesh_obj.data.shape_keys:
        print("  ❌ No shape keys on mesh")
        return False, "No shape keys on mesh"
    
    shape_key = mesh_obj.data.shape_keys.key_blocks.get(shape_key_name)
    if not shape_key:
        print(f"  ❌ Shape key '{shape_key_name}' not found")
        return False, f"Shape key not found"
    
    # Get basis
    basis = mesh_obj.data.shape_keys.key_blocks['Basis']
    
    # Set shape key to 1.0
    shape_key.value = 1.0
    
    # Update mesh
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh_eval = mesh_obj.evaluated_get(depsgraph)
    
    # Compare vertices
    moved_vertices = 0
    total_displacement = 0.0
    
    for i in range(len(mesh_eval.data.vertices)):
        basis_pos = basis.data[i].co
        shape_pos = shape_key.data[i].co
        
        displacement = (shape_pos - basis_pos).length
        if displacement > 0.0001:  # Threshold for "moved"
            moved_vertices += 1
            total_displacement += displacement
    
    # Reset
    shape_key.value = 0.0
    
    avg_displacement = total_displacement / moved_vertices if moved_vertices > 0 else 0
    
    if moved_vertices > 0:
        print(f"  ✅ Shape key works: {moved_vertices} vertices moved, avg displacement: {avg_displacement:.4f}")
        return True, f"{moved_vertices} vertices moved"
    else:
        print(f"  ❌ Shape key has no effect")
        return False, "No vertices moved"


def render_shape_key(mesh_obj, shape_key_name, index):
    """Render shape key activation"""
    if not os.path.exists(RENDER_DIR):
        os.makedirs(RENDER_DIR)
    
    shape_key = mesh_obj.data.shape_keys.key_blocks.get(shape_key_name)
    if not shape_key:
        return None
    
    # Set shape key value
    shape_key.value = 1.0
    bpy.context.view_layer.update()
    
    # Render
    output_path = os.path.join(RENDER_DIR, f"facial_{shape_key_name}_{index:02d}.png")
    bpy.context.scene.render.filepath = output_path
    
    try:
        bpy.ops.render.render(write_still=True)
        print(f"  📷 Rendered: {output_path}")
        result = output_path
    except Exception as e:
        print(f"  ⚠️  Render failed: {e}")
        result = None
    
    # Reset
    shape_key.value = 0.0
    bpy.context.view_layer.update()
    
    return result


def verify_armature(armature_obj):
    """Verify armature is intact"""
    if not armature_obj:
        return False, "No armature found"
    
    if armature_obj.type != 'ARMATURE':
        return False, f"Object type is {armature_obj.type}, not ARMATURE"
    
    bone_count = len(armature_obj.data.bones)
    if bone_count != 18:
        return False, f"Expected 18 bones, found {bone_count}"
    
    return True, f"Armature intact with {bone_count} bones"


def export_glb(filepath, mesh_obj, armature_obj):
    """Export as GLB with skinning and morph targets"""
    print(f"\n[Export] Exporting to {filepath}")
    
    # Select objects
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    if armature_obj:
        armature_obj.select_set(True)
    
    # Export
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',
            use_selection=True,
            export_materials='EXPORT',
            export_attributes=True,
            export_skins=True,
            export_morph=True,  # CRITICAL: Export shape keys as morph targets
            export_morph_normal=True,
            export_all_influences=True,
            export_def_bones=True,
            export_hierarchy_flatten_bones=False,
            export_animations=False,
            export_normals=True,
            export_apply=False
        )
        
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"[Export] Exported {filepath} ({size / 1024 / 1024:.2f} MB)")
            return True
        else:
            print("[Export] ERROR: File not created")
            return False
            
    except Exception as e:
        print(f"[Export] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_exported_glb(filepath):
    """Verify exported GLB has everything"""
    print(f"\n[Verify Export] Importing {filepath}")
    
    # Clear and import
    clear_scene()
    
    try:
        bpy.ops.import_scene.gltf(filepath=filepath)
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False, {}
    
    # Check armature
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    
    # Check mesh
    meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH' and len(obj.data.vertices) > 100]
    
    if not meshes:
        print("  ❌ No mesh found")
        return False, {}
    
    mesh_obj = meshes[0]
    
    # Check shape keys
    shape_key_names = []
    if mesh_obj.data.shape_keys:
        shape_key_names = [kb.name for kb in mesh_obj.data.shape_keys.key_blocks if kb.name != 'Basis']
    
    verification = {
        'armature_present': len(armatures) > 0,
        'armature_count': len(armatures),
        'bone_count': len(armatures[0].data.bones) if armatures else 0,
        'mesh_present': len(meshes) > 0,
        'vertex_groups': len(mesh_obj.vertex_groups),
        'shape_keys_present': len(shape_key_names) > 0,
        'shape_key_count': len(shape_key_names),
        'shape_key_names': shape_key_names
    }
    
    print(f"  Armatures: {verification['armature_count']}")
    print(f"  Bones: {verification['bone_count']}")
    print(f"  Mesh vertex groups: {verification['vertex_groups']}")
    print(f"  Shape keys: {verification['shape_key_count']}")
    print(f"  Shape key names: {shape_key_names}")
    
    success = (
        verification['armature_present'] and
        verification['bone_count'] == 18 and
        verification['shape_keys_present']
    )
    
    if success:
        print("  ✅ Export verification passed")
    else:
        print("  ❌ Export verification failed")
    
    return success, verification


def main():
    """Main execution"""
    print("="*60)
    print("Facial Animation and Lip-Sync Setup")
    print("="*60)
    
    from datetime import datetime
    
    report = {
        'test_date': datetime.now().isoformat(),
        'input_file': INPUT_GLB,
        'output_file': OUTPUT_GLB,
        'topology_analysis': {},
        'shape_keys_created': [],
        'shape_keys_tested': [],
        'armature_verification': {},
        'export_verification': {},
        'overall_result': 'UNKNOWN'
    }
    
    # Step 1: Import
    print("\n[Step 1] Import rigged GLB")
    clear_scene()
    if not import_glb(INPUT_GLB):
        report['overall_result'] = 'FAIL'
        save_report(report)
        return False
    
    # Step 2: Find objects
    print("\n[Step 2] Find mesh and armature")
    mesh_obj = find_mesh()
    armature_obj = find_armature()
    
    if not mesh_obj:
        print("❌ No mesh found")
        report['overall_result'] = 'FAIL'
        save_report(report)
        return False
    
    print(f"  ✅ Mesh: {mesh_obj.name}")
    if armature_obj:
        print(f"  ✅ Armature: {armature_obj.name}")
    
    # Step 3: Analyze topology
    print("\n[Step 3] Analyze face topology")
    analysis = analyze_face_topology(mesh_obj)
    report['topology_analysis'] = analysis
    
    if not analysis['suitable_for_facial']:
        print("\n❌ TOPOLOGY NOT SUITABLE FOR FACIAL ANIMATION")
        print("\nLimitations:")
        for limitation in analysis['limitations']:
            print(f"  - {limitation}")
        
        report['overall_result'] = 'FAIL'
        report['failure_reason'] = 'Topology not suitable'
        save_report(report)
        return False
    
    # Step 4: Create shape keys
    print("\n[Step 4] Create facial shape keys")
    bpy.context.view_layer.objects.active = mesh_obj
    
    shape_key_results = create_facial_shape_keys(mesh_obj, analysis)
    report['shape_keys_created'] = shape_key_results
    
    # Step 5: Test shape keys
    print("\n[Step 5] Test shape keys")
    
    test_results = []
    for sk_result in shape_key_results:
        if sk_result['created']:
            works, details = test_shape_key(mesh_obj, sk_result['name'])
            test_results.append({
                'name': sk_result['name'],
                'exists': True,
                'produces_deformation': works,
                'details': details
            })
    
    report['shape_keys_tested'] = test_results
    
    # Step 6: Render expressions (if possible)
    print("\n[Step 6] Setup and render expressions")
    
    # Setup camera and lighting
    try:
        bounds = analysis['bounds']
        center = Vector(bounds['center'])
        
        # Camera
        bpy.ops.object.camera_add(location=(center.x + 1.5, center.y - 1.5, center.z + 0.5))
        camera = bpy.context.active_object
        direction = center - camera.location
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.camera = camera
        
        # Light
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
        light = bpy.context.active_object
        light.data.energy = 2
        
        # Render settings
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.scene.render.resolution_x = 800
        bpy.context.scene.render.resolution_y = 800
        
        rendering_enabled = True
    except Exception as e:
        print(f"  ⚠️  Render setup failed: {e}")
        rendering_enabled = False
    
    if rendering_enabled:
        for i, sk_result in enumerate(shape_key_results):
            if sk_result['created'] and sk_result['deformed_vertices'] > 0:
                render_path = render_shape_key(mesh_obj, sk_result['name'], i + 1)
                if render_path:
                    # Find matching test result and add render path
                    for test_result in test_results:
                        if test_result['name'] == sk_result['name']:
                            test_result['render_path'] = render_path
    
    # Step 7: Verify armature
    print("\n[Step 7] Verify armature")
    armature_ok, armature_msg = verify_armature(armature_obj)
    report['armature_verification'] = {
        'intact': armature_ok,
        'message': armature_msg
    }
    
    if armature_ok:
        print(f"  ✅ {armature_msg}")
    else:
        print(f"  ❌ {armature_msg}")
    
    # Step 8: Export
    print("\n[Step 8] Export with facial animation")
    export_success = export_glb(OUTPUT_GLB, mesh_obj, armature_obj)
    
    if not export_success:
        print("❌ Export failed")
        report['overall_result'] = 'FAIL'
        save_report(report)
        return False
    
    # Step 9: Verify export
    print("\n[Step 9] Verify exported GLB")
    verify_success, verify_data = verify_exported_glb(OUTPUT_GLB)
    report['export_verification'] = verify_data
    report['export_verification']['passed'] = verify_success
    
    # Step 10: Determine overall result
    all_shape_keys_work = all(t['produces_deformation'] for t in test_results if t['exists'])
    
    if verify_success and armature_ok and all_shape_keys_work:
        report['overall_result'] = 'PASS'
    else:
        report['overall_result'] = 'FAIL'
    
    # Save report
    save_report(report)
    
    # Print summary
    print("\n" + "="*60)
    if report['overall_result'] == 'PASS':
        print("FACIAL ANIMATION SETUP: PASS")
        print("="*60)
        print(f"✅ Created {len([r for r in shape_key_results if r['created']])} shape keys")
        print(f"✅ All shape keys produce deformation")
        print(f"✅ Armature intact ({armature_obj.name if armature_obj else 'N/A'})")
        print(f"✅ Export successful with morph targets")
        print(f"\n📄 Output: {OUTPUT_GLB}")
    else:
        print("FACIAL ANIMATION SETUP: FAIL")
        print("="*60)
        if not all_shape_keys_work:
            print("❌ Some shape keys don't produce deformation")
        if not armature_ok:
            print(f"❌ Armature problem: {armature_msg}")
        if not verify_success:
            print("❌ Export verification failed")
    
    if rendering_enabled:
        print(f"\n📷 Renders saved to: {RENDER_DIR}")
    
    print(f"\n📄 Report saved to: {REPORT_FILE}")
    print("="*60)
    
    return report['overall_result'] == 'PASS'


def save_report(report):
    """Save report to JSON"""
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"[Report] Failed to save: {e}")


if __name__ == "__main__":
    success = main()
    if not success:
        import sys
        sys.exit(1)
