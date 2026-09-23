import math
import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

OBJ = (
    "I\n800\nOBJ\n\nPOINT_COUNTS 0 0 0 0\n"
    # CL650: a spot pointing down, on a dataref
    "LIGHT_SPILL_CUSTOM 1 2 3 1 0.9 0.8 1 0.5 0 -1 0 0.6755902 CL650/lamps/integ/P3LM\n"
    # NAPS terminals: a spot with A 0.4, pointing forward and down
    "LIGHT_SPILL_CUSTOM 4 5 6 1 0.85 0.3 0.4 30 0.0 -0.985 -0.174 0.707 none\n"
    # Laminar's 737: omni, A 0
    "LIGHT_SPILL_CUSTOM 7 8 9 1 1 1 0 2 0 0 0 1 laminar/B738/cabin_lights_spill\n"
)


class TestSpillCustomLights(XPlaneTestCase):
    def test_spill_custom_round_trip(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        (root / "a.obj").write_text(OBJ)
        bpy.ops.import_scene.xplane_obj(filepath=str(root / "a.obj"))
        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        got = sorted(
            line.split()[1:]
            for line in next(out.glob("*.obj")).read_text().splitlines()
            if line.split()[:1] == ["LIGHT_SPILL_CUSTOM"]
        )
        want = sorted(line.split()[1:] for line in OBJ.splitlines() if "SPILL" in line)
        self.assertEqual(len(got), 3)
        for g, w in zip(got, want):
            self.assertEqual(g[-1], w[-1])
            for a, b in zip(g[:-1], w[:-1]):
                # Directions come back normalized from the spot's rotation
                self.assertAlmostEqual(float(a), float(b), places=3)


runTestCases([TestSpillCustomLights])
