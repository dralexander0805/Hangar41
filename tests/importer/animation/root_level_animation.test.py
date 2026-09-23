import tempfile
from pathlib import Path

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *

# Two triangles, so there's geometry before and inside a nested block
HEADER = (
    "I\n800\nOBJ\n\nPOINT_COUNTS 6 0 0 6\n"
    + "".join(
        f"VT {x} 0 {z} 0 1 0 0 0\n"
        for x, z in [(0, 0), (1, 0), (0, 1), (2, 0), (3, 0), (2, 1)]
    )
    + "IDX10 0 1 2 3 4 5 0 0 0 0\n"
)


def write_obj(name: str, body: str) -> Path:
    path = Path(tempfile.gettempdir()) / f"{name}.obj"
    path.write_text(HEADER + body)
    return path


def ancestors(ob: bpy.types.Object):
    while ob.parent:
        ob = ob.parent
        yield ob


class TestRootLevelAnimation(XPlaneTestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile()
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)

    def test_root_level_hide_covers_rest_of_file(self) -> None:
        # Laminar's Citation X hides its wings like this, with no ANIM_begin
        import_obj(
            write_obj(
                "root_level_hide",
                "ANIM_hide 6 6 sim/operation/failures/rel_wing1L\n"
                "TRIS 0 3\n"
                "ANIM_begin\n"
                "ANIM_rotate 0 1 0 0 90 0 1 some/dref\n"
                "TRIS 3 3\n"
                "ANIM_end\n",
            )
        )
        hide = [
            ob
            for ob in bpy.data.objects
            if any(
                d.path == "sim/operation/failures/rel_wing1L"
                and d.anim_type == xplane_constants.ANIM_TYPE_HIDE
                for d in ob.xplane.datarefs
            )
        ]
        self.assertEqual(len(hide), 1)
        meshes = [ob for ob in bpy.data.objects if ob.type == "MESH"]
        self.assertEqual(len(meshes), 2)
        for mesh in meshes:
            self.assertTrue(
                mesh == hide[0] or hide[0] in ancestors(mesh),
                f"{mesh.name} should be hidden with the wing",
            )

    def test_stray_anim_end_is_ignored(self) -> None:
        import_obj(write_obj("stray_anim_end", "TRIS 0 3\nANIM_end\nTRIS 3 3\n"))
        self.assertEqual(
            len([ob for ob in bpy.data.objects if ob.type == "MESH"]), 2
        )


runTestCases([TestRootLevelAnimation])
