# Hangar41

**The first working OBJ importer for X-Plane — import any cockpit directly into Blender 4.1, edit it, and export it back to X-Plane.**

Until now, there was no way to bring an existing X-Plane `.obj` file back into Blender for editing. You had to keep the original `.blend` file or start from scratch. Hangar41 changes that.

---

## What It Does

### OBJ Importer
- Import any X-Plane `.obj` file directly into Blender 4.1
- Full animation hierarchy reconstructed — `ANIM_trans`, `ANIM_rotate`, show/hide
- `drag_rotate` manipulators with detent ranges (flap handles, speedbrakes, gear levers)
- Complete round-trip: import → edit → export → works identically in X-Plane

### Exporter Bug Fixes
- **`drag_rotate` v2_max**: Fixed a bug where the physical lift distance was used as `v2_max` instead of the dataref's actual maximum value — causing flap handles and speedbrakes to break on export
- **Detent range validator**: Fixed overly strict validation that blocked export of valid Plane Maker–generated OBJs

### Blender 4.1 Compatibility
All Blender 4.x API breaks have been fixed:

| Issue | Fix |
|-------|-----|
| `AxisAngle` type removed | Defined locally |
| `is_vector_axis_aligned` removed | Defined locally |
| `vertex.normal` read-only | Removed assignment |
| `calc_normals()` removed | Use `me.update(calc_edges=True)` |
| `bpy.ops` context dict syntax removed | Use `bpy.context.temp_override()` |
| `KeyframeInfo.dataref_loop` removed | Removed parameter |
| `create_datablock_mesh(mesh_src=)` removed | Direct `bpy.data.objects.new()` |

---

## Requirements

- **Blender 4.1**
- **X-Plane 12** (OBJ8 format)

---

## Installation

1. Download or clone this repo
2. Zip the `io_xplane2blender` folder
3. In Blender: **Edit → Preferences → Add-ons → Install from File**
4. Select the zip, enable **"Import-Export: XPlane2Blender"**
5. Restart Blender

---

## Usage

### Importing an OBJ
**File → Import → X-Plane Object (.obj)**

Select your cockpit `.obj` file. The importer will:
- Reconstruct the full animation hierarchy as Blender EMPTYs and MESHes
- Assign manipulators, show/hide animations, and datarefs
- Preserve all material and UV data

### Exporting
**File → Export → X-Plane Object (.obj)**

Same export workflow you already know.

---

## Round-Trip Notes

The exported OBJ is structurally equivalent to the original but not byte-identical:

| Change | Reason | X-Plane behavior |
|--------|--------|-----------------|
| More VTs | Blender doesn't share vertices across UV seams | Identical geometry |
| Old single-line `ANIM_rotate` → `ANIM_rotate_begin/key/end` | Modern OBJ8 format | Identical animation |
| Forward-backward pivot pattern simplified | Mesh VTs stored in pivot-local space | Identical rotation |
| Extra `ATTR_manip_none` between objects | Defensive state reset | Identical manipulators |
| A few extra `ANIM_begin` nesting levels | ob_static/ob_dynamic split | Harmless in X-Plane |

All animation directive counts (TRIS, ANIM_trans, ANIM_rotate_begin, show/hide) match exactly.

---

## License

See [LICENSE](LICENSE).
