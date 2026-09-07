# Bunny Character — Facial / Lip-Sync System Status

**Status: COMPLETE ✅**
**Date:** 2026-08-31
**Output:** `/Users/tanishqyadav/agent/bunny_character_lipsync.glb` (5.84 MB)

---

## What Was Built

The original `bunny_rigged.glb` mesh (`mesh.glb`, 61,517 verts, TripoSR topology) is unsuitable for facial shape keys — the existing facial geometry has no dedicated face topology. A **hybrid facial system** was used instead: two separate low-poly meshes were created and attached to the existing rig.

### Facial Geometry Added

| Object | Verts | Faces | Purpose |
|---|---|---|---|
| `FaceMouth` | 17 | 16 | Lip ring with all mouth/viseme controls |
| `FaceEyes` | 32 | 14 | Two eye arc panels with blink controls |

**Skinning method:** Armature modifier + 100% vertex weight to `head` bone. This is GLB-compatible (GLTF skin weights), unlike Blender's internal bone-parent which is not preserved across GLB export/import.

### Everything Preserved

- ✅ Original body mesh (`mesh.glb`) — untouched, all 61,542 verts
- ✅ `BunnyArmature` — 18 bones, hierarchy unchanged
- ✅ Original skinning on body mesh
- ✅ Tail mesh (`Icosphere`)
- ✅ All original materials: `Dots Stroke`, `Material`, `Material_0`

---

## Facial Controls

### Mouth Controls (`FaceMouth`)

| Shape Key | Max Displacement | Description |
|---|---|---|
| `jawOpen` | 25.0 mm | Lower lip/jaw drops open |
| `mouthClose` | 12.0 mm | Inner ring closes toward center |
| `mouthSmile` | 20.6 mm | Corners pull wide and up |
| `mouthPucker` | 16.1 mm | Lips protrude forward, squeeze in |
| `viseme_A` | 28.0 mm | "ahh" — wide open jaw |
| `viseme_E` | 22.0 mm | "ehh" — corners wide, slight open |
| `viseme_I` | 17.0 mm | "eee" — narrow, slight smile |
| `viseme_O` | 19.7 mm | "ohh" — rounded, moderate open |
| `viseme_U` | 21.3 mm | "ooo" — tight forward pucker |

### Eye Controls (`FaceEyes`)

| Shape Key | Max Displacement | Description |
|---|---|---|
| `blink.L` | 23.4 mm | Left upper lid sweeps down to close |
| `blink.R` | 23.4 mm | Right upper lid sweeps down to close |

---

## Verification Results

### Shape Key Tests — 11/11 PASS

All shape keys tested by activating to value=1.0 and measuring maximum vertex displacement vs. Basis. Minimum threshold: 1mm. All controls exceed threshold by 10–28×.

### Head-Following Test — PASS

Facial geometry was verified to follow the `head` bone using Blender's depsgraph evaluated mesh:

| Mesh | Delta on 30° head rotation |
|---|---|
| FaceMouth | **45.4 mm** |
| FaceEyes | **66.4 mm** |

### GLB Re-Import Verification — **35/35 PASS**

Imported in a clean Blender process (no carry-over state). Every check passed:

- BunnyArmature present with 18 bones
- Body mesh present with 61,542 verts, armature modifier, 18 vertex groups
- FaceMouth present with all 9 mouth shape keys
- FaceEyes present with both blink shape keys
- All shape keys produce real deformation (confirmed on re-imported data)
- Both facial meshes have armature modifier + `head` vertex group
- All original materials present

---

## Test Renders

Located in `/Users/tanishqyadav/agent/renders/` (512×512 PNG, Eevee):

| File | Pose |
|---|---|
| `neutral.png` | Rest pose |
| `jaw_open.png` | jawOpen = 1.0 |
| `smile.png` | mouthSmile = 1.0 |
| `pucker.png` | mouthPucker = 1.0 |
| `blink.png` | blink.L = blink.R = 1.0 |
| `viseme_A.png` | viseme_A = 1.0 |

---

## Using the Controls

### In Three.js / React Three Fiber
```js
// Access by mesh name
const mouthMesh = gltf.scene.getObjectByName('FaceMouth');
const eyesMesh  = gltf.scene.getObjectByName('FaceEyes');

// Morph target indices match shape key order (0-indexed, Basis excluded)
mouthMesh.morphTargetInfluences[0] = 1.0;  // jawOpen
mouthMesh.morphTargetInfluences[4] = 0.8;  // viseme_A
eyesMesh.morphTargetInfluences[0]  = 1.0;  // blink.L
eyesMesh.morphTargetInfluences[1]  = 1.0;  // blink.R
```

### Morph Target Index Map

**FaceMouth:**
```
0: jawOpen    1: mouthClose   2: mouthSmile  3: mouthPucker
4: viseme_A   5: viseme_E     6: viseme_I    7: viseme_O    8: viseme_U
```

**FaceEyes:**
```
0: blink.L    1: blink.R
```

### In Blender
```python
mouth = bpy.data.objects['FaceMouth']
mouth.data.shape_keys.key_blocks['jawOpen'].value = 1.0
```

---

## Scripts

All scripts are in `/Users/tanishqyadav/agent/scripts/`:

| Script | Purpose |
|---|---|
| `01_analyze.py` | Inspect original GLB structure |
| `02_build_facial.py` | Build facial system, export GLB |
| `03_render_tests.py` | Render 6 test poses |
| `04_verify_glb.py` | 35-check automated verification |
| `check_head_follow_v2.py` | Depsgraph head-follow test |

---

## Known Constraints

1. **Mesh simplicity by design.** The facial meshes are intentionally low-poly (17 and 32 verts). They are functional control surfaces, not high-fidelity face geometry. The visual appearance relies on the existing bunny body mesh for the overall look.

2. **No texture on facial meshes.** FaceMouth reuses the existing `Material`. FaceEyes uses a new flat dark `EyeMaterial`. Neither has UV-mapped textures — adding textured geometry would require manual UV work outside this automated pipeline.

3. **GLB parent_type is OBJECT, not BONE.** This is expected — GLTF does not have a bone-parent concept separate from skinning. The head-following is driven by vertex weights (100% to `head`), which is the correct GLTF-native mechanism and is verified working.
