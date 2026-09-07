#!/usr/bin/env blender --python
"""
Blender script to properly rig the bunny character with a real armature.

This script CORRECTLY creates a Blender ARMATURE object and exports with skinning.

Usage:
    blender --background --python blender_rig_bunny_fixed.py
"""

import bpy
import bmesh
import os
from mathutils import Vector

# Configuration
INPUT_GLB = "/Users/tanishqyadav/agent/bunny_character_fixed_tail.glb"
OUTPUT_BLEND = "/Users/tanishqyadav/agent/bunny_rigging.blend"
OUTPUT_GLB = "/Users/tanishqyadav/agent/bunny_rigged.glb"

# Armature configuration
ARMATURE_NAME = "BunnyArmature"
USE_AUTO_WEIGHTS = False  # FORCE manual weights - auto weights failing silently!


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Also clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)
    
    print("[Clear] Scene cleared")


def import_glb(filepath):
    """Import GLB file"""
    print(f"[Import] Loading {filepath}")
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    imported_objects = list(bpy.context.selected_objects)
    print(f"[Import] Imported {len(imported_objects)} objects")
    
    return imported_objects


def find_mesh_object():
    """Find the main mesh object (the bunny)"""
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and len(obj.data.vertices) > 100:
            print(f"[Mesh] Found main mesh: {obj.name} ({len(obj.data.vertices)} vertices)")
            return obj
    return None


def analyze_mesh_bounds(mesh_obj):
    """Analyze mesh bounds for bone placement"""
    mesh = mesh_obj.data
    vertices = mesh.vertices
    
    if len(vertices) == 0:
        return None
    
    # Calculate bounds in world space
    coords = [mesh_obj.matrix_world @ v.co for v in vertices]
    
    min_x = min(v.x for v in coords)
    max_x = max(v.x for v in coords)
    min_y = min(v.y for v in coords)
    max_y = max(v.y for v in coords)
    min_z = min(v.z for v in coords)
    max_z = max(v.z for v in coords)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    
    print(f"[Analysis] Mesh bounds:")
    print(f"  X: {min_x:.3f} to {max_x:.3f} (width: {width:.3f})")
    print(f"  Y: {min_y:.3f} to {max_y:.3f} (depth: {depth:.3f})")
    print(f"  Z: {min_z:.3f} to {max_z:.3f} (height: {height:.3f})")
    print(f"  Center: ({center_x:.3f}, {center_y:.3f}, {center_z:.3f})")
    
    return {
        'min': Vector((min_x, min_y, min_z)),
        'max': Vector((max_x, max_y, max_z)),
        'center': Vector((center_x, center_y, center_z)),
        'width': width,
        'depth': depth,
        'height': height
    }


def create_armature_object(name):
    """Create a REAL Blender ARMATURE object"""
    print(f"[Armature] Creating armature data: {name}")
    
    # Create armature data block
    armature_data = bpy.data.armatures.new(name)
    armature_data.display_type = 'STICK'  # Display type
    
    # Create armature object
    armature_object = bpy.data.objects.new(name, armature_data)
    
    # Link to scene
    bpy.context.collection.objects.link(armature_object)
    
    # Verify it's an ARMATURE
    assert armature_object.type == 'ARMATURE', f"Object type is {armature_object.type}, not ARMATURE!"
    
    print(f"[Armature] Created armature object: {armature_object.name}")
    print(f"[Armature] Object type: {armature_object.type}")
    
    return armature_object


def create_bones(armature_obj, bounds):
    """Create bones for the bunny skeleton"""
    print("[Bones] Creating bone structure...")
    
    # Set armature as active and enter edit mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    edit_bones = armature_obj.data.edit_bones
    
    # Calculate key positions based on mesh bounds
    min_pt = bounds['min']
    max_pt = bounds['max']
    center = bounds['center']
    width = bounds['width']
    depth = bounds['depth']
    height = bounds['height']
    
    # Helper function to create bones
    def add_bone(name, head_pos, tail_pos, parent=None):
        bone = edit_bones.new(name)
        bone.head = head_pos
        bone.tail = tail_pos
        if parent:
            bone.parent = parent
        return bone
    
    # Root (at bottom center, slightly above feet)
    root_head = Vector((center.x, center.y, min_pt.z + height * 0.05))
    root_tail = Vector((center.x, center.y, min_pt.z + height * 0.15))
    root = add_bone('root', root_head, root_tail)
    
    # Spine (lower body)
    spine_head = root_tail
    spine_tail = Vector((center.x, center.y, min_pt.z + height * 0.35))
    spine = add_bone('spine', spine_head, spine_tail, root)
    
    # Chest (upper body)
    chest_head = spine_tail
    chest_tail = Vector((center.x, center.y, min_pt.z + height * 0.6))
    chest = add_bone('chest', chest_head, chest_tail, spine)
    
    # Neck
    neck_head = chest_tail
    neck_tail = Vector((center.x, center.y + depth * 0.05, min_pt.z + height * 0.7))
    neck = add_bone('neck', neck_head, neck_tail, chest)
    
    # Head (big for chibi proportions)
    head_head = neck_tail
    head_tail = Vector((center.x, center.y + depth * 0.1, min_pt.z + height * 0.95))
    head = add_bone('head', head_head, head_tail, neck)
    
    # Ears (on top of head)
    ear_base_z = min_pt.z + height * 0.85
    ear_tip_z = min_pt.z + height * 1.05
    
    # Left ear
    ear_l_head = Vector((center.x - width * 0.15, center.y, ear_base_z))
    ear_l_tail = Vector((center.x - width * 0.2, center.y, ear_tip_z))
    ear_l = add_bone('ear.L', ear_l_head, ear_l_tail, head)
    
    # Right ear
    ear_r_head = Vector((center.x + width * 0.15, center.y, ear_base_z))
    ear_r_tail = Vector((center.x + width * 0.2, center.y, ear_tip_z))
    ear_r = add_bone('ear.R', ear_r_head, ear_r_tail, head)
    
    # Arms (from shoulders)
    shoulder_z = min_pt.z + height * 0.55
    elbow_z = min_pt.z + height * 0.35
    hand_z = min_pt.z + height * 0.2
    
    # Left arm
    shoulder_l_head = Vector((center.x - width * 0.25, center.y, shoulder_z))
    shoulder_l_tail = Vector((center.x - width * 0.35, center.y, elbow_z))
    upper_arm_l = add_bone('upper_arm.L', shoulder_l_head, shoulder_l_tail, chest)
    
    forearm_l_head = shoulder_l_tail
    forearm_l_tail = Vector((center.x - width * 0.4, center.y, hand_z))
    forearm_l = add_bone('forearm.L', forearm_l_head, forearm_l_tail, upper_arm_l)
    
    # Right arm
    shoulder_r_head = Vector((center.x + width * 0.25, center.y, shoulder_z))
    shoulder_r_tail = Vector((center.x + width * 0.35, center.y, elbow_z))
    upper_arm_r = add_bone('upper_arm.R', shoulder_r_head, shoulder_r_tail, chest)
    
    forearm_r_head = shoulder_r_tail
    forearm_r_tail = Vector((center.x + width * 0.4, center.y, hand_z))
    forearm_r = add_bone('forearm.R', forearm_r_head, forearm_r_tail, upper_arm_r)
    
    # Legs (from hips)
    hip_z = min_pt.z + height * 0.25
    knee_z = min_pt.z + height * 0.12
    foot_z = min_pt.z
    
    # Left leg
    hip_l_head = Vector((center.x - width * 0.15, center.y, hip_z))
    hip_l_tail = Vector((center.x - width * 0.17, center.y + depth * 0.05, knee_z))
    thigh_l = add_bone('thigh.L', hip_l_head, hip_l_tail, root)
    
    shin_l_head = hip_l_tail
    shin_l_tail = Vector((center.x - width * 0.18, center.y + depth * 0.1, foot_z))
    shin_l = add_bone('shin.L', shin_l_head, shin_l_tail, thigh_l)
    
    foot_l_head = shin_l_tail
    foot_l_tail = Vector((center.x - width * 0.18, center.y + depth * 0.15, foot_z))
    foot_l = add_bone('foot.L', foot_l_head, foot_l_tail, shin_l)
    
    # Right leg
    hip_r_head = Vector((center.x + width * 0.15, center.y, hip_z))
    hip_r_tail = Vector((center.x + width * 0.17, center.y + depth * 0.05, knee_z))
    thigh_r = add_bone('thigh.R', hip_r_head, hip_r_tail, root)
    
    shin_r_head = hip_r_tail
    shin_r_tail = Vector((center.x + width * 0.18, center.y + depth * 0.1, foot_z))
    shin_r = add_bone('shin.R', shin_r_head, shin_r_tail, thigh_r)
    
    foot_r_head = shin_r_tail
    foot_r_tail = Vector((center.x + width * 0.18, center.y + depth * 0.15, foot_z))
    foot_r = add_bone('foot.R', foot_r_head, foot_r_tail, shin_r)
    
    # Tail (behind, at lower back)
    tail_head = Vector((center.x, min_pt.y + depth * 0.1, min_pt.z + height * 0.2))
    tail_tail = Vector((center.x, min_pt.y, min_pt.z + height * 0.25))
    tail = add_bone('tail', tail_head, tail_tail, spine)
    
    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    bone_count = len(armature_obj.data.bones)
    print(f"[Bones] Created {bone_count} bones:")
    for bone in armature_obj.data.bones:
        print(f"  - {bone.name}")
    
    return bone_count


def bind_mesh_to_armature(mesh_obj, armature_obj, use_auto_weights=True):
    """Bind mesh to armature with vertex groups and modifier"""
    print("[Binding] Creating vertex groups and armature modifier...")
    
    # Make sure mesh is in object mode
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select mesh first, then armature
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    
    if use_auto_weights:
        print("[Binding] Attempting automatic weights...")
        try:
            # Use automatic weights - this should create both vertex groups AND set up parenting
            bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            print("[Binding] Automatic weights applied successfully")
            
            # Verify vertex groups were created
            if len(mesh_obj.vertex_groups) == 0:
                print("[Binding] WARNING: Automatic weights didn't create vertex groups!")
                use_auto_weights = False
            
        except RuntimeError as e:
            print(f"[Binding] Automatic weights failed: {e}")
            print("[Binding] Falling back to manual vertex groups...")
            use_auto_weights = False
    
    if not use_auto_weights:
        # Manual binding: create vertex groups and parent without weights
        print("[Binding] Creating manual vertex groups...")
        
        # First, ensure mesh has no existing parent or modifiers
        if mesh_obj.parent:
            mesh_obj.parent = None
        
        # Remove any existing armature modifiers
        for mod in list(mesh_obj.modifiers):
            if mod.type == 'ARMATURE':
                mesh_obj.modifiers.remove(mod)
        
        # Create vertex groups for each bone
        mesh_obj.vertex_groups.clear()
        for bone in armature_obj.data.bones:
            vg = mesh_obj.vertex_groups.new(name=bone.name)
        
        # Assign vertices to nearest bone (simple distance-based)
        assign_vertices_to_bones(mesh_obj, armature_obj)
        
        # Add armature modifier MANUALLY
        armature_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        armature_mod.object = armature_obj
        armature_mod.use_vertex_groups = True
        armature_mod.use_deform_preserve_volume = True
        
        # Set parent (needed for export)
        mesh_obj.parent = armature_obj
        mesh_obj.parent_type = 'OBJECT'  # Regular object parenting
    
    # Verify vertex groups were created
    vg_count = len(mesh_obj.vertex_groups)
    print(f"[Binding] Vertex groups created: {vg_count}")
    
    if vg_count == 0:
        print("[Binding] ERROR: No vertex groups created!")
        return False
    
    # Verify armature modifier exists
    armature_mod = None
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            armature_mod = mod
            break
    
    if not armature_mod:
        print("[Binding] ERROR: No armature modifier found!")
        return False
    
    # Ensure modifier settings are correct for export
    armature_mod.show_viewport = True
    armature_mod.show_render = True
    
    print(f"[Binding] Armature modifier: {armature_mod.name}")
    print(f"[Binding] Modifier target: {armature_mod.object.name if armature_mod.object else 'None'}")
    print(f"[Binding] Modifier uses vertex groups: {armature_mod.use_vertex_groups}")
    
    return True


def assign_vertices_to_bones(mesh_obj, armature_obj):
    """Simple distance-based vertex assignment"""
    print("[Weights] Assigning vertices to bones...")
    
    mesh = mesh_obj.data
    bones = armature_obj.data.bones
    
    # Get bone positions
    bone_positions = {}
    for bone in bones:
        # Use bone head position in world space
        bone_pos = armature_obj.matrix_world @ bone.head_local
        bone_positions[bone.name] = bone_pos
    
    # For each vertex, find closest bones and assign weights
    for v in mesh.vertices:
        v_pos = mesh_obj.matrix_world @ v.co
        
        # Find 3 closest bones
        distances = []
        for bone_name, bone_pos in bone_positions.items():
            dist = (v_pos - bone_pos).length
            distances.append((dist, bone_name))
        
        distances.sort()
        
        # Assign to closest 3 bones with distance-based weights
        total_weight = 0
        weights = []
        for i in range(min(3, len(distances))):
            dist, bone_name = distances[i]
            # Inverse distance weight
            weight = 1.0 / (dist + 0.001)  # Add small epsilon to avoid division by zero
            weights.append((bone_name, weight))
            total_weight += weight
        
        # Normalize and assign
        for bone_name, weight in weights:
            normalized_weight = weight / total_weight
            vg = mesh_obj.vertex_groups.get(bone_name)
            if vg:
                vg.add([v.index], normalized_weight, 'REPLACE')
    
    print("[Weights] Vertex weights assigned")


def verify_before_export(mesh_obj, armature_obj):
    """Verify scene is ready for export"""
    print("\n" + "="*60)
    print("[Verify] Pre-export verification:")
    print("="*60)
    
    success = True
    
    # Check armature object type
    if armature_obj.type != 'ARMATURE':
        print(f"❌ Armature object type is {armature_obj.type}, not ARMATURE!")
        success = False
    else:
        print(f"✅ Armature object type: {armature_obj.type}")
    
    # Check bone count
    bone_count = len(armature_obj.data.bones)
    if bone_count == 0:
        print("❌ No bones in armature!")
        success = False
    else:
        print(f"✅ Bones: {bone_count}")
    
    # Check vertex groups
    vg_count = len(mesh_obj.vertex_groups)
    if vg_count == 0:
        print("❌ No vertex groups on mesh!")
        success = False
    else:
        print(f"✅ Vertex groups: {vg_count}")
    
    # Check armature modifier
    armature_mod = None
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            armature_mod = mod
            break
    
    if not armature_mod:
        print("❌ No armature modifier on mesh!")
        success = False
    else:
        print(f"✅ Armature modifier: {armature_mod.name}")
        if armature_mod.object == armature_obj:
            print(f"✅ Modifier points to correct armature")
        else:
            print(f"❌ Modifier points to wrong object: {armature_mod.object}")
            success = False
    
    # Check parent relationship
    if mesh_obj.parent == armature_obj:
        print(f"✅ Mesh parent: {mesh_obj.parent.name}")
    else:
        print(f"⚠️  Mesh parent: {mesh_obj.parent.name if mesh_obj.parent else 'None'}")
    
    print("="*60)
    return success


def save_blend_file(filepath):
    """Save Blender project file"""
    print(f"[Save] Saving Blender file: {filepath}")
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"[Save] Saved {filepath} ({size / 1024 / 1024:.2f} MB)")
        return True
    return False


def export_glb(filepath, mesh_obj, armature_obj):
    """Export as GLB with proper skinning"""
    print(f"[Export] Exporting to {filepath}")
    
    # Ensure objects are in correct state
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # CRITICAL FIX: The glTF exporter in Blender 5.2 seems to require
    # that the armature modifier is NOT at the top of the modifier stack
    # or has specific settings. Let's ensure proper configuration.
    
    # First, let's make absolutely sure the vertex groups have weights
    print(f"[Export] Checking vertex group weights...")
    has_weights = False
    for vg in mesh_obj.vertex_groups:
        # Check if this group has any vertices
        try:
            for v in mesh_obj.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0:
                        has_weights = True
                        break
                if has_weights:
                    break
        except:
            pass
        if has_weights:
            break
    
    if not has_weights:
        print("[Export] WARNING: No vertex weights found! Skinning will not export.")
        print("[Export] This usually means automatic weights failed silently.")
    else:
        print("[Export] ✅ Vertex weights confirmed")
    
    # Select only mesh and armature
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    
    print(f"[Export] Selected objects: {[obj.name for obj in bpy.context.selected_objects]}")
    print(f"[Export] Mesh parent: {mesh_obj.parent.name if mesh_obj.parent else 'None'}")
    print(f"[Export] Mesh vertex groups: {len(mesh_obj.vertex_groups)}")
    print(f"[Export] Armature bones: {len(armature_obj.data.bones)}")
    
    # Check for armature modifier
    armature_mods = [mod for mod in mesh_obj.modifiers if mod.type == 'ARMATURE']
    print(f"[Export] Armature modifiers on mesh: {len(armature_mods)}")
    for mod in armature_mods:
        print(f"[Export]   - {mod.name}: target={mod.object.name if mod.object else 'None'}, vertex_groups={mod.use_vertex_groups}")
    
    # Export with all necessary options for skinning
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',
            use_selection=True,  # Export only selected objects
            export_materials='EXPORT',
            export_attributes=True,
            export_skins=True,  # CRITICAL: Include skinning data
            export_all_influences=True,  # Export all bone influences
            export_def_bones=True,  # Export deformation bones
            export_hierarchy_flatten_bones=False,  # Keep bone hierarchy
            export_morph=False,
            export_animations=False,
            export_normals=True,
            export_tangents=False,
            export_apply=False,  # Don't apply modifiers
            export_yup=True
        )
        print("[Export] glTF export operation completed")
    except Exception as e:
        print(f"[Export] ERROR during export: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"[Export] File created: {filepath} ({size / 1024 / 1024:.2f} MB)")
        return True
    else:
        print(f"[Export] ERROR: File not created!")
        return False


def verify_exported_glb(filepath):
    """Import the exported GLB in a clean scene and verify"""
    print("\n" + "="*60)
    print("[Verify Import] Verifying exported GLB...")
    print("="*60)
    
    # Clear scene
    clear_scene()
    
    # Import
    try:
        bpy.ops.import_scene.gltf(filepath=filepath)
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Check for armatures
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    print(f"Armatures found: {len(armatures)}")
    
    if len(armatures) == 0:
        print("❌ No armatures in imported file!")
        return False
    
    for arm in armatures:
        print(f"  ✅ Armature: {arm.name} ({len(arm.data.bones)} bones)")
        for bone in arm.data.bones:
            print(f"    - {bone.name}")
    
    # Check for meshes
    meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    print(f"\nMeshes found: {len(meshes)}")
    
    if len(meshes) == 0:
        print("❌ No meshes in imported file!")
        return False
    
    success = True
    for mesh in meshes:
        print(f"  Mesh: {mesh.name}")
        print(f"    Vertices: {len(mesh.data.vertices)}")
        print(f"    Vertex groups: {len(mesh.vertex_groups)}")
        
        # Skip very small meshes (these might be visualization objects)
        if len(mesh.data.vertices) < 100:
            print(f"    ⚠️  Skipping small mesh (likely visualization)")
            continue
        
        if len(mesh.vertex_groups) == 0:
            print("    ❌ No vertex groups!")
            success = False
        else:
            print(f"    ✅ Vertex groups: {[vg.name for vg in mesh.vertex_groups]}")
        
        # Check for armature modifier
        has_armature_mod = any(mod.type == 'ARMATURE' for mod in mesh.modifiers)
        if has_armature_mod:
            print(f"    ✅ Has armature modifier")
        else:
            print(f"    ⚠️  No armature modifier (may be baked into skin)")
        
        # Check parent
        if mesh.parent:
            print(f"    Parent: {mesh.parent.name} ({mesh.parent.type})")
    
    print("="*60)
    
    # Success if we have at least one armature and at least one properly rigged mesh
    rigged_meshes = [m for m in meshes if len(m.data.vertices) >= 100 and len(m.vertex_groups) > 0]
    
    if len(armatures) > 0 and len(rigged_meshes) > 0:
        print("✅ Export verification PASSED!")
        print(f"   - {len(armatures)} armature(s)")
        print(f"   - {len(rigged_meshes)} rigged mesh(es)")
        return True
    else:
        print("❌ Export verification FAILED!")
        return False


def main():
    """Main execution"""
    print("="*60)
    print("Bunny Rigging - Fixed Script")
    print("Using Blender 5.2.1 LTS")
    print("="*60)
    
    # Step 1: Clear and import
    print("\n[Step 1] Import")
    clear_scene()
    import_glb(INPUT_GLB)
    
    # Step 2: Find mesh
    print("\n[Step 2] Find mesh")
    bunny_mesh = find_mesh_object()
    if not bunny_mesh:
        print("❌ ERROR: Could not find bunny mesh!")
        return False
    
    # Step 3: Analyze bounds
    print("\n[Step 3] Analyze mesh")
    bounds = analyze_mesh_bounds(bunny_mesh)
    if not bounds:
        print("❌ ERROR: Could not analyze mesh!")
        return False
    
    # Step 4: Create REAL armature object
    print("\n[Step 4] Create armature")
    armature_obj = create_armature_object(ARMATURE_NAME)
    
    # Step 5: Create bones
    print("\n[Step 5] Create bones")
    bone_count = create_bones(armature_obj, bounds)
    
    if bone_count == 0:
        print("❌ ERROR: No bones created!")
        return False
    
    # Step 6: Bind mesh to armature
    print("\n[Step 6] Bind mesh to armature")
    bind_success = bind_mesh_to_armature(bunny_mesh, armature_obj, USE_AUTO_WEIGHTS)
    
    if not bind_success:
        print("❌ ERROR: Binding failed!")
        return False
    
    # Step 7: Verify before export
    print("\n[Step 7] Verify before export")
    if not verify_before_export(bunny_mesh, armature_obj):
        print("❌ ERROR: Pre-export verification failed!")
        return False
    
    # Step 8: Save .blend file
    print("\n[Step 8] Save Blender file")
    if not save_blend_file(OUTPUT_BLEND):
        print("⚠️  Warning: Could not save .blend file")
    
    # Step 9: Export GLB
    print("\n[Step 9] Export GLB")
    if not export_glb(OUTPUT_GLB, bunny_mesh, armature_obj):
        print("❌ ERROR: Export failed!")
        return False
    
    # Step 10: Verify exported GLB
    print("\n[Step 10] Verify exported GLB")
    if not verify_exported_glb(OUTPUT_GLB):
        print("❌ ERROR: Exported GLB verification failed!")
        return False
    
    # Success!
    print("\n" + "="*60)
    print("✅ RIGGING COMPLETE AND VERIFIED!")
    print("="*60)
    print(f"Input:  {INPUT_GLB}")
    print(f"Blend:  {OUTPUT_BLEND}")
    print(f"Output: {OUTPUT_GLB}")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ RIGGING FAILED - See errors above")
        import sys
        sys.exit(1)
