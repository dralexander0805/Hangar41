import os
import tempfile
from pathlib import Path
from typing import List

import bpy

from io_xplane2blender.tests import *

HEADER = (
    "I\n800\nOBJ\n\n"
    "POINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
)

# LevelUp's 737: a speedbrake lever with detents and no animation at all
ROTATE_DETENT = HEADER + (
    "ATTR_manip_drag_rotate hand 0 0 0 1 0 0 0 40 0.02 0 1 0 1"
    " sim/cockpit2/controls/speedbrake_ratio none Speedbrake\n"
    "ATTR_axis_detent_range 0 0.5 0\n"
    "ATTR_axis_detent_range 0.5 1 0.02\n"
    "TRIS 0 3\n"
)

# X-Plane 11's C172 seaplane: the flap handle's drag animation has four
# keyframes, and the exporter wants two, but the OBJ line has what X-Plane uses
AXIS_DETENT = HEADER + (
    "ANIM_begin\n"
    "ANIM_trans_begin sim/cockpit2/controls/flap_ratio\n"
    "ANIM_trans_key 0 0 0 0\n"
    "ANIM_trans_key 0.333 0 -0.0149 0\n"
    "ANIM_trans_key 0.666 0 -0.0291 0\n"
    "ANIM_trans_key 1 0 -0.0503 0\n"
    "ANIM_trans_end\n"
    "ANIM_begin\n"
    "ANIM_trans 0 0 0 0.004 0 0 0 1 laminar/c172/flap_side_shift\n"
    "ATTR_manip_drag_axis hand 0 -0.0503 0 0 1 sim/cockpit2/controls/flap_ratio Flaps\n"
    "ATTR_axis_detented 0.004 0 0 0 1 laminar/c172/flap_side_shift\n"
    "ATTR_axis_detent_range 0 0.333 0\n"
    "ATTR_axis_detent_range 0.333 0.666 0.5\n"
    "ATTR_axis_detent_range 0.666 1 1\n"
    "TRIS 0 3\n"
    "ANIM_end\n"
    "ANIM_end\n"
)


def round_trip(name: str, obj: str) -> List[List[str]]:
    bpy.ops.wm.read_homefile(use_empty=True)
    root = Path(tempfile.mkdtemp())
    (root / f"{name}.obj").write_text(obj)
    bpy.ops.import_scene.xplane_obj(filepath=str(root / f"{name}.obj"))
    out = root / "out"
    assert bpy.ops.export.xplane_obj(filepath=str(out) + os.sep) == {"FINISHED"}
    return [
        line.split()
        for line in next(out.glob("*.obj")).read_text().splitlines()
        if line.split()
    ]


class TestDetentsFromImportedValues(XPlaneTestCase):
    def assertNumbers(self, tokens: List[str], want: List[float]) -> None:
        self.assertEqual(len(tokens), len(want))
        for token, number in zip(tokens, want):
            self.assertAlmostEqual(float(token), number, places=5)

    def test_rotate_detent_without_animation(self) -> None:
        lines = round_trip("rotate_detent", ROTATE_DETENT)
        (manip,) = [l for l in lines if l[0] == "ATTR_manip_drag_rotate"]
        self.assertNumbers(manip[2:15], [0, 0, 0, 1, 0, 0, 0, 40, 0.02, 0, 1, 0, 1])
        self.assertEqual(
            [[float(x) for x in l[1:]] for l in lines if l[0] == "ATTR_axis_detent_range"],
            [[0, 0.5, 0], [0.5, 1, 0.02]],
        )

    def test_axis_detent_with_many_keyframes(self) -> None:
        lines = round_trip("axis_detent", AXIS_DETENT)
        (manip,) = [l for l in lines if l[0] == "ATTR_manip_drag_axis"]
        (detented,) = [l for l in lines if l[0] == "ATTR_axis_detented"]
        self.assertNumbers(manip[2:7], [0, -0.0503, 0, 0, 1])
        self.assertEqual(manip[7], "sim/cockpit2/controls/flap_ratio")
        self.assertNumbers(detented[1:6], [0.004, 0, 0, 0, 1])
        self.assertEqual(detented[6], "laminar/c172/flap_side_shift")
        self.assertEqual(
            len([l for l in lines if l[0] == "ATTR_axis_detent_range"]), 3
        )


runTestCases([TestDetentsFromImportedValues])
