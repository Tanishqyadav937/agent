#!/usr/bin/env blender --python
"""
Blender script to fix the bunny's dinosaur-like long tail into a short, rounded bunny tail.

Usage:
    blender --background --python blender_fix_tail.py

Or run inside Blender's Scripting workspace.
"""

import bpy
import bmesh
import os
from mathutils import Vector

# Configuration
INPUT_GLB = "/Users/tanishqyadav/agent/bunny_character_triposr.glb"
OUTPUT_GLB = "/Users/tanishqyadav/agent/bunny_character_fixed_tail.glb"
BACKUP_GLB = "/Users/tanishqyadav/agent/bunny_character_triposr_backup.glb"

# Tail modification parameters
TAIL_SHORTEN_FACTOR = 0.3  # Keep only 30% of tail length
TAIL_ROUNDNESS = 1.5       # How rounded the tail should be (1.0 = no change, >1 = more round)


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    print("[Clear] Scene cleared")


def import_glb(filepath):
    """Import GLB file"""
    print(f"[Import] Loading {filepath}")
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    # Get imported objects
    imported_objects = [obj for obj in bpy.context.selected_objects]
    print(f"[Import] Imported {len(imported_objects)} objects")
    
    return imported_objects


def find_mesh_object():
    """Find the main mesh object (usually the bunny)"""
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and len(obj.data.vertices) > 100:
            print(f"[Mesh] Found main mesh: {obj.name} ({len(obj.data.vertices)} vertices)")
            return obj
    return None


def backup_glb():
    """Create backup of original file"""
    if not os.path.exists(BACKUP_GLB):
        import shutil
        shutil.copy2(INPUT_GLB, BACKUP_GLB)
        print(f"[Backup] Created backup: {BACKUP_GLB}")
    else:
        print(f"[Backup] Backup already exists: {BACKUP_GLB}")


def analyze_tail_geometry(obj):
    """Analyze the mesh to identify tail vertices"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    
    # Calculate bounding box
    vertices = [v for v in bm.verts]
    if not vertices:
        print("[Error] No vertices found")
        return None
    
    # Find extremes
    min_x = min(v.co.x for v in vertices)
    max_x = max(v.co.x for v in vertices)
    min_y = min(v.co.y for v in vertices)
    max_y = max(v.co.y for v in vertices)
    min_z = min(v.co.z for v in vertices)
    max_z = max(v.co.z for v in vertices)
    
    print(f"[Analysis] Bounding box:")
    print(f"  X: {min_x:.3f} to {max_x:.3f}")
    print(f"  Y: {min_y:.3f} to {max_y:.3f}")
    print(f"  Z: {min_z:.3f} to {max_z:.3f}")
    
    # Assume tail extends in -Y direction (behind the bunny)
    # Find vertices that are significantly behind the center
    center_y = (min_y + max_y) / 2
    tail_threshold = min_y + (max_y - min_y) * 0.2  # Bottom 20% in Y
    
    tail_verts = [v for v in vertices if v.co.y < tail_threshold]
    print(f"[Analysis] Identified {len(tail_verts)} tail vertices (Y < {tail_threshold:.3f})")
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return {
        'tail_verts_count': len(tail_verts),
        'bounds': {'min_y': min_y, 'max_y': max_y, 'center_y': center_y},
        'tail_threshold': tail_threshold
    }


def fix_tail_automated(obj, info):
    """Automatically shorten and round the tail"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    # Select tail vertices
    tail_threshold = info['tail_threshold']
    min_y = info['bounds']['min_y']
    max_y = info['bounds']['max_y']
    center_y = info['bounds']['center_y']
    
    # Calculate where the shortened tail should end
    tail_length = abs(min_y - tail_threshold)
    new_tail_end = tail_threshold - (tail_length * TAIL_SHORTEN_FACTOR)
    
    print(f"[Tail Fix] Original tail end: {min_y:.3f}")
    print(f"[Tail Fix] New tail end: {new_tail_end:.3f}")
    print(f"[Tail Fix] Shortening by {(1-TAIL_SHORTEN_FACTOR)*100:.0f}%")
    
    modified_count = 0
    for v in bm.verts:
        if v.co.y < tail_threshold:
            # This is a tail vertex
            # Calculate how far along the tail it is (0 = base, 1 = tip)
            if v.co.y < new_tail_end:
                # Beyond new tail end - move it to the new end and round it
                tail_position = (v.co.y - tail_threshold) / tail_length
                
                # Move vertex toward new end
                v.co.y = new_tail_end
                
                # Add roundness by pulling vertices toward center
                # More rounding at the tip
                rounding_factor = abs(tail_position) * TAIL_ROUNDNESS * 0.5
                center_xz = Vector((0, v.co.y, center_y))
                v.co.x = v.co.x * (1 - rounding_factor)
                v.co.z = v.co.z * (1 - rounding_factor) + center_y * rounding_factor
                
                modified_count += 1
    
    bmesh.update_edit_mesh(mesh)
    print(f"[Tail Fix] Modified {modified_count} vertices")
    
    bpy.ops.object.mode_set(mode='OBJECT')


def cleanup_mesh(obj):
    """Clean up mesh: remove doubles, fix normals"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    print("[Cleanup] Removing doubles...")
    bpy.ops.mesh.select_all(action='SELECT')
    result = bpy.ops.mesh.remove_doubles(threshold=0.0001)
    print(f"[Cleanup] {result}")
    
    print("[Cleanup] Recalculating normals...")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    
    print("[Cleanup] Checking for non-manifold geometry...")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    non_manifold_count = len([v for v in obj.data.vertices if v.select])
    if non_manifold_count > 0:
        print(f"[Cleanup] Warning: {non_manifold_count} non-manifold vertices found")
        # Attempt to fix
        bpy.ops.mesh.fill_holes()
    else:
        print("[Cleanup] No non-manifold geometry found")
    
    bpy.ops.object.mode_set(mode='OBJECT')


def smooth_tail(obj):
    """Apply smoothing to make tail look more natural"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Select tail region and smooth
    print("[Smooth] Applying Laplacian smooth to tail region...")
    
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    
    # Select lower Y vertices (tail area)
    bpy.ops.mesh.select_all(action='DESELECT')
    min_y = min(v.co.y for v in bm.verts)
    max_y = max(v.co.y for v in bm.verts)
    tail_threshold = min_y + (max_y - min_y) * 0.3
    
    for v in bm.verts:
        if v.co.y < tail_threshold:
            v.select = True
    
    bmesh.update_edit_mesh(mesh)
    
    # Apply smooth
    bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=3)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print("[Smooth] Smoothing complete")


def export_glb(filepath):
    """Export as GLB with all settings preserved"""
    print(f"[Export] Saving to {filepath}")
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        export_materials='EXPORT',
        export_attributes=True,
        export_normals=True,
        export_tangents=False,
        export_apply=False,  # Don't apply modifiers
        export_yup=True
    )
    
    # Check file size
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"[Export] Exported {filepath} ({size / 1024 / 1024:.2f} MB)")
    else:
        print(f"[Export] Warning: File not created at {filepath}")


def main():
    """Main execution"""
    print("="*60)
    print("Bunny Tail Fix - Automated Script")
    print("="*60)
    
    # Step 1: Backup original
    backup_glb()
    
    # Step 2: Clear and import
    clear_scene()
    import_glb(INPUT_GLB)
    
    # Step 3: Find mesh
    bunny = find_mesh_object()
    if not bunny:
        print("[Error] Could not find bunny mesh!")
        return
    
    # Step 4: Analyze tail
    info = analyze_tail_geometry(bunny)
    if not info:
        print("[Error] Could not analyze tail!")
        return
    
    # Step 5: Fix tail
    fix_tail_automated(bunny, info)
    
    # Step 6: Smooth tail
    smooth_tail(bunny)
    
    # Step 7: Cleanup
    cleanup_mesh(bunny)
    
    # Step 8: Export
    export_glb(OUTPUT_GLB)
    
    print("="*60)
    print("✅ Tail fix complete!")
    print(f"   Original: {INPUT_GLB}")
    print(f"   Fixed:    {OUTPUT_GLB}")
    print(f"   Backup:   {BACKUP_GLB}")
    print("="*60)
    print("\nNext steps:")
    print("1. Open fixed GLB in Blender to visually verify")
    print("2. If satisfied, proceed to rigging")
    print("3. If tail needs adjustment, edit TAIL_SHORTEN_FACTOR/TAIL_ROUNDNESS")


if __name__ == "__main__":
    main()
