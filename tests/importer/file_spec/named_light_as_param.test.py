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
        lights = [
            line.split()
            for line in next(out.glob("*.obj")).read_text().splitlines()
            if line.strip().startswith("LIGHT_PARAM")
        ]
        self.assertEqual(
            [light[1] for light in lights], ["airplane_beacon_sp", "spot_params_sp"]
        )
        self.assertEqual(
            [float(x) for x in lights[0][5:]],
            [1, 0, 0, 0, 3, 1, 0, 0, 1],
        )
        # Written as imported
        self.assertEqual(lights[1][9], "2850cd")


runTestCases([TestNamedLightAsParam])
