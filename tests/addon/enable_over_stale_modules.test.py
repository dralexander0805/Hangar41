import sys

import addon_utils

from io_xplane2blender.tests import *


class TestEnableOverStaleModules(XPlaneTestCase):
    def test_enable_after_a_failed_older_copy(self) -> None:
        # XPlane2Blender shares the module name and fails part way through
        # enabling on Blender 4, leaving some of its submodules behind.
        # Enabling Hangar41 after that failed with "partially initialized
        # module 'io_xplane2blender' has no attribute 'xplane_props'"
        addon_utils.disable("io_xplane2blender", default_set=True)
        for name in list(sys.modules):
            if name == "io_xplane2blender" or name.startswith(
                ("io_xplane2blender.tests", "io_xplane2blender.importer",
                 "io_xplane2blender.xplane_ops", "io_xplane2blender.xplane_ui")
            ):
                del sys.modules[name]
        self.assertIn("io_xplane2blender.xplane_props", sys.modules)

        errors = []
        module = addon_utils.enable(
            "io_xplane2blender", default_set=True, handle_error=errors.append
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(module)


runTestCases([TestEnableOverStaleModules])
