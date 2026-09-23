import os
import tempfile
from pathlib import Path

import bpy

from io_xplane2blender.tests import *

OBJ = (
    "I\n800\nOBJ\n\n"
    "TEXTURE tex.png\n"
    "POINT_COUNTS 3 0 0 3\n"
    "VT 0 0 0 0 1 0 0 0\n"
    "VT 1 0 0 0 1 0 1 0\n"
    "VT 0 0 1 0 1 0 0 1\n"
    "IDX 0\nIDX 1\nIDX 2\n"
    "TRIS 0 3\n"
)


class TestExportElsewhereTexturePaths(XPlaneTestCase):
    def test_texture_path_relative_to_chosen_folder(self) -> None:
        # File > Export to a folder that isn't next to the .blend (here the
        # .blend isn't saved at all) must still write working texture paths
        bpy.ops.wm.read_homefile(use_empty=True)
        root = Path(tempfile.mkdtemp())
        src = root / "src"
        out = root / "out" / "deeper"
        src.mkdir()
        (src / "tex.png").write_bytes(b"")
        (src / "a.obj").write_text(OBJ)

        bpy.ops.import_scene.xplane_obj(filepath=str(src / "a.obj"))
        self.assertEqual(
            bpy.ops.export.xplane_obj(filepath=str(out) + os.sep), {"FINISHED"}
        )

        exported = next(out.glob("*.obj")).read_text()
        texture = next(
            line.split(None, 1)[1].strip()
            for line in exported.splitlines()
            if line.split()[:1] == ["TEXTURE"]
        )
        self.assertEqual(texture, "../../src/tex.png")
        self.assertTrue((out / texture).exists())


runTestCases([TestExportElsewhereTexturePaths])
