"""
atmosphere.py - Atmospheric effects: rice paper texture, ink mist, red sun, and calligraphy seal
Enhances the Shan Shui aesthetic with traditional Chinese painting atmosphere.
"""

import math
import random
from typing import List, Tuple, Optional

from .utils import (
    PolyPrimitive, poly, stroke, blob, div,
    noise, parse_color
)

# -----------------------------------------------------------------------------
# 1. Procedural Rice Paper Generator
# -----------------------------------------------------------------------------
def generate_paper_texture(width: int = 512, height: int = 512):
    """
    Generates a seamless 512x512 PIL Image of fibrous, warm cream rice paper
    matching lines 4337-4361 of shanshui/index.html.
    """
    from PIL import Image
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    half_w = width // 2 + 1
    half_h = height // 2 + 1

    for i in range(half_w):
        for j in range(half_h):
            c = 245.0 + noise(i * 0.1, j * 0.1) * 10.0 - random.random() * 20.0
            r = int(min(255, max(0, c)))
            g = int(min(255, max(0, c * 0.95)))
            b = int(min(255, max(0, c * 0.85)))
            col = (r, g, b)

            pixels[i, j] = col
            pixels[width - 1 - i, j] = col
            pixels[i, height - 1 - j] = col
            pixels[width - 1 - i, height - 1 - j] = col

    return img

# -----------------------------------------------------------------------------
# 2. Ink Wash Mist & Cloud Ribbons
# -----------------------------------------------------------------------------
def mist_band(xoff: float, yoff: float, width: float = 1200.0,
              height: float = 80.0, seed: float = 0.0,
              alpha: float = 0.15) -> List[PolyPrimitive]:
    """
    Soft translucent mist band drifting between mountain layers.
    Simulates ink wash vapor and valley clouds (yunhai 云海).
    """
    prims: List[PolyPrimitive] = []
    reso = 40
    step = width / float(reso)

    upper: List[Tuple[float, float]] = []
    lower: List[Tuple[float, float]] = []

    for i in range(reso + 1):
        x = xoff + i * step
        t = i / float(reso)
        envelope = math.sin(t * math.pi)

        n1 = (noise(x * 0.003, seed, 1.0) - 0.5) * height * 0.8
        n2 = (noise(x * 0.003, seed + 10.0, 2.0) - 0.5) * height * 0.8

        uy = yoff - envelope * (height * 0.5 + n1)
        ly = yoff + envelope * (height * 0.5 + n2)

        upper.append((x, uy))
        lower.append((x, ly))

    hull = upper + list(reversed(lower))
    # Soft translucent warm-white vapor polygon
    a_int = int(min(255, max(0, alpha * 255)))
    prims.extend(poly(hull, fil=(250, 248, 240, a_int)))

    # Delicate wispy contour strands
    wisp_col = f"rgba(235,230,220,{(alpha * 0.8):.3f})"
    prims.extend(stroke(upper, wid=2.0, col=wisp_col, noi=0.8, fun=lambda x: math.sin(x * math.pi)))
    prims.extend(stroke(lower, wid=2.0, col=wisp_col, noi=0.8, fun=lambda x: math.sin(x * math.pi)))

    return prims

# -----------------------------------------------------------------------------
# 3. Cinnabar Red Sun / Rising Mist
# -----------------------------------------------------------------------------
def red_sun(x: float, y: float, radius: float = 60.0) -> List[PolyPrimitive]:
    """
    Traditional stylized Chinese red sun rendered in translucent vermilion ink wash.
    """
    prims: List[PolyPrimitive] = []
    # Concentric soft rings fading outward
    rings = 12
    for r_idx in range(rings, 0, -1):
        r = radius * (r_idx / float(rings))
        # Vermilion / cinnabar red (#D74128)
        alpha = int(40 + (1.0 - r_idx / float(rings)) * 140)
        circle_pts = []
        segments = 36
        for s in range(segments):
            ang = (s / float(segments)) * math.pi * 2.0
            # Slight organic wobble
            wobble = 1.0 + (noise(math.cos(ang) + 5.0, math.sin(ang) + 5.0, r_idx * 0.1) - 0.5) * 0.06
            circle_pts.append((x + math.cos(ang) * r * wobble, y + math.sin(ang) * r * wobble))
        prims.extend(poly(circle_pts, fil=(215, 65, 40, alpha), str_=(215, 65, 40, alpha), wid=0.5))

    return prims

# -----------------------------------------------------------------------------
# 4. Calligraphy Seal / Chop Stamp (Yinzhang 印章)
# -----------------------------------------------------------------------------
def calligraphy_seal(x: float, y: float, size: float = 48.0,
                     style: str = "yin") -> List[PolyPrimitive]:
    """
    Traditional Chinese carved seal / chop stamp (*yinzhang* 印章).
    Renders weathered cinnabar vermilion ink with authentic seal-script glyphs
    for 'Shan Shui' (山水 - Mountain & Water) in Yin (白文) or Yang (朱文) style.
    """
    prims: List[PolyPrimitive] = []
    # Cinnabar vermilion ink and parchment white colors
    seal_col = (195, 38, 25, 235)
    white_col = (248, 245, 235, 245)

    # Outer distressed square border
    half = size * 0.5
    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    border_pts: List[Tuple[float, float]] = []

    for c_idx in range(4):
        c0 = corners[c_idx]
        c1 = corners[(c_idx + 1) % 4]
        sub = div([c0, c1], 4)
        for pt in sub[:-1]:
            # Add distressed rough stone carving jitter
            jitter = (noise(pt[0] * 0.2, pt[1] * 0.2) - 0.5) * 1.8
            border_pts.append((x + pt[0] + jitter, y + pt[1] + jitter))

    if style == "yin":
        # Yin seal (白文): solid red cinnabar background with carved negative characters
        prims.extend(poly(border_pts, fil=seal_col, str_=seal_col, wid=1.5))
        glyph_col = white_col
    else:
        # Yang seal (朱文): open background with red positive border and red characters
        prims.extend(poly(border_pts, fil=(0, 0, 0, 0), str_=seal_col, wid=3.0))
        glyph_col = seal_col

    inner_scale = size * 0.68
    ih = inner_scale * 0.5

    # Traditional Chinese seal reading order: Right-to-Left
    # Right column: 山 (Shan - Mountain)
    # Left column:  水 (Shui - Water)

    # Coordinates for 山 (Shan)
    cx_s = ih * 0.50
    lx_s = ih * 0.16
    rx_s = ih * 0.84
    y_top_s = -ih * 0.78
    y_bot_s = ih * 0.78
    y_prong_s = -ih * 0.35

    # Coordinates for 水 (Shui)
    cx_w = -ih * 0.50
    lx_w = -ih * 0.84
    rx_w = -ih * 0.16
    y_top_w = -ih * 0.78
    y_bot_w = ih * 0.78

    glyph_paths: List[List[Tuple[float, float]]] = [
        # --- 山 (Shan - Mountain) ---
        # Central tall peak
        [(cx_s, y_top_s), (cx_s, y_bot_s)],
        # Left peak with serif curving into base
        [(lx_s + ih * 0.06, y_prong_s), (lx_s, y_prong_s), (lx_s, y_bot_s)],
        # Right peak with serif curving into base
        [(rx_s - ih * 0.06, y_prong_s), (rx_s, y_prong_s), (rx_s, y_bot_s)],
        # Bottom connecting cradle base
        [(lx_s, y_bot_s), (rx_s, y_bot_s)],

        # --- 水 (Shui - Water) ---
        # Sinuous central stream
        [(cx_w, y_top_w), (cx_w + ih * 0.05, -ih * 0.28), (cx_w - ih * 0.05, ih * 0.28), (cx_w, y_bot_w)],
        # Upper-left water ripple
        [(cx_w - ih * 0.08, -ih * 0.18), (lx_w, -ih * 0.18), (lx_w, -ih * 0.70)],
        # Lower-left water ripple
        [(cx_w - ih * 0.08, ih * 0.18), (lx_w, ih * 0.18), (lx_w, ih * 0.70)],
        # Upper-right water ripple
        [(cx_w + ih * 0.08, -ih * 0.18), (rx_w, -ih * 0.18), (rx_w, -ih * 0.70)],
        # Lower-right water ripple
        [(cx_w + ih * 0.08, ih * 0.18), (rx_w, ih * 0.18), (rx_w, ih * 0.70)],
    ]

    for path in glyph_paths:
        sub = div(path, 3)
        jittered: List[Tuple[float, float]] = []
        for pt in sub:
            # Subtle stone carving chisel texture (金石气)
            jx = (noise((x + pt[0]) * 0.4, (y + pt[1]) * 0.4) - 0.5) * 0.5
            jy = (noise((x + pt[0]) * 0.4 + 5.0, (y + pt[1]) * 0.4 + 5.0) - 0.5) * 0.5
            jittered.append((x + pt[0] + jx, y + pt[1] + jy))
        prims.extend(stroke(jittered, wid=1.2, col=glyph_col, out=0.5, noi=0.08, fun=lambda _: 1.0))

    return prims
