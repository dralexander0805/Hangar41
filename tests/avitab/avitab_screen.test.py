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


runTestCases([TestAviTabScreen])
