# Hangar41

![Beta](https://img.shields.io/badge/status-beta-orange)
![Blender](https://img.shields.io/badge/Blender-4.1-blue?logo=blender)
![X-Plane](https://img.shields.io/badge/X--Plane-12-darkblue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

**Import an existing X-Plane `.obj` into Blender 4.1, edit it, and export it back to a working object — a full round-trip.**

A few importers for X-Plane objects already exist, but in practice they've been partial or unreliable — they can pull geometry and some keyframes into Blender, but the result doesn't cleanly re-export. The hard part has always been that other direction: getting an imported object back *out* in a state that works in sim. That's what Hangar41 is built around — a full round-trip, with meshes, animations, and manipulators surviving the trip in and back out again.

> ⚠️ **Beta** — core functionality is solid in testing, but this hasn't been validated against every kind of OBJ out there. If something comes out wrong, please open an issue and attach the OBJ.

---

## Demo

Import → edit → re-export, working in sim:

![Round-trip demo](docs/round-trip.gif)

Detent manipulators surviving the round-trip (flap handle):

![Detent manipulator demo](docs/detent-manip.gif)


---

## Features

- **OBJ Importer** — bring any X-Plane `.obj` directly into Blender, textured in the viewport
- **Round-trip export** — re-export an imported object back to a working `.obj`
- **Animations** — translations, rotations, show/hide, keyframe loops, including deeply nested pivots
- **Manipulators** — including detent manips (flap handles, speedbrakes, gear levers)
- **Lights and magnets** — named, param and custom billboard lights; EFB/flashlight magnets
- **Attributes** — light levels, panel regions, blending, shadows, hard surfaces, LODs, normals
- Blender 4.1 compatible

Tested by importing, exporting and re-importing 28 cockpit and cabin objects from X-Plane 12
and X-Plane 11 aircraft by many different authors. Every part lands where X-Plane puts it at
several animation positions, and manipulators, lights and datarefs survive the trip.

---

## Known limitations

This is a beta. Expect rough edges with objects authored in unusual ways by other tools or older exporters.

After an import, the Info bar (and the *Import for …* text in Blender's Text Editor) lists anything that wasn't imported and so will be missing from an export. Currently that is:

- `LIGHT_SPILL_CUSTOM` and old-style `LIGHTS` vertex lights
- `EMITTER` (particle emitters)
- Pre-X-Plane 10 attributes: `ATTR_cull`/`ATTR_no_cull`, `ATTR_diffuse_rgb`, `ATTR_emission_rgb`
- Detent ranges on a drag manipulator whose `ATTR_axis_detented` has a zero axis (the manipulator itself is kept)

A few things are written differently but mean the same to X-Plane: the file header's `GLOBAL_specular` becomes per-material `ATTR_shiny_rat`, static `ANIM_rotate`/`ANIM_trans` are baked into the geometry, and state on invisible click zones (`ATTR_draw_disable`) that can't affect drawing is left out.

Exporting may warn that some light names are unknown: the bundled `lights.txt` predates X-Plane 12. The lights are still written exactly as they were imported.

Bug reports with the offending `.obj` attached are the most useful thing you can contribute right now.

---

## Requirements

- Blender 4.1
- X-Plane 12

---

## Installation

1. If you have **XPlane2Blender** installed, disable it first. Hangar41 is built on it and uses the same add-on folder name and settings, so only one can be enabled.
2. Download or clone this repo
3. Zip the `io_xplane2blender` folder
4. In Blender: **Edit → Preferences → Add-ons → Install from File**
5. Select the zip, then enable **"Import-Export: Hangar41: X-Plane .obj Import/Export"**
6. Restart Blender

---

## Usage

### Import

**File → Import → X-Plane Object (.obj)**

### Export

An import fills these in from the `.obj` (export type, textures, cockpit regions, LODs), so a straight round-trip needs no setup:

1. Open the **Scene Properties** panel
2. Scroll to the **X-Plane** section
3. Check your X-Plane version, collection type, and texture paths
4. Click **Export OBJs**

X-Plane needs texture paths relative to the `.obj`, so export to a folder on the same drive as the textures.

---

## Credits

Hangar41 builds on the work of people who tackled X-Plane OBJ import before it:

- [**XPlane2Blender**](https://github.com/X-Plane/XPlane2Blender) — Laminar Research's official exporter, and the foundation this add-on extends. Laminar's experimental importer (4.2 alpha) and Ted Greene's writing on why round-trip import is hard shaped the approach here.

If I've missed a project that belongs here, open an issue and I'll add it.

---

## License

[GPL-3.0](LICENSE)
