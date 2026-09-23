import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

# Like the CL650's particles.obj: nothing but emitters
OBJ = (
    "A\n800\nOBJ\n\n"
    "TEXTURE\n"
    "PARTICLE_SYSTEM aircraft_particles.pss\n"
    "POINT_COUNTS 0 0 0 0\n\n"
    "EMITTER engine_fire -2.22 1.12 13.2 179 -1 0 0\n"
    "EMITTER engine_fire 2.22 1.12 13.2 181 -1 0 1\n"
    "EMITTER compr_stall_inlet -2.36 1.25 11.9 359 1 0\n"
)


class TestEmitters(XPlaneTestCase):
    def test_emitters_round_trip(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        src = root / "src"
        src.mkdir()
        (src / "particles.obj").write_text(OBJ)
        bpy.ops.import_scene.xplane_obj(filepath=str(src / "particles.obj"))

        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        lines = [
            line.split()
            for line in next(out.glob("*.obj")).read_text().splitlines()
            if line.split()
        ]
        self.assertIn(["PARTICLE_SYSTEM", "../src/aircraft_particles.pss"], lines)

        def emitter(tokens):
            name, *numbers = tokens[1:]
            # Angles may come back as an equivalent turn, e.g. 181 as -179
            x, y, z, yaw, pitch, roll, *index = map(float, numbers)
            def turn(a):
                return round(a % 360, 3) % 360

            return (name, round(x, 4), round(y, 4), round(z, 4),
                    turn(yaw), round(pitch, 3), turn(roll), index)

        self.assertEqual(
            sorted(emitter(line) for line in lines if line[0] == "EMITTER"),
            sorted([
                ("engine_fire", -2.22, 1.12, 13.2, 179, -1, 0, [0]),
                ("engine_fire", 2.22, 1.12, 13.2, 181, -1, 0, [1]),
                ("compr_stall_inlet", -2.36, 1.25, 11.9, 359, 1, 0, []),
            ]),
        )


runTestCases([TestEmitters])
