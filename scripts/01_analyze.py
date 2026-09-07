"""
01_analyze.py
Analyze bunny_rigged.glb: list all objects, bones, meshes, materials.
Outputs analysis to /Users/tanishqyadav/agent/analysis_result.json
"""
import bpy
import json
import sys
import math

OUTPUT = "/Users/tanishqyadav/agent/analysis_result.json"
GLB    = "/Users/tanishqyadav/agent/bunny_rigged.glb"

# ── Clean scene ──────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ── Import ───────────────────────────────────────────────────────────────────
bpy.ops.import_scene.gltf(filepath=GLB)
print(f"Imported {GLB}")

result = {
    "objects": [],
    "armatures": [],
    "meshes": [],
    "materials": [],
    "head_bone_candidates": [],
}

# ── Walk all objects ─────────────────────────────────────────────────────────
for obj in bpy.data.objects:
    entry = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "parent": obj.parent.name if obj.parent else None,
    }

    if obj.type == 'ARMATURE':
        bones_info = []
        for bone in obj.data.bones:
            binfo = {
                "name": bone.name,
                "head": list(bone.head_local),
                "tail": list(bone.tail_local),
                "parent": bone.parent.name if bone.parent else None,
                "children": [c.name for c in bone.children],
            }
            bones_info.append(binfo)
        entry["bones"] = bones_info
        entry["bone_count"] = len(bones_info)
        result["armatures"].append(entry)

        # Find likely head bone (highest z, name contains 'head')
        for bone in obj.data.bones:
            if any(kw in bone.name.lower() for kw in ['head', 'neck', 'skull', 'face']):
                result["head_bone_candidates"].append({
                    "bone_name": bone.name,
                    "armature": obj.name,
                    "head_pos": list(bone.head_local),
                    "tail_pos": list(bone.tail_local),
                })

    elif obj.type == 'MESH':
        mesh = obj.data
        vcount = len(mesh.vertices)
        fcount = len(mesh.polygons)

        # Sample vertex positions
        sample_verts = [list(v.co) for v in mesh.vertices[:5]]

        # Shape keys
        sk_names = []
        if mesh.shape_keys:
            sk_names = [sk.name for sk in mesh.shape_keys.key_blocks]

        # Vertex groups
        vg_names = [vg.name for vg in obj.vertex_groups]

        # Bounding box
        bbox = [list(c) for c in obj.bound_box]
        bb_min = [min(c[i] for c in obj.bound_box) for i in range(3)]
        bb_max = [max(c[i] for c in obj.bound_box) for i in range(3)]

        mat_names = [m.name if m else "None" for m in mesh.materials]

        minfo = {
            "name": obj.name,
            "vertex_count": vcount,
            "face_count": fcount,
            "sample_vertices": sample_verts,
            "shape_keys": sk_names,
            "vertex_groups": vg_names,
            "materials": mat_names,
            "bb_min": bb_min,
            "bb_max": bb_max,
            "location": list(obj.location),
            "parent": obj.parent.name if obj.parent else None,
            "armature_modifier": None,
        }

        # Check for armature modifier
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE':
                minfo["armature_modifier"] = mod.object.name if mod.object else "unnamed"

        result["meshes"].append(minfo)
        entry["vertex_count"] = vcount

    result["objects"].append(entry)

# ── Materials ────────────────────────────────────────────────────────────────
for mat in bpy.data.materials:
    result["materials"].append({
        "name": mat.name,
        "use_nodes": mat.use_nodes,
        "node_count": len(mat.node_tree.nodes) if mat.use_nodes and mat.node_tree else 0,
    })

# ── Print summary ────────────────────────────────────────────────────────────
print("\n=== ANALYSIS SUMMARY ===")
print(f"Objects: {len(result['objects'])}")
print(f"Armatures: {len(result['armatures'])}")
for arm in result['armatures']:
    print(f"  {arm['name']}: {arm['bone_count']} bones")
    for b in arm.get('bones', []):
        print(f"    {b['name']:30s}  parent={b['parent']}")
print(f"Meshes: {len(result['meshes'])}")
for m in result['meshes']:
    print(f"  {m['name']:30s}  verts={m['vertex_count']}  bb_min={[round(x,3) for x in m['bb_min']]}  bb_max={[round(x,3) for x in m['bb_max']]}")
print(f"Head bone candidates: {result['head_bone_candidates']}")
print(f"Materials: {[m['name'] for m in result['materials']]}")

# ── Write JSON ───────────────────────────────────────────────────────────────
with open(OUTPUT, 'w') as f:
    json.dump(result, f, indent=2)
print(f"\nAnalysis written to {OUTPUT}")
