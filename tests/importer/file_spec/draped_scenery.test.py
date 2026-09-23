import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.tests import *

# Like airport markings: draped geometry with its own draped texture
OBJ = (
    "I\n800\nOBJ\n\n"
    "TEXTURE tex.png\n"
    "TEXTURE_DRAPED lines.png\n"
    "POINT_COUNTS 6 0 0 6\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "VT 2 0 0 0 1 0 0 0\n"
    "VT 3 0 0 0 1 0 1 0\n"
    "VT 2 0 1 0 1 0 0 1\n"
    "IDX10 0 1 2 3 4 5 0 0 0 0\n"
    "TRIS 0 3\n"
    "ATTR_draped\n"
    "TRIS 3 3\n"
)


class TestDrapedScenery(XPlaneTestCase):
    def test_draped_imports_as_scenery_and_exports(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        src = root / "src"
        src.mkdir()
        for name in ("tex.png", "lines.png"):
            (src / name).write_bytes(b"")
        (src / "a.obj").write_text(OBJ)
        bpy.ops.import_scene.xplane_obj(filepath=str(src / "a.obj"))

        layer = bpy.data.collections["a"].xplane.layer
        self.assertEqual(layer.export_type, xplane_constants.EXPORT_TYPE_SCENERY)

        out = root / "out"
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )
        lines = [
            line.split()
            for line in next(out.glob("*.obj")).read_text().splitlines()
            if line.split()
        ]
        draped_tex = [line for line in lines if line[0] == "TEXTURE_DRAPED"]
        self.assertEqual(draped_tex, [["TEXTURE_DRAPED", "../src/lines.png"]])
        self.assertIn(["ATTR_draped"], lines)


runTestCases([TestDrapedScenery])
