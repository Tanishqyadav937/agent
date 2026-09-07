#!/usr/bin/env blender --python
"""
Inspect the bunny GLB file to understand its structure.

Usage:
    blender --background --python blender_inspect.py
"""

import bpy
import json

INPUT_GLB = "/Users/tanishqyadav/agent/bunny_character_triposr.glb"
REPORT_FILE = "/Users/tanishqyadav/agent/bunny_inspection_report.json"


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def inspect_glb():
    """Inspect GLB structure"""
    clear_scene()
    
    print("="*60)
    print(f"Inspecting: {INPUT_GLB}")
    print("="*60)
    
    # Import
    bpy.ops.import_scene.gltf(filepath=INPUT_GLB)
    
    report = {
        "file": INPUT_GLB,
        "objects": [],
        "materials": [],
        "meshes": []
    }
    
    # Inspect objects
    print("\n[Objects]")
    for obj in bpy.data.objects:
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale)
        }
        
        print(f"  {obj.name}")
        print(f"    Type: {obj.type}")
        print(f"    Location: ({obj.location.x:.3f}, {obj.location.y:.3f}, {obj.location.z:.3f})")
        
        if obj.type == 'MESH':
            mesh = obj.data
            verts = len(mesh.vertices)
            faces = len(mesh.polygons)
            
            # Calculate bounds
            if verts > 0:
                min_x = min(v.co.x for v in mesh.vertices)
                max_x = max(v.co.x for v in mesh.vertices)
                min_y = min(v.co.y for v in mesh.vertices)
                max_y = max(v.co.y for v in mesh.vertices)
                min_z = min(v.co.z for v in mesh.vertices)
                max_z = max(v.co.z for v in mesh.vertices)
                
                obj_info["mesh"] = {
                    "vertices": verts,
                    "faces": faces,
                    "bounds": {
                        "x": [min_x, max_x],
                        "y": [min_y, max_y],
                        "z": [min_z, max_z]
                    }
                }
                
                print(f"    Vertices: {verts}")
                print(f"    Faces: {faces}")
                print(f"    Bounds:")
                print(f"      X: {min_x:.3f} to {max_x:.3f} (width: {max_x-min_x:.3f})")
                print(f"      Y: {min_y:.3f} to {max_y:.3f} (depth: {max_y-min_y:.3f})")
                print(f"      Z: {min_z:.3f} to {max_z:.3f} (height: {max_z-min_z:.3f})")
                
                # Identify potential tail (lowest Y values)
                tail_threshold = min_y + (max_y - min_y) * 0.2
                tail_verts = [v for v in mesh.vertices if v.co.y < tail_threshold]
                print(f"    Potential tail vertices (Y < {tail_threshold:.3f}): {len(tail_verts)}")
                
            # Check materials
            if len(obj.material_slots) > 0:
                print(f"    Materials: {[slot.material.name if slot.material else 'None' for slot in obj.material_slots]}")
                obj_info["materials"] = [slot.material.name if slot.material else None for slot in obj.material_slots]
        
        report["objects"].append(obj_info)
    
    # Inspect materials
    print("\n[Materials]")
    for mat in bpy.data.materials:
        mat_info = {
            "name": mat.name,
            "use_nodes": mat.use_nodes
        }
        
        print(f"  {mat.name}")
        if mat.use_nodes:
            print(f"    Nodes: {len(mat.node_tree.nodes)}")
            mat_info["nodes"] = [node.type for node in mat.node_tree.nodes]
        
        report["materials"].append(mat_info)
    
    # Inspect images/textures
    print("\n[Textures]")
    if len(bpy.data.images) > 0:
        for img in bpy.data.images:
            print(f"  {img.name}")
            print(f"    Size: {img.size[0]}x{img.size[1]}")
    else:
        print("  No textures found")
    
    # Save report
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n="*60)
    print(f"✅ Inspection complete!")
    print(f"   Report saved to: {REPORT_FILE}")
    print("="*60)


if __name__ == "__main__":
    inspect_glb()
