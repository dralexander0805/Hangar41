import tempfile
from pathlib import Path

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *

HEADER = (
    "I\n800\nOBJ\n\nPOINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\nVT 1 0 0 0 1 0 0 0\nVT 0 0 1 0 1 0 0 0\n"
    "IDX 0\nIDX 1\nIDX 2\n"
)

# A handle that rotates 0-35 degrees, as in Laminar's Citation X
HANDLE = (
    "ANIM_begin\n"
    "ANIM_rotate 0 1 0 0 35 0 1 test/handle\n"
    "ATTR_manip_drag_rotate hand 0 0 0 0 1 0 0 35 0 0 1 0 0 test/handle none Handle\n"
)


def write_obj(name: str, body: str) -> Path:
    path = Path(tempfile.gettempdir()) / f"{name}.obj"
    path.write_text(HEADER + body)
    return path


def handle() -> bpy.types.Object:
    return next(ob for ob in bpy.data.objects if ob.type == "MESH")


class TestEmptyDetentRange(XPlaneTestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile()
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)

    def test_only_empty_ranges_stay_plain_drag_rotate(self) -> None:
        # Laminar's tools write this after plain handles; it does nothing
        import_obj(
            write_obj(
                "empty_detent_range",
                HANDLE + "ATTR_axis_detent_range 0 0 0\nTRIS 0 3\nANIM_end\n",
            )
        )
        manip = handle().xplane.manip
        self.assertEqual(manip.type, xplane_constants.MANIP_DRAG_ROTATE)
        self.assertEqual(len(manip.axis_detent_ranges), 0)

    def test_real_ranges_keep_detents(self) -> None:
        import_obj(
            write_obj(
                "real_detent_range",
                HANDLE
                + "ATTR_axis_detent_range 0 0 0\n"
                + "ATTR_axis_detent_range 0 1 1\n"
                + "TRIS 0 3\nANIM_end\n",
            )
        )
        manip = handle().xplane.manip
        self.assertEqual(manip.type, xplane_constants.MANIP_DRAG_ROTATE_DETENT)
        self.assertEqual(len(manip.axis_detent_ranges), 2)


runTestCases([TestEmptyDetentRange])
