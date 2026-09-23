"""
AviTab screens for 3D cockpits. AviTab draws into a rectangle of the panel
texture, given in AviTab.json next to the .acf. A screen is a quad in the
cockpit OBJ that's part of the panel and UV-mapped onto that rectangle.
The tablet around it is its own OBJ, like the iPad in AviTab's sample.
See AviTab's AircraftIntegration/readme.txt.
"""

import json
import os

import bmesh
import bpy
from bpy_extras.io_utils import ExportHelper
from mathutils import Matrix

from io_xplane2blender.xplane_constants import (
    ANIM_TYPE_HIDE,
    COCKPIT_FEATURE_PANEL,
    EXPORT_TYPE_AIRCRAFT,
    EXPORT_TYPE_COCKPIT,
    PANEL_COCKPIT_REGION,
)

# Where the panel rectangle is kept on the screen object, for AviTab.json
AVITAB_PROP = "xplane_avitab_panel"


def _exportable_collection(context):
    """The X-Plane collection the new object lands in, if any"""
    coll = context.collection
    while coll is not None:
        if coll.xplane.is_exportable_collection:
            return coll
        coll = next(
            (c for c in bpy.data.collections if coll.name in c.children), None
        )
    return None


class OBJECT_OT_add_xplane_avitab_screen(bpy.types.Operator):
    """Add a screen AviTab draws on, UV-mapped to a rectangle of the panel texture"""

    bl_idname = "object.add_xplane_avitab_screen"
    bl_label = "AviTab Screen"
    bl_options = {"REGISTER", "UNDO"}

    panel_width: bpy.props.IntProperty(
        name="Panel Width",
        description="Width in pixels of the aircraft's panel texture",
        default=2048,
        min=1,
    )
    panel_height: bpy.props.IntProperty(
        name="Panel Height",
        description="Height in pixels of the aircraft's panel texture",
        default=2048,
        min=1,
    )
    left: bpy.props.IntProperty(
        name="Left",
        description="Left edge of AviTab's rectangle, in panel pixels",
        default=0,
        min=0,
    )
    bottom: bpy.props.IntProperty(
        name="Bottom",
        description="Bottom edge of AviTab's rectangle, in panel pixels from the bottom",
        default=0,
        min=0,
    )
    width: bpy.props.IntProperty(
        name="Width",
        description="Width of AviTab's rectangle in panel pixels (AviTab's default is 800)",
        default=800,
        min=1,
    )
    height: bpy.props.IntProperty(
        name="Height",
        description="Height of AviTab's rectangle in panel pixels (AviTab's default is 480)",
        default=480,
        min=1,
    )
    screen_width: bpy.props.FloatProperty(
        name="Screen Width",
        description="Width of the screen in the cockpit. Its height follows from the"
        " rectangle, so the picture isn't stretched",
        default=0.2,
        min=0.01,
        unit="LENGTH",
    )
    follow_brightness: bpy.props.BoolProperty(
        name="Follow Tablet Brightness",
        description="Light the screen with avitab/brightness",
        default=True,
    )
    add_tablet: bpy.props.BoolProperty(
        name="Tablet Around It",
        description="Also add a tablet body around the screen, in its own collection"
        " so it exports as its own .obj (add it in Plane Maker as a misc object)",
        default=True,
    )
    bezel: bpy.props.FloatProperty(
        name="Bezel",
        description="Border between the screen and the tablet's edge",
        default=0.012,
        min=0.0,
        unit="LENGTH",
    )
    thickness: bpy.props.FloatProperty(
        name="Thickness",
        description="Depth of the tablet body",
        default=0.008,
        min=0.001,
        unit="LENGTH",
    )
    hide_when_disabled: bpy.props.BoolProperty(
        name="Hide When Disabled",
        description="Hide the screen while avitab/panel_enabled is 0",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Panel texture (pixels)")
        row = col.row(align=True)
        row.prop(self, "panel_width", text="Width")
        row.prop(self, "panel_height", text="Height")
        col = layout.column(align=True)
        col.label(text="AviTab rectangle (pixels)")
        row = col.row(align=True)
        row.prop(self, "left")
        row.prop(self, "bottom")
        row = col.row(align=True)
        row.prop(self, "width")
        row.prop(self, "height")
        layout.prop(self, "screen_width")
        layout.prop(self, "follow_brightness")
        layout.prop(self, "hide_when_disabled")
        layout.prop(self, "add_tablet")
        if self.add_tablet:
            row = layout.row(align=True)
            row.prop(self, "bezel")
            row.prop(self, "thickness")
        if (
            self.left + self.width > self.panel_width
            or self.bottom + self.height > self.panel_height
        ):
            layout.label(text="The rectangle goes past the panel texture", icon="ERROR")

    def execute(self, context):
        if (
            self.left + self.width > self.panel_width
            or self.bottom + self.height > self.panel_height
        ):
            self.report({"ERROR"}, "AviTab's rectangle goes past the panel texture")
            return {"CANCELLED"}

        root = _exportable_collection(context)
        if root and root.xplane.layer.cockpit_panel_mode == PANEL_COCKPIT_REGION:
            self.report(
                {"ERROR"},
                f"'{root.name}' uses panel regions. Set its Panel Texture Mode to"
                " Default, or map the screen to a region by hand",
            )
            return {"CANCELLED"}

        # A quad in the XZ plane facing -Y, which is towards the pilot
        half_w = self.screen_width / 2
        half_h = half_w * self.height / self.width
        mesh = bpy.data.meshes.new("AviTab Screen")
        bm = bmesh.new()
        corners = [
            bm.verts.new(co)
            for co in (
                (-half_w, 0, -half_h),
                (half_w, 0, -half_h),
                (half_w, 0, half_h),
                (-half_w, 0, half_h),
            )
        ]
        face = bm.faces.new(corners)
        # Panel texture coordinates, 0 at the bottom like AviTab's "bottom"
        u0, u1 = self.left / self.panel_width, (self.left + self.width) / self.panel_width
        v0, v1 = (
            self.bottom / self.panel_height,
            (self.bottom + self.height) / self.panel_height,
        )
        uv = bm.loops.layers.uv.new("UVMap")
        for loop, co in zip(face.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            loop[uv].uv = co
        bm.normal_update()
        bm.to_mesh(mesh)
        bm.free()

        ob = bpy.data.objects.new("AviTab Screen", mesh)
        context.collection.objects.link(ob)
        cursor = context.scene.cursor
        ob.matrix_world = Matrix.Translation(cursor.location) @ cursor.matrix.to_3x3().to_4x4()

        mat = bpy.data.materials.new("AviTab Screen")
        mat.xplane.cockpit_feature = COCKPIT_FEATURE_PANEL
        if self.follow_brightness:
            mat.xplane.lightLevel = True
            mat.xplane.lightLevel_v1 = 0
            mat.xplane.lightLevel_v2 = 1
            mat.xplane.lightLevel_dataref = "avitab/brightness"
        mesh.materials.append(mat)

        tablet = self._add_tablet(context, ob, half_w, half_h) if self.add_tablet else None

        if self.hide_when_disabled:
            for hidden in filter(None, (ob, tablet)):
                dref = hidden.xplane.datarefs.add()
                dref.path = "avitab/panel_enabled"
                dref.anim_type = ANIM_TYPE_HIDE
                dref.show_hide_v1 = 0
                dref.show_hide_v2 = 0

        ob[AVITAB_PROP] = {
            "left": self.left,
            "bottom": self.bottom,
            "width": self.width,
            "height": self.height,
        }

        for other in context.selected_objects:
            other.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob

        if root is None:
            self.report(
                {"WARNING"},
                "Added outside an X-Plane collection; move it into your cockpit's",
            )
        elif root.xplane.layer.export_type not in {EXPORT_TYPE_COCKPIT, EXPORT_TYPE_AIRCRAFT}:
            self.report(
                {"WARNING"},
                f"'{root.name}' isn't a Cockpit or Aircraft; AviTab only draws in cockpits",
            )
        return {"FINISHED"}

    def _add_tablet(self, context, screen, half_w, half_h):
        """A rounded slab just behind the screen, in its own exportable collection"""
        w = 2 * (half_w + self.bezel)
        h = 2 * (half_h + self.bezel)
        mesh = bpy.data.meshes.new("AviTab Tablet")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        # Front face half a millimetre behind the screen, so they don't z-fight
        front = 0.0005
        for v in bm.verts:
            v.co.x *= w
            v.co.z *= h
            v.co.y = front + (v.co.y + 0.5) * self.thickness
        # Round the four corners: the edges that run front to back
        corners = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1e-6]
        radius = min(self.bezel * 0.9, w / 4, h / 4)
        if radius > 1e-5:
            bmesh.ops.bevel(
                bm, geom=corners, offset=radius, segments=4, affect="EDGES", profile=0.5
            )
        bm.normal_update()
        bm.to_mesh(mesh)
        bm.free()

        mat = bpy.data.materials.new("AviTab Tablet")
        mat.diffuse_color = (0.02, 0.02, 0.025, 1)
        mesh.materials.append(mat)

        coll = bpy.data.collections.new("AviTab Tablet")
        context.scene.collection.children.link(coll)
        coll.xplane.is_exportable_collection = True
        coll.xplane.layer.name = "avitab_tablet"
        coll.xplane.layer.export_type = EXPORT_TYPE_AIRCRAFT

        tablet = bpy.data.objects.new("AviTab Tablet", mesh)
        coll.objects.link(tablet)
        tablet.matrix_world = screen.matrix_world.copy()
        return tablet


class EXPORT_OT_xplane_avitab_json(bpy.types.Operator, ExportHelper):
    """Write the AviTab.json that goes next to the .acf, for the selected AviTab screen"""

    bl_idname = "export.xplane_avitab_json"
    bl_label = "Write AviTab.json"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    enabled: bpy.props.BoolProperty(
        name="Always On",
        description='"enabled": AviTab draws without the aircraft setting avitab/panel_enabled',
        default=True,
    )
    hide_header: bpy.props.BoolProperty(
        name="Hide Header",
        description='"hide_header": leave out AviTab\'s status bar',
        default=False,
    )
    disable_capture_window: bpy.props.BoolProperty(
        name="No Capture Window",
        description='"disable_capture_window": for aircraft whose own windows (SASL)'
        " clash with AviTab's; clicks must then be sent with AviTab/click_left",
        default=False,
    )

    @staticmethod
    def _screen(context):
        active = context.active_object
        if active is not None and AVITAB_PROP in active:
            return active
        return next((ob for ob in context.scene.objects if AVITAB_PROP in ob), None)

    def invoke(self, context, event):
        # AviTab reads exactly this name
        self.filepath = os.path.join(
            os.path.dirname(bpy.data.filepath) or os.path.expanduser("~"), "AviTab.json"
        )
        return super().invoke(context, event)

    def execute(self, context):
        screen = self._screen(context)
        if screen is None:
            self.report({"ERROR"}, "No AviTab screen; add one with Add > Mesh > AviTab Screen")
            return {"CANCELLED"}
        panel = {key: int(screen[AVITAB_PROP][key]) for key in ("left", "bottom", "width", "height")}
        panel["enabled"] = self.enabled
        if self.hide_header:
            panel["hide_header"] = True
        if self.disable_capture_window:
            panel["disable_capture_window"] = True
        path = os.path.join(os.path.dirname(self.filepath), "AviTab.json")
        with open(path, "w") as f:
            json.dump({"panel": panel}, f, indent=4)
            f.write("\n")
        self.report({"INFO"}, f"Wrote {path}; it goes next to the .acf")
        return {"FINISHED"}


def menu_func_add(self, context):
    self.layout.operator(
        OBJECT_OT_add_xplane_avitab_screen.bl_idname, text="AviTab Screen", icon="WINDOW"
    )


def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_xplane_avitab_json.bl_idname, text="AviTab.json (X-Plane)")


_classes = (OBJECT_OT_add_xplane_avitab_screen, EXPORT_OT_xplane_avitab_json)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func_add)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func_add)
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
