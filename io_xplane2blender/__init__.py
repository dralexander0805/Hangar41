# File: __init__.py
# Needed for python to register this folder as a module and for blender to register/unregister the addon.

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Variable: bl_info
# Contains informations for Blender to recognize and categorize the addon.
bl_info = {
    "name": "Hangar41: X-Plane .obj Import/Export",
    "description": "Import X-Plane objects (.obj), edit them, and export them back",
    "author": "Ted Greene, Ben Supnik, Hangar41 contributors",
    "version": (4, 2, 0),
    "blender": (4, 1, 0),
    "location": "File > Import/Export > X-Plane Object (.obj)",
    "warning": "Beta. Replaces XPlane2Blender; disable that add-on first",
    "doc_url": "https://github.com/dralexander0805/Hangar41",
    "tracker_url": "https://github.com/dralexander0805/Hangar41/issues",
    "category": "Import-Export",
}

if "bpy" in locals():
    # imp was removed in Python 3.12 (Blender 4.2+)
    import importlib

    importlib.reload(xplane_ui)
    importlib.reload(xplane_props)
    importlib.reload(xplane_import)
    importlib.reload(xplane_export)
    importlib.reload(xplane_ops)
    importlib.reload(xplane_ops_dev)
    importlib.reload(xplane_config)
    importlib.reload(xplane_updater)
    importlib.reload(xplane_avitab_atlas)
    importlib.reload(xplane_avitab_tablet)
    importlib.reload(xplane_avitab)
else:
    import sys

    # This package is being imported fresh, so any of its submodules Python
    # still has come from an earlier copy: XPlane2Blender, which shares this
    # module name and fails part way on Blender 4, or a Hangar41 this one
    # replaced. Reusing them breaks enabling with "partially initialized
    # module 'io_xplane2blender' has no attribute 'xplane_props'".
    for _stale in [name for name in sys.modules if name.startswith(__name__ + ".")]:
        del sys.modules[_stale]

    import bpy
    from . import xplane_ui
    from . import xplane_props
    from . import xplane_import
    from . import xplane_export
    from . import xplane_ops
    from . import xplane_ops_dev
    from . import xplane_config
    from . import xplane_updater
    from . import xplane_avitab_atlas
    from . import xplane_avitab_tablet
    from . import xplane_avitab


# Function: menu_func
# Adds the export option to the menu.
#
# Parameters:
#   self - Instance to something
#   context - The Blender context object
def menu_func_export(self, context):
    self.layout.operator(
        xplane_export.EXPORT_OT_ExportXPlane.bl_idname, text="X-Plane Object (.obj)"
    )


def menu_func_import(self, context):
    self.layout.operator(
        xplane_import.IMPORT_OT_ImportXPlane.bl_idname, text="X-Plane Object (.obj)"
    )


# Function: register
# Registers the addon with all its classes and the menu function.
def register():
    xplane_export.register()
    xplane_import.register()
    xplane_props.register()
    xplane_ops.register()
    xplane_ops_dev.register()
    xplane_ui.register()
    xplane_avitab.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


# Function: unregister
# Unregisters the addon and all its classes and removes the entry from the menu.
def unregister():
    xplane_avitab.unregister()
    xplane_export.unregister()
    xplane_import.unregister()
    xplane_ui.unregister()
    xplane_ops.unregister()
    xplane_ops_dev.unregister()
    xplane_props.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
