import tempfile
from pathlib import Path

import bpy
import mathutils

from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_parser import (
    _split_run_on_numbers,
    import_obj,
)
from io_xplane2blender.tests import *

BODY = (
    "POINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
)


def write_obj(name: str, text: str) -> Path:
    path = Path(tempfile.gettempdir()) / f"{name}.obj"
    path.write_text(text)
    return path


class TestLenientNumbersAndHeader(XPlaneTestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile()
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)

    def meshes(self):
        return [ob for ob in bpy.data.objects if ob.type == "MESH"]

    def test_split_run_on_numbers(self) -> None:
        self.assertEqual(
            _split_run_on_numbers(["-0.1060-0.178", "0.978"]),
            ["-0.1060", "-0.178", "0.978"],
        )
        self.assertEqual(_split_run_on_numbers(["-90.0.0"]), ["-90.0", ".0"])
        # Valid numbers, datarefs and words are left alone
        self.assertEqual(
            _split_run_on_numbers(["1e-3", "sim/a[0]", "-", "abc"]),
            ["1e-3", "sim/a[0]", "-", "abc"],
        )

    def test_blank_lines_in_header(self) -> None:
        # Laminar's OilPlatform.obj separates I, 800 and OBJ with blank lines
        import_obj(write_obj("blank_header", "I\n\n800\n\nOBJ\n\n" + BODY + "TRIS 0 3\n"))
        self.assertEqual(len(self.meshes()), 1)

    def test_run_on_numbers_in_vt(self) -> None:
        # A shipped cockpit writes a normal as "-0.1060-0.178"
        import_obj(
            write_obj(
                "run_on_vt",
                "I\n800\nOBJ\n\n"
                + BODY.replace("VT 0 0 1 0 1 0 0 1", "VT 0 0 1 -0.1060-0.178 0.978 0 1")
                + "TRIS 0 3\n",
            )
        )
        self.assertEqual(len(self.meshes()), 1)
        self.assertEqual(len(self.meshes()[0].data.polygons), 1)

    def test_run_on_numbers_in_anim(self) -> None:
        import_obj(
            write_obj(
                "run_on_anim",
                "I\n800\nOBJ\n\n"
                + BODY
                + "ANIM_begin\n"
                "ANIM_rotate 0 0 1 0 90 0 -90.0.0 sim/some/dref\n"
                "TRIS 0 3\n"
                "ANIM_end\n",
            )
        )
        self.assertEqual(len(self.meshes()), 1)

    def test_static_anim_with_dataref_but_no_values(self) -> None:
        # AeroGenesis' A330 engines: "ANIM_trans x y z x y z none"
        import_obj(
            write_obj(
                "anim_no_values",
                "I\n800\nOBJ\n\n"
                + BODY
                + "ANIM_begin\n"
                "ANIM_trans 1 2 3 1 2 3 none\n"
                "ANIM_rotate 0 1 0 0 0 none\n"
                "TRIS 0 3\n"
                "ANIM_end\n",
            )
        )
        (mesh,) = self.meshes()
        # X-Plane (1, 2, 3) is Blender (1, -3, 2)
        centroid = sum(
            (mesh.matrix_world @ v.co for v in mesh.data.vertices), mathutils.Vector()
        ) / 3
        self.assertAlmostEqual(centroid.x, 1 + 1 / 3, places=4)
        self.assertAlmostEqual(centroid.y, -3 - 1 / 3, places=4)
        self.assertAlmostEqual(centroid.z, 2, places=4)

    def test_garbage_still_fails(self) -> None:
        with self.assertRaises(xplane_imp_parser.UnrecoverableParserError):
            import_obj(
                write_obj(
                    "garbage_vt",
                    "I\n800\nOBJ\n\n"
                    + BODY.replace("VT 1 0 0 0 1 0 1 0", "VT 1 0 zero 0 1 0 1 0"),
                )
            )


runTestCases([TestLenientNumbersAndHeader])
