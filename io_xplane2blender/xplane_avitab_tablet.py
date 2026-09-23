"""
The body of an AviTab tablet, made like an iPad: flat aluminium sides with
rounded corners, glass over the bezel with a softened edge, speaker grilles,
buttons, a front camera, and a camera bump, flash and smart connector on
the back. It's UV-mapped onto one texture atlas (see xplane_avitab_atlas.py)
with an X-Plane NORMAL_METALNESS normal map.

The tablet is built in the screen's space: X across, Z up, the front facing
-Y towards the pilot. Anticlockwise seen from the front means facing -Y.
"""

import math
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import bmesh
import bpy

from io_xplane2blender import xplane_avitab_atlas as atlas
from io_xplane2blender.xplane_helpers import get_plugin_resources_folder

RESOURCES = Path(get_plugin_resources_folder()) / "avitab"

# Segments in each rounded corner, round a camera, and in rounded edges
CORNER_SEGMENTS = 12
ROUND_SEGMENTS = 32
EDGE_SEGMENTS = 3

# The glass's front, just behind the screen so they don't z-fight
FRONT = 0.0005
# How far decals (camera, flash, contacts) stand off the surface under them
DECAL = 0.00015

Vec3 = Tuple[float, float, float]
UV = Tuple[float, float]


class _Polys:
    """Faces with their UVs and shading, welded where their corners meet"""

    def __init__(self):
        self.faces: List[Tuple[List[Vec3], List[UV], bool]] = []

    def add(self, co: Sequence[Vec3], uvs: Sequence[UV], smooth: bool) -> None:
        self.faces.append((list(co), list(uvs), smooth))

    def ring_bands(self, rings, uv_of, skip=None, smooth=True, closed=True) -> None:
        """
        Quads between consecutive rings of points, each ring further back
        than the last, facing out. uv_of(ring, point, (j, k)) gives the UV
        of a corner of the quad on segment j to k; skip(band, (j, k)) leaves
        out quads that are made some other way.
        """
        n = len(rings[0])
        for i in range(len(rings) - 1):
            for j in range(n if closed else n - 1):
                k = (j + 1) % n
                if skip and skip(i, (j, k)):
                    continue
                corners = ((i, j), (i + 1, j), (i + 1, k), (i, k))
                uvs = [uv_of(ri, pj, pk) for ri, pj, pk in (
                    (i, j, (j, k)), (i + 1, j, (j, k)), (i + 1, k, (j, k)), (i, k, (j, k))
                )]
                self.add([rings[ri][pj] for ri, pj in corners], uvs, smooth)

    def to_mesh(self, mesh: bpy.types.Mesh) -> None:
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")
        verts: Dict[Tuple[int, int, int], bmesh.types.BMVert] = {}

        def vert(co):
            key = tuple(round(c * 1e6) for c in co)
            if key not in verts:
                verts[key] = bm.verts.new(co)
            return verts[key]

        for co, uvs, smooth in self.faces:
            try:
                face = bm.faces.new([vert(c) for c in co])
            except ValueError:
                continue  # collapsed to a line or already there
            face.smooth = smooth
            for loop, uv in zip(face.loops, uvs):
                loop[uv_layer].uv = uv
        bm.normal_update()
        bm.to_mesh(mesh)
        bm.free()
        # Blender before 4.1 only keeps flat faces' edges sharp with this
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = math.pi


def _rounded_rect(a, b, radius, inset, marks) -> List[Tuple[float, float]]:
    """
    A rounded rectangle of half sizes a, b, shrunk by inset, anticlockwise
    from the bottom of its right edge's lower corner. marks are heights of
    extra points on the left and right edges.
    """
    r = radius - inset
    cx, cz = a - radius, b - radius
    pts = []

    def arc(x, z, start):
        for i in range(CORNER_SEGMENTS + 1):
            t = math.radians(start + 90 * i / CORNER_SEGMENTS)
            pts.append((x + r * math.cos(t), z + r * math.sin(t)))

    arc(cx, -cz, -90)
    pts += [(a - inset, z) for z in sorted(marks)]
    arc(cx, cz, 0)
    arc(-cx, cz, 90)
    pts += [(-(a - inset), z) for z in sorted(marks, reverse=True)]
    arc(-cx, -cz, 180)
    return pts


def _circle(cx, cz, r, n=ROUND_SEGMENTS) -> List[Tuple[float, float]]:
    """Anticlockwise from the front"""
    return [
        (cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def _disc_uv(cell, pts, cx, cz, r, mirror=False) -> List[UV]:
    """UVs for a disc filling a square cell's inscribed circle"""
    s = -1 if mirror else 1
    return [
        atlas.uv(cell, 0.5 + s * 0.49 * (x - cx) / r, 0.5 + 0.49 * (z - cz) / r)
        for x, z in pts
    ]


def _decal(polys, cell, cx, y, cz, r, facing_back, n=24) -> None:
    pts = _circle(cx, cz, r, n)
    uvs = _disc_uv(cell, pts, cx, cz, r, mirror=facing_back)
    if facing_back:
        pts, uvs = pts[::-1], uvs[::-1]
    polys.add([(x, y, z) for x, z in pts], uvs, False)


def _button(polys, x, y, z, sx, sy, sz, uv_origin) -> None:
    """A rounded key, UV-mapped onto a patch of the aluminium edge"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x + v.co.x * sx
        v.co.y = y + v.co.y * sy
        v.co.z = z + v.co.z * sz
    bmesh.ops.bevel(
        bm,
        geom=list(bm.edges),
        offset=min(sx, sy, sz) * 0.45,
        segments=3,
        affect="EDGES",
        profile=0.5,
    )
    bm.normal_update()
    u0, v0 = uv_origin
    for face in bm.faces:
        n = face.normal
        flat = max(abs(n.x), abs(n.y), abs(n.z)) > 0.999
        co = [tuple(v.co) for v in face.verts]
        # Planar mapping at the edge band's scale; it's uniform aluminium
        uvs = [
            atlas.uv(atlas.SIDE, u0 + (c[0] - x) * 4 + (c[2] - z) * 4, v0 + (c[1] - y) * 40)
            for c in co
        ]
        polys.add(co, uvs, not flat)
    bm.free()


def build_tablet_mesh(
    name: str, half_w: float, half_h: float, bezel: float, thickness: float
) -> bpy.types.Mesh:
    """The tablet round a screen of half size half_w by half_h"""
    a, b = half_w + bezel, half_h + bezel
    back = FRONT + thickness
    # iPad-like corners, as round as they can be without cutting the
    # screen's square corners
    radius = min(1.8 * bezel, 0.45 * min(a, b))
    fit = (math.sqrt(2) * bezel - 0.0005) / (math.sqrt(2) - 1)
    radius = max(min(radius, fit), 0.0015)
    e_front = min(0.0006, thickness * 0.15, radius * 0.4)
    e_back = min(0.0012, thickness * 0.25, radius * 0.4)

    # Speaker grilles on the left and right edges: two each when they fit
    straight = b - radius
    grilles: List[Tuple[float, float]] = []
    if atlas.GRILLE_SEG <= 0.8 * straight:
        length = atlas.GRILLE_SEG
        centres = (-straight / 2, straight / 2)
    else:
        length = min(atlas.GRILLE_SEG, 1.6 * straight * 0.8)
        centres = (0.0,)
    grille_scale = length / atlas.GRILLE_SEG
    if length > 0.004:
        grilles = [(c - length / 2, c + length / 2) for c in centres]
    marks = [z for g in grilles for z in g]

    # The profile, front to back: rounded glass edge, flat side, rounded
    # back edge. Each ring is (inset, y)
    profile = []
    for k in range(EDGE_SEGMENTS + 1):
        t = math.pi / 2 * k / EDGE_SEGMENTS
        profile.append((e_front * (1 - math.sin(t)), FRONT + e_front * (1 - math.cos(t))))
    for k in range(EDGE_SEGMENTS + 1):
        t = math.pi / 2 * k / EDGE_SEGMENTS
        profile.append((e_back * (1 - math.cos(t)), back - e_back + e_back * math.sin(t)))
    glass_bands = EDGE_SEGMENTS  # rings 0..EDGE_SEGMENTS are glass
    side_ring = EDGE_SEGMENTS  # the flat side runs from here to the next ring

    outlines = [_rounded_rect(a, b, radius, inset, marks) for inset, _ in profile]
    rings = [[(x, y, z) for x, z in outline] for outline, (_, y) in zip(outlines, profile)]

    # Distance round the outline, for U along the edge
    edge = outlines[side_ring]
    along = [0.0]
    for (x0, z0), (x1, z1) in zip(edge, edge[1:] + edge[:1]):
        along.append(along[-1] + math.hypot(x1 - x0, z1 - z0))
    total = along[-1]
    # Distance down the metal part of the profile, for V
    down = [0.0]
    for (i0, y0), (i1, y1) in zip(profile[side_ring:], profile[side_ring + 1 :]):
        down.append(down[-1] + math.hypot(i1 - i0, y1 - y0))

    def is_grille(j, k):
        (x0, z0), (x1, z1) = edge[j], edge[k]
        mid = (z0 + z1) / 2
        return abs(x0 - x1) < 1e-9 and abs(abs(x0) - a) < 1e-9 and any(
            lo < mid < hi for lo, hi in grilles
        )

    band_h = back - e_back - (FRONT + e_front)
    grille_u = atlas.GRILLE_SEG * atlas.GRILLE_PX_PER_M / atlas.GRILLE[2] / 2
    grille_v = min(
        band_h * atlas.GRILLE_PX_PER_M / grille_scale / atlas.GRILLE[3], 0.94
    ) / 2

    polys = _Polys()

    # Glass edge: black glass, UVs anywhere in its cell
    def glass_uv(ring, point, seg):
        return atlas.uv(atlas.GLASS, 0.1 + 0.8 * _u(point, seg), 0.3 + 0.4 * ring / glass_bands)

    def _u(point, seg):
        j, k = seg
        # The seam: the segment that closes the loop ends at the total
        s = total if (point == 0 and j == len(edge) - 1) else along[point]
        return s / total

    polys.ring_bands(rings[: glass_bands + 1], glass_uv)

    # Aluminium from the side back round the back edge, with the grilles
    metal_rings = rings[side_ring:]

    def metal_uv(ring, point, seg):
        return atlas.uv(atlas.SIDE, 0.005 + 0.99 * _u(point, seg), 0.95 - 0.9 * down[ring] / down[-1])

    # The grilles replace the flat side (band 0) where they are
    polys.ring_bands(metal_rings, metal_uv, skip=lambda band, seg: band == 0 and is_grille(*seg))

    def grille_uv(ring, point, seg):
        j, k = seg
        lo = min(edge[j][1], edge[k][1])
        hi = max(edge[j][1], edge[k][1])
        fu = (edge[point][1] - lo) / (hi - lo)
        return atlas.uv(atlas.GRILLE, 0.5 + grille_u * (2 * fu - 1), 0.5 + grille_v * (1 - 2 * ring))

    polys.ring_bands(metal_rings[:2], grille_uv, skip=lambda band, seg: not is_grille(*seg))

    # Front glass: one face; the screen covers its middle
    cap = outlines[0]
    polys.add(
        [(x, FRONT, z) for x, z in cap],
        [atlas.uv(atlas.GLASS, 0.5 + 0.4 * x / a, 0.5 + 0.4 * z / b) for x, z in cap],
        False,
    )
    # Back: aluminium, read from behind so mirrored, at one scale both ways
    cap = outlines[-1][::-1]
    bx, by, bw, bh = atlas.BACK
    px = min((bw - 32) / (2 * a), (bh - 32) / (2 * b))
    polys.add(
        [(x, back, z) for x, z in cap],
        [atlas.uv(atlas.BACK, 0.5 - x * px / bw, 0.5 + z * px / bh) for x, z in cap],
        False,
    )

    # Front camera, in the middle of the bezel above the screen
    if bezel > 0.004:
        r = min(0.0011, bezel * 0.22)
        _decal(polys, atlas.FRONT_CAM, 0.0, FRONT - DECAL, half_h + bezel / 2, r, False)

    # Rear camera bump in the top corner, seen from behind on the left
    lens_r = min(0.005, 0.12 * b)
    off = max(lens_r + 0.0045, radius * 0.85)
    cx, cz = a - off, b - off
    rise = min(0.0009, thickness * 0.15)
    e_bump = rise * 0.45
    bump_profile = [(0.0, back), (0.0, back + rise - e_bump)]
    for k in range(1, EDGE_SEGMENTS + 1):
        t = math.pi / 2 * k / EDGE_SEGMENTS
        bump_profile.append((e_bump * (1 - math.cos(t)), back + rise - e_bump + e_bump * math.sin(t)))
    bump = [
        [(x, y, z) for x, z in _circle(cx, cz, lens_r - inset)] for inset, y in bump_profile
    ]

    def bump_uv(ring, point, seg):
        j, k = seg
        f = (ROUND_SEGMENTS if point == 0 and j == ROUND_SEGMENTS - 1 else point) / ROUND_SEGMENTS
        return atlas.uv(atlas.SIDE, 0.02 + 0.1 * f, 0.9 - 0.8 * ring / (len(bump) - 1))

    polys.ring_bands(bump, bump_uv)
    top_r = lens_r - e_bump
    top = _circle(cx, cz, top_r)[::-1]
    polys.add(
        [(x, back + rise, z) for x, z in top],
        _disc_uv(atlas.LENS, top, cx, cz, top_r, mirror=True),
        False,
    )
    # Flash beside it, towards the middle
    flash_r = lens_r * 0.3
    _decal(polys, atlas.FLASH, cx - lens_r - flash_r - 0.0025, back + DECAL, cz, flash_r, True)
    # Smart connector: three contacts at the bottom middle of the back
    for i in (-1, 0, 1):
        _decal(polys, atlas.CONTACT, i * 0.0028, back + DECAL, -b + 0.0055, 0.0006, True, n=16)

    # Buttons on the top edge: the top button on the left, volume on the right
    depth = min(0.0028, band_h * 0.5)
    if 2 * (a - radius) > 0.07 and depth > 0.001:
        y = (FRONT + back) / 2
        proud, sunk = 0.0005, 0.0004
        z = b + (proud - sunk) / 2
        h = proud + sunk
        _button(polys, -a + radius + 0.018, y, z, 0.016, depth, h, (0.2, 0.5))
        right = a - radius - 0.012
        _button(polys, right, y, z, 0.011, depth, h, (0.3, 0.5))
        _button(polys, right - 0.0145, y, z, 0.011, depth, h, (0.4, 0.5))

    mesh = bpy.data.meshes.new(name)
    polys.to_mesh(mesh)
    return mesh


def install_textures(dest: Optional[Path], finish: str) -> Tuple[Path, Path, bool]:
    """
    Copies the finish's albedo and the normal map into dest, keeping any
    already there (they may have been edited). Without dest they're used
    from the add-on, and the last value is False.
    """
    names = (atlas.finish_file(finish), atlas.NORMAL)
    if dest is None:
        return RESOURCES / names[0], RESOURCES / names[1], False
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        if not (dest / name).exists():
            shutil.copyfile(RESOURCES / name, dest / name)
    return dest / names[0], dest / names[1], True


def make_material(name: str, albedo: Path, normal: Path) -> bpy.types.Material:
    """
    A material showing the textures in Blender's viewport as X-Plane reads
    them: the normal map's blue is metalness and its alpha is gloss. The
    exporter writes the textures from the collection's settings, not these.
    """
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (0.3, 0.31, 0.33, 1)
    mat.metallic = 1.0
    mat.roughness = 0.45
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return mat

    def image_node(path, colour, x, y):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(path), check_existing=True)
        node.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        # Gloss is in alpha; don't let Blender multiply the colour by it
        node.image.alpha_mode = "CHANNEL_PACKED"
        node.location = (x, y)
        return node

    def new(*types):
        for t in types:
            try:
                return nodes.new(t)
            except RuntimeError:
                pass
        raise RuntimeError(f"None of {types} in this Blender")

    x = bsdf.location.x
    base = image_node(albedo, True, x - 900, bsdf.location.y + 200)
    links.new(base.outputs["Color"], bsdf.inputs["Base Color"])

    nml = image_node(normal, False, x - 900, bsdf.location.y - 200)
    split = new("ShaderNodeSeparateColor", "ShaderNodeSeparateRGB")
    split.location = (x - 600, bsdf.location.y - 200)
    links.new(nml.outputs["Color"], split.inputs[0])
    links.new(split.outputs[2], bsdf.inputs["Metallic"])
    rough = nodes.new("ShaderNodeMath")
    rough.operation = "SUBTRACT"
    rough.inputs[0].default_value = 1.0
    rough.location = (x - 400, bsdf.location.y - 350)
    links.new(nml.outputs["Alpha"], rough.inputs[1])
    links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    # Only red and green are the normal; its Z is rebuilt from them
    join = new("ShaderNodeCombineColor", "ShaderNodeCombineRGB")
    join.location = (x - 400, bsdf.location.y - 150)
    links.new(split.outputs[0], join.inputs[0])
    links.new(split.outputs[1], join.inputs[1])
    join.inputs[2].default_value = 1.0
    bump = nodes.new("ShaderNodeNormalMap")
    bump.location = (x - 200, bsdf.location.y - 150)
    links.new(join.outputs[0], bump.inputs["Color"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat
