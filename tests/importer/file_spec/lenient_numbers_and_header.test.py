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
        # What follows the number is ignored, as with strtod
        self.assertEqual(_split_run_on_numbers(["36584,9223792524"]), ["36584"])
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

    def test_comma_decimal_in_lod(self) -> None:
        # simHeaven's Maracana: "ATTR_LOD 0 36584,9223792524"
        import_obj(
            write_obj(
                "comma_lod",
                "I\n800\nOBJ\n\n" + BODY + "ATTR_LOD 0 36584,9223792524\nTRIS 0 3\n",
            )
        )
        layer = bpy.data.collections["comma_lod"].xplane.layer
        self.assertEqual(layer.lods, "1")
        self.assertEqual((layer.lod[0].near, layer.lod[0].far), (0, 36584))

    def test_never_drawn_lod_left_out(self) -> None:
        # RescueX: "ATTR_LOD 0 0" first, which X-Plane never draws
        import_obj(
            write_obj(
                "zero_lod",
                "I\n800\nOBJ\n\n"
                + BODY
                + "ATTR_LOD 0 0\nTRIS 0 3\nATTR_LOD 0 1000\nTRIS 0 3\n",
            )
        )
        layer = bpy.data.collections["zero_lod"].xplane.layer
        self.assertEqual(layer.lods, "1")
        self.assertEqual((layer.lod[0].near, layer.lod[0].far), (0, 1000))
        self.assertEqual(len(self.meshes()), 1)

    def test_truncated_hide_left_out(self) -> None:
        # A static 747-8F writes "ANIM_hide <tab> arginal/groundtraffic/speed"
        import_obj(
            write_obj(
                "truncated_hide",
                "I\n800\nOBJ\n\n"
                + BODY
                + "ANIM_begin\nANIM_hide\t\targinal/groundtraffic/speed\nTRIS 0 3\nANIM_end\n",
            )
        )
        self.assertEqual(len(self.meshes()), 1)

    def test_light_first_without_point_counts(self) -> None:
        # simHeaven's seamarks: no POINT_COUNTS, and a light is the first line
        import_obj(
            write_obj(
                "light_first",
                "A\n800\nOBJ\n\nLIGHT_NAMED carrier_center_white 0 1 0\n",
            )
        )
        lights = [ob for ob in bpy.data.objects if ob.type == "LIGHT"]
        self.assertEqual(
            [ob.data.xplane.name for ob in lights], ["carrier_center_white"]
        )

    def test_sketchup2xplane_vertex_and_idx(self) -> None:
        # world-models' hedgerows: VERTEX for VT, several indices per IDX
        import_obj(
            write_obj(
                "sketchup",
                "I\n800\nOBJ\n\nPOINT_COUNTS 4 0 0 6\n"
                "VERTEX 0 0 0 0 1 0 0 0\nVERTEX 1 0 0 0 1 0 1 0\n"
                "VERTEX 0 0 1 0 1 0 0 1\nVERTEX 1 0 1 0 1 0 1 1\n"
                "IDX 0 1 2 1 3\nIDX 2\nTRIS 0 6\n",
            )
        )
        (mesh,) = self.meshes()
        self.assertEqual(len(mesh.data.polygons), 2)

    def test_geometry_before_first_lod_kept(self) -> None:
        # SAM's docking poles: a TRIS, then ATTR_LOD. It was dropped on export
        import_obj(
            write_obj(
                "before_lod",
                "I\n800\nOBJ\n\n" + BODY + "TRIS 0 3\nATTR_LOD 0 150\nTRIS 0 3\n",
            )
        )
        for ob in self.meshes():
            self.assertTrue(ob.xplane.override_lods)
            self.assertTrue(ob.xplane.lod[0])

    def test_header_after_point_counts(self) -> None:
        # MisterX's library: POINT_COUNTS first, then GLOBAL_specular and
        # NORMAL_METALNESS, then an IF block
        import_obj(
            write_obj(
                "late_header",
                "I\n800\nOBJ\n"
                + BODY.replace("VT 0 0 0", "GLOBAL_specular 0.25\nIF NOT SCENERY_SHADOWS\nENDIF\nVT 0 0 0", 1)
                + "TRIS 0 3\n",
            )
        )
        (mesh,) = self.meshes()
        self.assertAlmostEqual(mesh.material_slots[0].material.specular_intensity, 0.25)
        layer = bpy.data.collections["late_header"].xplane.layer
        self.assertNotIn("IF", [attr.name for attr in layer.customAttributes])

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
