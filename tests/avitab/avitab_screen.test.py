import json
import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

COCKPIT = (
    "I\n800\nOBJ\n\nGLOBAL_cockpit_lit\nPOINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\nVT 1 0 0 0 1 0 1 0\nVT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\nTRIS 0 3\n"
)


class TestAviTabScreen(XPlaneTestCase):
    def test_screen_exports_and_json_matches(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        (root / "cockpit.obj").write_text(COCKPIT)
        bpy.ops.import_scene.xplane_obj(filepath=str(root / "cockpit.obj"))

        # Add into the imported cockpit's collection
        coll = bpy.data.collections["cockpit"]
        layer_coll = bpy.context.view_layer.layer_collection.children[coll.name]
        bpy.context.view_layer.active_layer_collection = layer_coll
        bpy.context.scene.cursor.location = (0.3, 0.1, 0.9)
        self.assertEqual(
            bpy.ops.object.add_xplane_avitab_screen(
                panel_width=4096, panel_height=2048,
                left=1150, bottom=1508, width=885, height=495,
                screen_width=0.24, hide_when_disabled=True,
            ),
            {"FINISHED"},
        )
        screen = bpy.context.active_object
        self.assertIn(screen.name, coll.objects)

        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        lines = [l.split() for l in (out / "cockpit.obj").read_text().splitlines() if l.split()]
        directives = [l[0] for l in lines]
        self.assertIn("ATTR_cockpit", directives)
        self.assertIn(["ATTR_light_level", "0", "1", "avitab/brightness"], lines)
        self.assertIn(["ANIM_hide", "0", "0", "avitab/panel_enabled"], lines)

        # The screen's four corners map exactly onto AviTab's rectangle
        uvs = {(round(float(l[7]), 5), round(float(l[8]), 5)) for l in lines if l[0] == "VT"}
        for uv in ((1150 / 4096, 1508 / 2048), (2035 / 4096, 2003 / 2048)):
            self.assertIn(tuple(round(c, 5) for c in uv), uvs)

        # Not stretched: width over height is the rectangle's
        xs = [v.co.x for v in screen.data.vertices]
        zs = [v.co.z for v in screen.data.vertices]
        self.assertAlmostEqual(max(xs) - min(xs), 0.24, places=5)
        self.assertAlmostEqual((max(xs) - min(xs)) / (max(zs) - min(zs)), 885 / 495, places=4)

        # The tablet: its own .obj, the screen plus the bezel, behind the screen
        self.assertEqual(sorted(p.name for p in out.glob("*.obj")), ["avitab_tablet.obj", "cockpit.obj"])
        tablet_lines = [l.split() for l in (out / "avitab_tablet.obj").read_text().splitlines() if l.split()]
        self.assertIn(["ANIM_hide", "0", "0", "avitab/panel_enabled"], tablet_lines)
        tablet = bpy.data.objects["AviTab Tablet"]
        txs = [v.co.x for v in tablet.data.vertices]
        tys = [v.co.y for v in tablet.data.vertices]
        self.assertAlmostEqual(max(txs) - min(txs), 0.24 + 2 * 0.012, places=5)
        self.assertGreater(min(tys), 0)  # behind the screen, which faces -Y
        self.assertEqual(tablet.matrix_world, screen.matrix_world)
        # Its glass faces the pilot, and its back faces away
        big = sorted(tablet.data.polygons, key=lambda p: p.area)[-2:]
        self.assertEqual(sorted(round(p.normal.y) for p in big), [-1, 1])
        # The body is closed: no gaps round the grilles or anywhere else
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(tablet.data)
        bm.faces.ensure_lookup_table()
        body, todo = set(), [max(bm.faces, key=lambda f: f.calc_area())]
        while todo:
            face = todo.pop()
            if face not in body:
                body.add(face)
                todo += [f for e in face.edges for f in e.link_faces]
        open_edges = [e for f in body for e in f.edges if len(e.link_faces) != 2]
        self.assertEqual(open_edges, [])
        bm.free()

        # Textured like the add-on's; its textures, bundled, go next to its .obj
        self.assertIn(["TEXTURE", "avitab_tablet_space_grey.png"], tablet_lines)
        self.assertIn(["TEXTURE_NORMAL", "avitab_tablet_NML.png"], tablet_lines)
        self.assertIn(["NORMAL_METALNESS"], tablet_lines)
        for name in ("avitab_tablet_space_grey.png", "avitab_tablet_NML.png"):
            self.assertTrue((out / name).is_file())

        # AviTab.json
        self.assertEqual(
            bpy.ops.export.xplane_avitab_json(filepath=str(root / "AviTab.json"), hide_header=True),
            {"FINISHED"},
        )
        self.assertEqual(
            json.loads((root / "AviTab.json").read_text()),
            {"panel": {"left": 1150, "bottom": 1508, "width": 885, "height": 495,
                       "enabled": True, "hide_header": True}},
        )


    def test_two_tablets_export_separately(self) -> None:
        # Pilot and copilot tablets mirroring the same AviTab
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        (root / "cockpit.obj").write_text(COCKPIT)
        bpy.ops.import_scene.xplane_obj(filepath=str(root / "cockpit.obj"))
        layer_coll = bpy.context.view_layer.layer_collection.children["cockpit"]
        for x in (-0.3, 0.3):
            bpy.context.view_layer.active_layer_collection = layer_coll
            bpy.context.scene.cursor.location = (x, 0.1, 0.9)
            self.assertEqual(bpy.ops.object.add_xplane_avitab_screen(), {"FINISHED"})

        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        self.assertEqual(
            sorted(p.name for p in out.glob("*.obj")),
            ["avitab_tablet.obj", "avitab_tablet_2.obj", "cockpit.obj"],
        )
        cockpit = (out / "cockpit.obj").read_text()
        # Written once: the second screen needs the state the first set
        self.assertEqual(cockpit.count("avitab/brightness"), 1)


    def test_panel_size_found_and_screens_refit(self) -> None:
        # The C172's panel is 1024 x 1024; screens made for 2048 showed a quarter
        bpy.ops.wm.read_homefile(use_empty=True)
        aircraft = Path(tempfile.mkdtemp())
        (aircraft / "objects").mkdir()
        (aircraft / "objects" / "cockpit.png").write_bytes(b"")
        panels = aircraft / "cockpit_3d" / "-PANELS-"
        panels.mkdir(parents=True)
        # PNG signature and IHDR: width, height
        (panels / "Panel.png").write_bytes(
            b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (1024).to_bytes(4, "big") * 2
        )
        (aircraft / "objects" / "cockpit.obj").write_text(
            COCKPIT.replace("GLOBAL_cockpit_lit\n", "GLOBAL_cockpit_lit\nTEXTURE cockpit.png\n")
        )
        bpy.ops.import_scene.xplane_obj(filepath=str(aircraft / "objects" / "cockpit.obj"))
        layer_coll = bpy.context.view_layer.layer_collection.children["cockpit"]
        bpy.context.view_layer.active_layer_collection = layer_coll

        from io_xplane2blender.xplane_avitab import find_panel_size

        self.assertEqual(find_panel_size()[0], (1024, 1024))
        # Without a size given, it uses the one it finds
        self.assertEqual(bpy.ops.object.add_xplane_avitab_screen(), {"FINISHED"})
        found = bpy.context.active_object
        self.assertAlmostEqual(max(l.uv.x for l in found.data.uv_layers.active.data), 800 / 1024)
        # The tablet's textures go with the cockpit's, where its .obj will be
        self.assertTrue((aircraft / "objects" / "avitab_tablet_NML.png").is_file())
        self.assertEqual(
            Path(bpy.data.collections["AviTab Tablet"].xplane.layer.texture),
            aircraft / "objects" / "avitab_tablet_space_grey.png",
        )

        # A screen made for 2048, duplicated and joined, and joined with a
        # face that isn't a screen: Refit fixes only the screen faces
        self.assertEqual(
            bpy.ops.object.add_xplane_avitab_screen(panel_width=2048, panel_height=2048, add_tablet=False),
            {"FINISHED"},
        )
        screen = bpy.context.active_object
        bpy.ops.object.duplicate()
        copy = bpy.context.active_object
        copy.location.x += 0.5
        other = bpy.data.objects.new("other", bpy.data.meshes["Mesh"].copy())
        layer_coll.collection.objects.link(other)
        other_uvs = [tuple(l.uv) for l in other.data.uv_layers.active.data]
        for ob in bpy.context.scene.objects:
            ob.select_set(ob in (screen, copy, other))
        bpy.context.view_layer.objects.active = screen
        bpy.ops.object.join()

        self.assertEqual(
            bpy.ops.object.xplane_avitab_refit(panel_width=1024, panel_height=1024), {"FINISHED"}
        )
        uv = screen.data.uv_layers.active.data
        screen_uvs, rest = [], []
        for poly in screen.data.polygons:
            is_screen = screen.material_slots[poly.material_index].material.xplane.cockpit_feature == "panel"
            (screen_uvs if is_screen else rest).extend(tuple(uv[i].uv) for i in poly.loop_indices)
        self.assertEqual(len(screen_uvs), 8)  # both copies
        self.assertAlmostEqual(max(u for u, v in screen_uvs), 800 / 1024, places=5)
        self.assertAlmostEqual(max(v for u, v in screen_uvs), 480 / 1024, places=5)
        for got, want in zip(sorted(rest), sorted(other_uvs)):
            self.assertAlmostEqual(got[0], want[0], places=5)
            self.assertAlmostEqual(got[1], want[1], places=5)
        # Running it again changes nothing
        bpy.ops.object.xplane_avitab_refit(panel_width=1024, panel_height=1024)
        self.assertAlmostEqual(max(l.uv.x for l in screen.data.uv_layers.active.data if l.uv.x < 0.9), 800 / 1024, places=5)


runTestCases([TestAviTabScreen])
