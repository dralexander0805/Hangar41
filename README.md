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

- **OBJ Importer** — bring any X-Plane `.obj` directly into Blender
- **Round-trip export** — re-export an imported object back to a working `.obj`
- **Animations** — translations, rotations, show/hide
- **Manipulators** — including detent manips (flap handles, speedbrakes, gear levers)
- Blender 4.1 compatible

---

## Known limitations

This is a beta and has been tested mainly against my own library, which isn't representative of everything people have built. Expect rough edges in:

- Deeply nested or stacked animations
- Less common manipulator types beyond those listed above
- Objects authored in unusual ways by other tools or older exporters

Bug reports with the offending `.obj` attached are the most useful thing you can contribute right now.

---

## Requirements

- Blender 4.1
- X-Plane 12

---

## Installation

1. Download or clone this repo
2. Zip the `io_xplane2blender` folder
3. In Blender: **Edit → Preferences → Add-ons → Install from File**
4. Select the zip, then enable **"Import-Export: XPlane2Blender"**
5. Restart Blender

---

## Usage

### Import

**File → Import → X-Plane Object (.obj)**

### Export

1. Open the **Scene Properties** panel
2. Scroll to the **X-Plane** section
3. Set your X-Plane version, collection type, and texture paths
4. Click **Export OBJs**

---

## Credits

Hangar41 builds on the work of people who tackled X-Plane OBJ import before it:

- [**XPlane2Blender**](https://github.com/X-Plane/XPlane2Blender) — Laminar Research's official exporter, and the foundation this add-on extends. Laminar's experimental importer (4.2 alpha) and Ted Greene's writing on why round-trip import is hard shaped the approach here.

If I've missed a project that belongs here, open an issue and I'll add it.

---

## License

[GPL-3.0](LICENSE)
