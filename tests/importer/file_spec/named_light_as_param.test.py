import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

# X-Rotors' AW139 writes a named light (airplane_beacon_sp) as a LIGHT_PARAM
OBJ = (
    "I\n800\nOBJ\n\n"
    "POINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
    "TRIS 0 3\n"
    "LIGHT_PARAM airplane_beacon_sp 0 1 0 1.00 0.00 0.00 0.00 3.00 1.00 0.00 0.00 1.00\n"
)


class TestNamedLightAsParam(XPlaneTestCase):
    def test_named_light_as_param_exports_as_is(self) -> None:
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
        self.assertEqual(len(lights), 1)
        self.assertEqual(lights[0][1], "airplane_beacon_sp")
        self.assertEqual(
            [float(x) for x in lights[0][5:]],
            [1, 0, 0, 0, 3, 1, 0, 0, 1],
        )


runTestCases([TestNamedLightAsParam])
