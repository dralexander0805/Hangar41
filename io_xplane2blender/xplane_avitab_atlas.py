"""
Layout of the AviTab tablet's texture atlas, shared by the tablet builder
and scripts/make_avitab_textures.py, which draws the atlas. No bpy here, so
the script can load this file on its own.

Cells are (x, y, width, height) in pixels from the top left, like an image
editor shows them.
"""

SIZE = 2048

BACK = (0, 0, 2048, 1344)  # Aluminium back
SIDE = (0, 1344, 2048, 128)  # Aluminium band round the edge, and the buttons
GLASS = (0, 1472, 256, 256)  # Black glass over the bezel
GRILLE = (256, 1472, 1024, 128)  # A speaker grille in the edge
LENS = (1280, 1472, 256, 256)  # Top of the rear camera
FRONT_CAM = (1536, 1472, 128, 128)  # Front camera in the bezel
FLASH = (1664, 1472, 128, 128)  # Rear flash
CONTACT = (1792, 1472, 128, 128)  # One smart connector contact

# The grille cell's scale, and the stretch of edge one grille takes up
GRILLE_PX_PER_M = 12000
GRILLE_HOLES = 13
GRILLE_PITCH = 0.0012
GRILLE_HOLE = 0.00075
GRILLE_SEG = (GRILLE_HOLES - 1) * GRILLE_PITCH + GRILLE_HOLE + 0.002

# Finishes: the name and sRGB colour of the anodised aluminium. Each has
# its own albedo, and they share one normal map
FINISHES = {
    "SPACE_GREY": ("Space Grey", (108, 110, 115)),
    "SILVER": ("Silver", (196, 198, 201)),
    "MIDNIGHT": ("Midnight", (50, 56, 70)),
    "STARLIGHT": ("Starlight", (214, 205, 188)),
    "NAVY": ("Navy", (22, 34, 68)),
    "PURPLE": ("Purple", (168, 156, 192)),
    "PINK": ("Pink", (222, 182, 182)),
    "FOREST": ("Forest", (38, 64, 46)),
}
NORMAL = "avitab_tablet_NML.png"


def finish_file(finish: str) -> str:
    """The albedo for a finish"""
    return f"avitab_tablet_{finish.lower()}.png"


def uv(cell, fx, fy):
    """
    UV of the point at fractions fx, fy across a cell, fy from its bottom,
    for Blender and X-Plane, whose V runs up from the bottom of the image
    """
    x, y, w, h = cell
    return (x + fx * w) / SIZE, 1 - (y + (1 - fy) * h) / SIZE
