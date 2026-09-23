import math
import tempfile
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *

# The xPilot S76's gear: rotations on one dataref, first about a skewed axis,
# then about X. Merging the X rotation into the skewed one lost it.
OBJ = (
    "I\n800\nOBJ\n\nPOINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\nVT 1 0 0 0 1 0 1 0\nVT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
    "ANIM_begin\n"
    "ANIM_rotate 0 0.999560 -0.029666 17.89 1.99 0 1 d\n"
    "ANIM_rotate 1 0 0 -27.53 -3.16 0 1 d\n"
    "TRIS 0 3\n"
    "ANIM_end\n"
)


def x_to_b(v):
    return Vector((v[0], -v[2], v[1]))


class TestSkewedThenAlignedRotation(XPlaneTestCase):
    def test_both_rotations_kept(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        path = Path(tempfile.gettempdir()) / "skewed_then_aligned.obj"
        path.write_text(OBJ)
        import_obj(path)

        for frame, (a, b) in ((1, (17.89, -27.53)), (2, (1.99, -3.16))):
            bpy.context.scene.frame_set(frame)
            want = (
                Quaternion(Vector((0, 0.999560, -0.029666)).normalized(), math.radians(a))
                @ Quaternion(Vector((1, 0, 0)), math.radians(b))
            ).to_matrix()
            (mesh,) = [ob for ob in bpy.data.objects if ob.type == "MESH"]
            for v, xp in zip(mesh.data.vertices, ((0, 0, 0), (1, 0, 0), (0, 0, 1))):
                got = mesh.matrix_world @ v.co
                self.assertAlmostEqual((got - x_to_b(want @ Vector(xp))).length, 0, places=4)


runTestCases([TestSkewedThenAlignedRotation])
