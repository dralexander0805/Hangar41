"""The starting point for the export process, the start of the addon"""
import dataclasses
import os
import os.path
import pathlib
import sys
import traceback
from typing import IO, Any, Optional

import bpy
import mathutils

import io_xplane2blender
from bpy_extras.io_utils import ExportHelper, ImportHelper
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.xplane_helpers import logger


"""
class XPLANE_MT_xplane_export_log(bpy.types.Menu):
    bl_idname = "XPLANE_MT_xplane_export_log"
    bl_label = "XPlane2Blender Export Log Warning"

    def draw(self, context):
        self.layout.row().label(text="Export produced errors or warnings.")
        self.layout.row().label(
            text="Please see the internal text file XPlane2Blender.log"
        )
"""


class XPLANE_MT_xplane_import_log(bpy.types.Menu):
    bl_idname = "XPLANE_MT_xplane_import_log"
    bl_label = "XPlane2Blender Import"

    pass


class IMPORT_OT_ImportXPlane(bpy.types.Operator, ImportHelper):
    """Import X-Plane Object file format (.obj)"""

    bl_idname = "import_scene.xplane_obj"
    bl_label = "Import X-Plane Object"

    filename_ext = ".obj"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filename used for importing an X-Plane .obj",
        maxlen=1024,
        default="",
    )

    def execute(self, context):
        filename = pathlib.Path(self.filepath).name
        log_name = f"Import for {filename}"
        logger.clear()
        logger.addTransport(logger.InternalTextTransport(log_name))
        logger.addTransport(logger.ConsoleTransport())
        try:
            xplane_imp_parser.import_obj(self.filepath)
        except xplane_imp_parser.UnrecoverableParserError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        except Exception as e:
            # A bug in the importer rather than a problem the user can fix.
            logger.error(traceback.format_exc())
            self.report(
                {"ERROR"},
                f"Importing '{filename}' failed unexpectedly ({type(e).__name__}: {e})."
                f" This is likely an importer bug; please open an issue and attach"
                f" the .obj and the '{log_name}' text from Blender's Text Editor.",
            )
            return {"CANCELLED"}

        warnings = logger.findWarnings()
        if warnings:
            self.report(
                {"WARNING"},
                f"Imported '{filename}' with {len(warnings)} warning(s),"
                f" first: {warnings[0]['message']}"
                f" (see '{log_name}' in the Text Editor for all)",
            )
        else:
            self.report({"INFO"}, f"Imported '{filename}'")
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}


_classes = (IMPORT_OT_ImportXPlane,)
register, unregister = bpy.utils.register_classes_factory(_classes)
