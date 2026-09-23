import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

# Param lights as shipped aircraft and scenery write them
OBJ = (
    "I\n800\nOBJ\n\n"
    "POINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
    "TRIS 0 3\n"
    "LIGHT_PARAM airplane_beacon_sp 0 1 0 1.00 0.00 0.00 0.00 3.00 1.00 0.00 0.00 1.00\n"
    # Laminar's BulkCarrier ship writes a SIZE with a unit; X-Plane reads 2850
    "LIGHT_PARAM spot_params_sp 0 2 0 1.00 0.90 0.80 1.00 2850cd 0.00 -0.50 0.87 0.50\n"
    # Laminar's 747 gives a directional light no direction
    "LIGHT_PARAM airplane_generic_core 0 3 0 0 0 0 2 0.4\n"
    # X-Crafts' librain objects name a param light
    "LIGHT_NAMED airplane_generic_sp 0 4 0\n"
    # X-Crafts' ERJ gives fewer params than the bundled lights.txt wants
    "LIGHT_PARAM airplane_nav_tail_size 0 5 0 0.60\n"
)


class TestNamedLightAsParam(XPlaneTestCase):
    def test_odd_param_lights_export_as_is(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        (root / "a.obj").write_text(OBJ)
        bpy.ops.import_scene.xplane_obj(filepath=str(root / "a.obj"))
        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        lines = [
            line.split()
            for line in next(out.glob("*.obj")).read_text().splitlines()
            if line.split()
        ]
        lights = {line[1]: line[5:] for line in lines if line[0] == "LIGHT_PARAM"}
        self.assertEqual(
            sorted(lights),
            [
                "airplane_beacon_sp",
                "airplane_generic_core",
                "airplane_nav_tail_size",
                "spot_params_sp",
            ],
        )
        self.assertEqual(
            [float(x) for x in lights["airplane_beacon_sp"]],
            [1, 0, 0, 0, 3, 1, 0, 0, 1],
        )
        # Written as imported
        self.assertEqual(lights["spot_params_sp"][4], "2850cd")
        self.assertEqual(lights["airplane_generic_core"], ["0", "0", "0", "2", "0.4"])
        self.assertEqual(lights["airplane_nav_tail_size"], ["0.60"])
        self.assertIn(
            ["LIGHT_NAMED", "airplane_generic_sp"],
            [line[:2] for line in lines if line[0] == "LIGHT_NAMED"],
        )


runTestCases([TestNamedLightAsParam])
