# XPlane2Blender — with Round-Trip OBJ Importer

A fork of the official [XPlane2Blender](https://github.com/X-Plane/XPlane2Blender) addon, updated for **Blender 4.1** and extended with a fully working **OBJ importer** for round-trip cockpit editing.

> **The original addon has no import feature.** This fork adds one — import any X-Plane cockpit `.obj` file directly into Blender, edit it, and export it back. Tested on real-world aircraft including the B737 and B747 cockpits.

---

## What's New in This Fork

### OBJ Importer
- Import X-Plane `.obj` files directly into Blender 4.1
- All animations preserved: `ANIM_trans`, `ANIM_rotate`, show/hide
- `drag_rotate` manipulators with detent ranges (flap handles, speedbrakes, etc.)
- Full round-trip: import → edit → export → identical behavior in X-Plane

### Exporter Bug Fixes
- **`drag_rotate` v2_max wrong**: Exporter was using the physical lift distance as `v2_max` instead of the dataref's actual maximum value. Caused flap handles and speedbrakes to be non-functional after round-trip.
- **Detent range validator too strict**: Four validator checks blocked export of valid Plane Maker–generated OBJs. Downgraded from errors to warnings.

### Blender 4.1 Compatibility
All Blender 4.x API breaks from the original 4.2.0-alpha codebase have been fixed:

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

Standard XPlane2Blender export — unchanged from the original workflow.

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

## Upstream

This is a fork of [X-Plane/XPlane2Blender](https://github.com/X-Plane/XPlane2Blender) at version 4.2.0-alpha.1. The original addon is maintained by Laminar Research. Bug fixes in this fork that apply to the original have been submitted upstream as PRs.

Original license: see [LICENSE](LICENSE).
