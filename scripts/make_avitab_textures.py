"""
Draws the AviTab tablet's textures into io_xplane2blender/resources/avitab:
an albedo per finish and one X-Plane normal map (NORMAL_METALNESS: red and
green are the normal, blue is metalness, alpha is gloss).

    python scripts/make_avitab_textures.py

Needs only numpy. The layout is in io_xplane2blender/xplane_avitab_atlas.py.
"""

import importlib.util
import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "atlas", ROOT / "io_xplane2blender" / "xplane_avitab_atlas.py"
)
atlas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(atlas)

OUT = ROOT / "io_xplane2blender" / "resources" / "avitab"
N = atlas.SIZE
rng = np.random.default_rng(41)


def blurred_noise(sigma: float, sigma_x: float = None) -> np.ndarray:
    """
    Gaussian-filtered white noise over the whole atlas, scaled to -1..1;
    sigma_x, if given, blurs across differently from down
    """
    sigma_x = sigma if sigma_x is None else sigma_x
    white = rng.standard_normal((N, N))
    fy = np.fft.fftfreq(N)[:, None]
    fx = np.fft.fftfreq(N)[None, :]
    kernel = np.exp(-2 * np.pi**2 * ((sigma * fy) ** 2 + (sigma_x * fx) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * kernel))
    return out / np.abs(out).max()


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def cell_coords(cell):
    """Slices for a cell and its pixel centres as fractions: fx right, fy up"""
    x, y, w, h = cell
    ys, xs = np.mgrid[0:h, 0:w]
    return (slice(y, y + h), slice(x, x + w)), (xs + 0.5) / w, 1 - (ys + 0.5) / h


def disc_r(cell):
    """Distance from a square cell's centre, 1 at its edge"""
    sl, fx, fy = cell_coords(cell)
    return sl, np.hypot(fx - 0.5, fy - 0.5) * 2


# Channels, all 0..1 floats; albedo is per finish, filled in at the end
height = np.zeros((N, N))
metal = np.ones((N, N))
gloss = np.zeros((N, N))
# Where each finish's metal colour shows (1), and what shows elsewhere
metal_mask = np.ones((N, N))
other = np.zeros((N, N, 3))


def paint(sl, mask, colour=None, metalness=None, glossiness=None):
    m = mask[..., None]
    if colour is not None:
        other[sl] = other[sl] * (1 - m) + np.array(colour) / 255 * m
        metal_mask[sl] *= 1 - mask
    if metalness is not None:
        metal[sl] = metal[sl] * (1 - mask) + metalness * mask
    if glossiness is not None:
        gloss[sl] = gloss[sl] * (1 - mask) + glossiness * mask


# Bead-blasted anodising everywhere to start: fine grain in the height,
# and a faint mottle in the gloss so reflections don't look printed on
grain = blurred_noise(1.5)
mottle = blurred_noise(90)
height += grain * 0.12
gloss[:] = 0.52 + 0.03 * mottle + 0.015 * grain
tint = 1 + 0.015 * mottle

# The edge band is stretched about six times along its length on the
# tablet, so its grain is drawn squeezed that way to come out even
sl, fx, fy = cell_coords(atlas.SIDE)
side_grain = blurred_noise(1.5, 0.25)[sl]
side_mottle = blurred_noise(40, 7)[sl]
height[sl] = side_grain * 0.08
gloss[sl] = 0.55 + 0.03 * side_mottle + 0.01 * side_grain
tint[sl] = 1 + 0.015 * side_mottle

# Glass: deep black, near-perfect gloss, no grain
sl, fx, fy = cell_coords(atlas.GLASS)
height[sl] = 0
paint(sl, np.ones(fx.shape), (6, 6, 8), 0.0, 0.97)

# Speaker grille: a row of round holes along the middle
sl, fx, fy = cell_coords(atlas.GRILLE)
w_m = atlas.GRILLE[2] / atlas.GRILLE_PX_PER_M
h_m = atlas.GRILLE[3] / atlas.GRILLE_PX_PER_M
x_m = (fx - 0.5) * w_m
y_m = (fy - 0.5) * h_m
first = -(atlas.GRILLE_HOLES - 1) / 2 * atlas.GRILLE_PITCH
k = np.clip(np.round((x_m - first) / atlas.GRILLE_PITCH), 0, atlas.GRILLE_HOLES - 1)
d = np.hypot(x_m - (first + k * atlas.GRILLE_PITCH), y_m)
px = 1 / atlas.GRILLE_PX_PER_M
hole = 1 - smoothstep(atlas.GRILLE_HOLE / 2 - px, atlas.GRILLE_HOLE / 2 + px, d)
# Chamfered rims catch the light
rim = smoothstep(atlas.GRILLE_HOLE / 2 + 3 * px, atlas.GRILLE_HOLE / 2 - px, d)
height[sl] -= rim * 3.0
paint(sl, hole, (10, 10, 11), 0.0, 0.15)

# Rear camera, seen from above: the housing's top, a diamond-cut edge,
# the black sapphire ring, the lens barrel and the coated front element
sl, r = disc_r(atlas.LENS)
cut = smoothstep(0.76, 0.785, r) * (1 - smoothstep(0.80, 0.825, r))
height[sl] += smoothstep(0.78, 0.82, r) * 4.0
gloss[sl] = gloss[sl] * (1 - cut) + 0.92 * cut
inner = 1 - smoothstep(0.765, 0.78, r)
height[sl] *= 1 - inner
paint(sl, inner, (9, 9, 11), 0.0, 0.95)
barrel = 1 - smoothstep(0.50, 0.515, r)
ridges = 0.5 + 0.5 * np.cos(r * np.pi * 60)
paint(sl, barrel, (22, 22, 24), 0.0, 0.85)
height[sl] += barrel * ridges * 0.3 * (r > 0.31)
element = 1 - smoothstep(0.30, 0.312, r)
# Coating: violet in the middle going to green-blue at the rim
t = np.clip(r / 0.3, 0, 1)[..., None]
coat = (np.array([24, 16, 44]) * (1 - t) + np.array([10, 30, 34]) * t) / 255
other[sl] = other[sl] * (1 - element[..., None]) + coat * element[..., None]
metal_mask[sl] *= 1 - element
metal[sl] = metal[sl] * (1 - element)
gloss[sl] = gloss[sl] * (1 - element) + 0.98 * element
# A domed element
height[sl] += element * (1 - (r / 0.3) ** 2) * 8

# Front camera: a small violet lens in black
sl, r = disc_r(atlas.FRONT_CAM)
height[sl] = 0
paint(sl, np.ones(r.shape), (7, 7, 9), 0.0, 0.96)
paint(sl, 1 - smoothstep(0.42, 0.47, r), (20, 14, 36), 0.0, 0.98)
paint(sl, smoothstep(0.30, 0.36, r) * (1 - smoothstep(0.42, 0.47, r)), (14, 14, 18), 0.0, 0.9)

# Flash: a pale diffuser with Fresnel rings, in a dark rim
sl, r = disc_r(atlas.FLASH)
height[sl] = 0
paint(sl, np.ones(r.shape), (40, 40, 42), 0.0, 0.9)
lens = 1 - smoothstep(0.78, 0.84, r)
paint(sl, lens, (206, 198, 168), 0.0, 0.8)
height[sl] += lens * np.sin(r * np.pi * 14) * 0.8

# Smart connector contact: gold, polished
sl, r = disc_r(atlas.CONTACT)
height[sl] = 0
pad = 1 - smoothstep(0.86, 0.94, r)
paint(sl, pad, (220, 178, 90), 1.0, 0.82)
paint(sl, 1 - pad, (18, 18, 20), 0.0, 0.5)


def normal_map() -> np.ndarray:
    # Height is in rough "texels"; this sets how steep it looks
    gy, gx = np.gradient(height * 0.35)
    nx, ny = -gx, gy  # rows run down the image, V runs up
    length = np.sqrt(nx**2 + ny**2 + 1)
    out = np.empty((N, N, 4))
    out[..., 0] = 0.5 + 0.5 * nx / length
    out[..., 1] = 0.5 + 0.5 * ny / length
    out[..., 2] = np.clip(metal, 0, 1)
    out[..., 3] = np.clip(gloss, 0, 1)
    return out


def albedo(finish: str) -> np.ndarray:
    base = np.array(atlas.FINISHES[finish][1]) / 255 * tint[..., None]
    m = metal_mask[..., None]
    return base * m + other * (1 - m)


def write_png(path: Path, pixels: np.ndarray) -> None:
    rgb = np.clip(np.round(pixels * 255), 0, 255).astype(np.uint8)
    h, w, channels = rgb.shape
    # Filter each row with Sub (1); it squeezes the smooth fields well
    flat = rgb.reshape(h, w * channels).astype(np.int16)
    diff = flat.copy()
    diff[:, channels:] -= flat[:, :-channels]
    rows = (diff % 256).astype(np.uint8)
    raw = np.hstack([np.ones((h, 1), np.uint8), rows]).tobytes()

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    colour_type = {3: 2, 4: 6}[channels]
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, colour_type, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write_png(OUT / atlas.NORMAL, normal_map())
    for finish in atlas.FINISHES:
        write_png(OUT / atlas.finish_file(finish), albedo(finish))
    for p in sorted(OUT.glob("*.png")):
        print(f"{p.name}: {p.stat().st_size // 1024} KB")
