import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

# The Metro III leaves ATTR_light_level on over its panel parts
OBJ = (
    "I\n800\nOBJ\n\n"
    "TEXTURE tex.png\n"
    "POINT_COUNTS 6 0 0 6\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "VT 2 0 0 0 1 0 0 0\n"
    "VT 3 0 0 0 1 0 1 0\n"
    "VT 2 0 1 0 1 0 0 1\n"
    "IDX10 0 1 2 3 4 5 0 0 0 0\n"
    "ATTR_light_level 0 1 sim/cockpit2/electrical/instrument_brightness_ratio[31]\n"
    "TRIS 0 3\n"
    "ATTR_cockpit\n"
    "TRIS 3 3\n"
)


class TestPanelLightLevel(XPlaneTestCase):
    def test_panel_with_light_level_exports(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        (root / "tex.png").write_bytes(b"")
        (root / "a.obj").write_text(OBJ)
        bpy.ops.import_scene.xplane_obj(filepath=str(root / "a.obj"))
        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        body = [line.split()[0] for line in next(out.glob("*.obj")).read_text().splitlines() if line.split()]
        # The panel's TRIS still has both states on
        panel_tris = max(i for i, d in enumerate(body) if d == "TRIS")
        before = body[:panel_tris]
        self.assertIn("ATTR_cockpit", before)
        self.assertIn("ATTR_light_level", before)
        self.assertNotIn(
            "ATTR_light_level_reset",
            body[before.index("ATTR_light_level") : panel_tris],
        )


runTestCases([TestPanelLightLevel])
