import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

# X-Plane 11's Baron and King Air: trim wheels are drag_rotate click zones with
# no rotation animation. X-Plane needs none; the line has center, axis, angles.
OBJ = (
    "I\n800\nOBJ\n\n"
    "POINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
    "ANIM_begin\n"
    "ANIM_trans 1 2 3 1 2 3 0 0 none\n"
    "ATTR_manip_drag_rotate hand 0.5 0 0 -1 0 0 0 640 0 1 -1 0 0"
    " sim/cockpit2/controls/elevator_trim none Elevator Trim\n"
    "TRIS 0 3\n"
    "ANIM_end\n"
)


class TestDragRotateWithoutAnimation(XPlaneTestCase):
    def test_exports_from_imported_values(self) -> None:
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
        (manip,) = [line for line in lines if line[0] == "ATTR_manip_drag_rotate"]
        first_vt = next(line for line in lines if line[0] == "VT")

        # Wherever the static ANIM_trans ends up, the center keeps its place
        # relative to the geometry (VT 0 0 0 was 0.5 from it along x)
        origin = [float(x) for x in manip[2:5]]
        vertex = [float(x) for x in first_vt[1:4]]
        for o, v, want in zip(origin, vertex, (0.5, 0, 0)):
            self.assertAlmostEqual(o - v, want, places=4)
        self.assertEqual([float(x) for x in manip[5:8]], [-1, 0, 0])
        self.assertEqual(
            [float(x) for x in manip[8:15]], [0, 640, 0, 1, -1, 0, 0]
        )
        self.assertEqual(manip[15:], ["sim/cockpit2/controls/elevator_trim", "none", "Elevator", "Trim"])


runTestCases([TestDragRotateWithoutAnimation])
