# Hangar41

![Beta](https://img.shields.io/badge/status-beta-orange)
![Blender](https://img.shields.io/badge/Blender-4.1-blue?logo=blender)
![X-Plane](https://img.shields.io/badge/X--Plane-12-darkblue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

**Import any X-Plane cockpit into Blender 4.1, edit it, and export it back — fully working round-trip.**

Until now there was no way to bring an existing X-Plane `.obj` file back into Blender for editing. You had to keep the original `.blend` or start from scratch. Hangar41 changes that.

> ⚠️ **Beta** — core functionality is solid but edge cases may exist. Open an issue if you find one.

---

## Features

- **OBJ Importer** — bring any X-Plane `.obj` directly into Blender
- Full animation support — translations, rotations, show/hide, manipulators
- Detent manipulators work correctly (flap handles, speedbrakes, gear levers)
- Blender 4.1 compatible

---

## Requirements

- Blender 4.1
- X-Plane 12

---

## Installation

1. Download or clone this repo
2. Zip the `io_xplane2blender` folder
3. In Blender: **Edit → Preferences → Add-ons → Install from File**
4. Select the zip, enable **"Import-Export: XPlane2Blender"**
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

## License

[GPL-3.0](LICENSE)
