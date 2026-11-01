"""
utils.py - Custom math, noise functions, computational geometry, and brush stroke algorithms
Reproducing the core generative primitives of Lingdong Huang's Shan Shui for Py5.
"""

import math
import random
import re
from typing import List, Tuple, Optional, Callable, Union

# -----------------------------------------------------------------------------
# 1. Environment & JBR Runtime Auto-Configuration for Py5
# -----------------------------------------------------------------------------
import os
from pathlib import Path

def init_py5_runtime():
    """Ensure Java / JBR environment variables are configured for JPype/Py5 on Windows."""
    jbr_path = Path("C:/Program Files/JetBrains/PyCharm 2026.2.4/jbr")
    if jbr_path.exists():
        os.environ.setdefault("JAVA_HOME", str(jbr_path))
        bin_dir = str(jbr_path / "bin")
        server_dir = str(jbr_path / "bin" / "server")
        cur_path = os.environ.get("PATH", "")
        if bin_dir not in cur_path:
            os.environ["PATH"] = f"{bin_dir};{server_dir};" + cur_path

init_py5_runtime()

# -----------------------------------------------------------------------------
# 2. Pseudorandom Number Generator (PRNG)
# -----------------------------------------------------------------------------
class Prng:
    """
    Blum-Blum-Shub / Lehmer PRNG faithful to shanshui/index.html's PRNG implementation.
    """
    def __init__(self, seed: Optional[Union[int, str]] = 1234):
        self.p = 999979
        self.q = 999983
        self.m = self.p * self.q
        self.s = 1234
        self.seed(seed)

    def hash_str(self, x: str) -> int:
        z = 0
        for i, char in enumerate(str(x)):
            z += ord(char) * (128 ** (i % 8))
        return z

    def seed(self, x: Optional[Union[int, str]] = None):
        if x is None:
            x = random.randint(100000, 999999999)
        if isinstance(x, str):
            h = self.hash_str(x)
        else:
            h = int(x)

        y = 0
        z = 0
        while y % self.p == 0 or y % self.q == 0 or y == 0 or y == 1:
            y = (h + z) % self.m
            z += 1
        self.s = y
        for _ in range(10):
            self.next()

    def next(self) -> float:
        self.s = (self.s * self.s) % self.m
        return self.s / self.m

    def random(self) -> float:
        return self.next()

# Default global PRNG instance
_PRNG = Prng(1234)

def set_seed(s: Union[int, str]):
    _PRNG.seed(s)
    random.seed(s)

def rand() -> float:
    return _PRNG.next()

# -----------------------------------------------------------------------------
# 3. Processing-Compatible 3D Perlin Noise
# -----------------------------------------------------------------------------
class PerlinNoise:
    """
    Self-contained 3D Perlin Noise matching p5.js / Processing 4 noise calculation.
    """
    PERLIN_YWRAPB = 4
    PERLIN_YWRAP = 1 << PERLIN_YWRAPB
    PERLIN_ZWRAPB = 8
    PERLIN_ZWRAP = 1 << PERLIN_ZWRAPB
    PERLIN_SIZE = 4095

    def __init__(self, seed: Optional[int] = None):
        self.perlin_octaves = 4
        self.perlin_amp_falloff = 0.5
        self.perlin: Optional[List[float]] = None
        self.noise_seed(seed if seed is not None else 12345)

    @staticmethod
    def _scaled_cosine(i: float) -> float:
        return 0.5 * (1.0 - math.cos(i * math.pi))

    def noise_seed(self, seed: int):
        m = 4294967296
        a = 1664525
        c = 1013904223
        z = seed & 0xFFFFFFFF

        def lcg_rand():
            nonlocal z
            z = (a * z + c) % m
            return z / m

        self.perlin = [lcg_rand() for _ in range(self.PERLIN_SIZE + 1)]

    def noise(self, x: float, y: float = 0.0, z: float = 0.0) -> float:
        if self.perlin is None:
            self.noise_seed(12345)

        x = abs(x)
        y = abs(y)
        z = abs(z)

        xi = int(math.floor(x))
        yi = int(math.floor(y))
        zi = int(math.floor(z))

        xf = x - xi
        yf = y - yi
        zf = z - zi

        r = 0.0
        ampl = 0.5

        for _ in range(self.perlin_octaves):
            of = xi + (yi << self.PERLIN_YWRAPB) + (zi << self.PERLIN_ZWRAPB)
            rxf = self._scaled_cosine(xf)
            ryf = self._scaled_cosine(yf)

            n1 = self.perlin[of & self.PERLIN_SIZE]
            n1 += rxf * (self.perlin[(of + 1) & self.PERLIN_SIZE] - n1)
            n2 = self.perlin[(of + self.PERLIN_YWRAP) & self.PERLIN_SIZE]
            n2 += rxf * (self.perlin[(of + self.PERLIN_YWRAP + 1) & self.PERLIN_SIZE] - n2)
            n1 += ryf * (n2 - n1)

            of += self.PERLIN_ZWRAP
            n2 = self.perlin[of & self.PERLIN_SIZE]
            n2 += rxf * (self.perlin[(of + 1) & self.PERLIN_SIZE] - n2)
            n3 = self.perlin[(of + self.PERLIN_YWRAP) & self.PERLIN_SIZE]
            n3 += rxf * (self.perlin[(of + self.PERLIN_YWRAP + 1) & self.PERLIN_SIZE] - n3)
            n2 += ryf * (n3 - n2)

            n1 += self._scaled_cosine(zf) * (n2 - n1)
            r += n1 * ampl
            ampl *= self.perlin_amp_falloff

            xi <<= 1
            xf *= 2
            yi <<= 1
            yf *= 2
            zi <<= 1
            zf *= 2

            if xf >= 1.0:
                xi += 1
                xf -= 1.0
            if yf >= 1.0:
                yi += 1
                yf -= 1.0
            if zf >= 1.0:
                zi += 1
                zf -= 1.0

        return r

# Default global noise instance
_NOISE = PerlinNoise(42)

def noise(x: float, y: float = 0.0, z: float = 0.0) -> float:
    return _NOISE.noise(x, y, z)

def noise_seed(seed: int):
    _NOISE.noise_seed(seed)

# -----------------------------------------------------------------------------
# 4. Color Parsing & Conversion Utility
# -----------------------------------------------------------------------------
def parse_color(col: Union[str, tuple, list]) -> Tuple[int, int, int, int]:
    """
    Parses CSS color strings ('rgba(...)', 'rgb(...)', 'white', 'none')
    or color tuples into (r, g, b, a) in range [0, 255].
    """
    if isinstance(col, (tuple, list)):
        if len(col) == 3:
            return (int(col[0]), int(col[1]), int(col[2]), 255)
        elif len(col) >= 4:
            a = col[3]
            a_val = int(a * 255) if isinstance(a, float) and a <= 1.0 else int(a)
            return (int(col[0]), int(col[1]), int(col[2]), a_val)

    if not isinstance(col, str):
        return (0, 0, 0, 255)

    s = col.strip().lower()
    if s in ("none", "transparent", ""):
        return (0, 0, 0, 0)
    if s == "white":
        return (255, 255, 255, 255)
    if s == "black":
        return (0, 0, 0, 255)
    if s == "red":
        return (255, 0, 0, 255)
    if s == "green":
        return (0, 255, 0, 255)

    m = re.match(r"rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*([0-9.]+))?\s*\)", s)
    if m:
        r = int(float(m.group(1)))
        g = int(float(m.group(2)))
        b = int(float(m.group(3)))
        a_str = m.group(4)
        if a_str is not None:
            a = float(a_str)
            a_val = int(a * 255) if a <= 1.0 else int(a)
        else:
            a_val = 255
        return (r, g, b, a_val)

    if s.startswith("#"):
        hex_s = s.lstrip("#")
        if len(hex_s) == 6:
            r = int(hex_s[0:2], 16)
            g = int(hex_s[2:4], 16)
            b = int(hex_s[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_s) == 8:
            r = int(hex_s[0:2], 16)
            g = int(hex_s[2:4], 16)
            b = int(hex_s[4:6], 16)
            a = int(hex_s[6:8], 16)
            return (r, g, b, a)

    return (100, 100, 100, 255)

# -----------------------------------------------------------------------------
# 5. Core Math & Sampling Helpers
# -----------------------------------------------------------------------------
def distance(p0: Tuple[float, float], p1: Tuple[float, float]) -> float:
    return math.hypot(p1[0] - p0[0], p1[1] - p0[1])

def mapval(val: float, istart: float, istop: float, ostart: float, ostop: float) -> float:
    if istop == istart:
        return ostart
    return ostart + (ostop - ostart) * ((val - istart) / (istop - istart))

def rand_choice(arr: list):
    return random.choice(arr)

def norm_rand(m: float, M: float) -> float:
    return m + random.random() * (M - m)

def wtrand(func: Callable[[float], float]) -> float:
    """Rejection sampling against arbitrary probability density function."""
    for _ in range(1000):
        x = random.random()
        y = random.random()
        if y < func(x):
            return x
    return x

def rand_gaussian() -> float:
    """Bounded gaussian-like distribution matching Lingdong Huang's Shan Shui engine."""
    return (
        wtrand(lambda x: math.exp(-24.0 * math.pow(x - 0.5, 2))) * 2.0 - 1.0
    )

def loop_noise(nslist: List[float]):
    """Loop noise array smoothly so beginning and end join without seam."""
    n = len(nslist)
    if n == 0:
        return
    half = n // 2
    for i in range(half):
        p = i / half
        nslist[i] = nslist[i] * (1.0 - p) + nslist[i + half] * p

def bezmh(P: List[Tuple[float, float]], w: float = 1.0) -> List[Tuple[float, float]]:
    """Bezier midpoint smoothing algorithm."""
    if len(P) < 2:
        return P[:]
    out = [P[0]]
    for i in range(len(P) - 1):
        p0 = P[i]
        p1 = P[i + 1]
        mx = (p0[0] + p1[0]) * 0.5
        my = (p0[1] + p1[1]) * 0.5
        out.append((mx, my))
    out.append(P[-1])
    return out

# -----------------------------------------------------------------------------
# 6. PolyTools (Computational Geometry & Triangulation Engine)
# -----------------------------------------------------------------------------
class PolyTools:
    """
    Geometric utility class matching shanshui/index.html's PolyTools.
    Handles segment intersection, ray-casting point containment,
    ear-clipping triangulation, and recursive triangle shattering.
    """
    @staticmethod
    def mid_pt(*args) -> Tuple[float, float]:
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            plist = args[0]
        else:
            plist = args
        if not plist:
            return (0.0, 0.0)
        sx = sum(p[0] for p in plist)
        sy = sum(p[1] for p in plist)
        n = float(len(plist))
        return (sx / n, sy / n)

    @staticmethod
    def line_expr(pt0: Tuple[float, float], pt1: Tuple[float, float]) -> Tuple[float, float]:
        den = pt1[0] - pt0[0]
        m = float("inf") if den == 0 else (pt1[1] - pt0[1]) / den
        k = pt0[1] - m * pt0[0]
        return (m, k)

    @staticmethod
    def intersect(ln0: Tuple[Tuple[float, float], Tuple[float, float]],
                  ln1: Tuple[Tuple[float, float], Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        den0 = ln0[1][0] - ln0[0][0]
        den1 = ln1[1][0] - ln1[0][0]

        # Handle vertical lines
        if den0 == 0 and den1 == 0:
            return None
        if den0 == 0:
            x = ln0[0][0]
            m1 = (ln1[1][1] - ln1[0][1]) / den1
            k1 = ln1[0][1] - m1 * ln1[0][0]
            y = m1 * x + k1
        elif den1 == 0:
            x = ln1[0][0]
            m0 = (ln0[1][1] - ln0[0][1]) / den0
            k0 = ln0[0][1] - m0 * ln0[0][0]
            y = m0 * x + k0
        else:
            m0 = (ln0[1][1] - ln0[0][1]) / den0
            k0 = ln0[0][1] - m0 * ln0[0][0]
            m1 = (ln1[1][1] - ln1[0][1]) / den1
            k1 = ln1[0][1] - m1 * ln1[0][0]
            den = m0 - m1
            if abs(den) < 1e-9:
                return None
            x = (k1 - k0) / den
            y = m0 * x + k0

        def on_seg(p, ln):
            eps = 1e-4
            return (
                min(ln[0][0], ln[1][0]) - eps <= p[0] <= max(ln[0][0], ln[1][0]) + eps and
                min(ln[0][1], ln[1][1]) - eps <= p[1] <= max(ln[0][1], ln[1][1]) + eps
            )

        if on_seg((x, y), ln0) and on_seg((x, y), ln1):
            return (x, y)
        return None

    @classmethod
    def pt_in_poly(cls, pt: Tuple[float, float], plist: List[Tuple[float, float]]) -> bool:
        inside = False
        n = len(plist)
        x, y = pt
        for i in range(n):
            p1 = plist[i]
            p2 = plist[(i + 1) % n]
            if (p1[1] > y) != (p2[1] > y):
                x_inters = (p2[0] - p1[0]) * (y - p1[1]) / (p2[1] - p1[1]) + p1[0]
                if x < x_inters:
                    inside = not inside
        return inside

    @classmethod
    def ln_in_poly(cls, ln: Tuple[Tuple[float, float], Tuple[float, float]],
                   plist: List[Tuple[float, float]]) -> bool:
        ep = 0.01
        lnc = (
            (ln[0][0] * (1.0 - ep) + ln[1][0] * ep, ln[0][1] * (1.0 - ep) + ln[1][1] * ep),
            (ln[0][0] * ep + ln[1][0] * (1.0 - ep), ln[0][1] * ep + ln[1][1] * (1.0 - ep))
        )
        n = len(plist)
        for i in range(n):
            pt = plist[i]
            np = plist[(i + 1) % n]
            if cls.intersect(lnc, (pt, np)) is not None:
                return False
        mid = cls.mid_pt(ln[0], ln[1])
        return cls.pt_in_poly(mid, plist)

    @staticmethod
    def sides_of(plist: List[Tuple[float, float]]) -> List[float]:
        slist = []
        n = len(plist)
        for i in range(n):
            pt = plist[i]
            np = plist[(i + 1) % n]
            slist.append(math.hypot(np[0] - pt[0], np[1] - pt[1]))
        return slist

    @classmethod
    def area_of(cls, plist: List[Tuple[float, float]]) -> float:
        if len(plist) < 3:
            return 0.0
        if len(plist) == 3:
            slist = cls.sides_of(plist)
            a, b, c = slist[0], slist[1], slist[2]
            s = (a + b + c) * 0.5
            val = s * (s - a) * (s - b) * (s - c)
            return math.sqrt(max(0.0, val))
        # Shoelace formula for arbitrary polygon
        area = 0.0
        n = len(plist)
        for i in range(n):
            j = (i + 1) % n
            area += plist[i][0] * plist[j][1] - plist[j][0] * plist[i][1]
        return abs(area) * 0.5

    @classmethod
    def sliver_ratio(cls, plist: List[Tuple[float, float]]) -> float:
        a = cls.area_of(plist)
        p = sum(cls.sides_of(plist))
        return a / p if p > 0 else 0.0

    @classmethod
    def best_ear(cls, plist: List[Tuple[float, float]],
                 convex: bool = False, optimize: bool = True):
        cuts = []
        n = len(plist)
        for i in range(n):
            pt = plist[i]
            lp = plist[(i - 1 + n) % n]
            np = plist[(i + 1) % n]
            qlist = [plist[k] for k in range(n) if k != i]
            if convex or cls.ln_in_poly((lp, np), plist):
                c = ([lp, pt, np], qlist)
                if not optimize:
                    return c
                cuts.append(c)

        best = (plist, [])
        best_ratio = -1.0
        for ear, rem in cuts:
            r = cls.sliver_ratio(ear)
            if r >= best_ratio:
                best = (ear, rem)
                best_ratio = r
        return best

    @classmethod
    def shatter(cls, plist: List[Tuple[float, float]], a: float) -> List[List[Tuple[float, float]]]:
        if len(plist) < 3:
            return []
        if cls.area_of(plist) < a:
            return [plist]
        slist = cls.sides_of(plist)
        # Find longest side
        ind = 0
        max_s = slist[0]
        for i, s in enumerate(slist):
            if s > max_s:
                max_s = s
                ind = i
        n = len(plist)
        nind = (ind + 1) % n
        lind = (ind + 2) % n
        mid = cls.mid_pt(plist[ind], plist[nind])
        return (
            cls.shatter([plist[ind], mid, plist[lind]], a) +
            cls.shatter([plist[lind], plist[nind], mid], a)
        )

    @classmethod
    def triangulate(cls, plist: List[Tuple[float, float]],
                    area: float = 100.0, convex: bool = False, optimize: bool = True) -> List[List[Tuple[float, float]]]:
        if len(plist) <= 3:
            return cls.shatter(plist, area)
        cut_ear, remaining = cls.best_ear(plist, convex=convex, optimize=optimize)
        if not remaining:
            return cls.shatter(plist, area)
        return cls.shatter(cut_ear, area) + cls.triangulate(remaining, area=area, convex=convex, optimize=optimize)

# -----------------------------------------------------------------------------
# 7. Retained Graphic Primitives (Poly, Stroke, Blob, Div, Texture)
# -----------------------------------------------------------------------------
class PolyPrimitive:
    """
    Representation of a 2D filled and/or stroked polygon.
    Can be rendered to a Py5 context or graphics buffer.
    """
    __slots__ = ("points", "fill_col", "stroke_col", "stroke_weight")

    def __init__(self, points: List[Tuple[float, float]],
                 fill_col: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 stroke_col: Tuple[int, int, int, int] = (0, 0, 0, 0),
                 stroke_weight: float = 0.0):
        self.points = points
        self.fill_col = fill_col
        self.stroke_col = stroke_col
        self.stroke_weight = stroke_weight

    def draw(self, g):
        """Draws this polygon into a Py5 sketch or Py5Graphics instance."""
        if not self.points:
            return
        if self.fill_col[3] > 0:
            g.fill(self.fill_col[0], self.fill_col[1], self.fill_col[2], self.fill_col[3])
        else:
            g.no_fill()

        if self.stroke_weight > 0 and self.stroke_col[3] > 0:
            g.stroke(self.stroke_col[0], self.stroke_col[1], self.stroke_col[2], self.stroke_col[3])
            g.stroke_weight(self.stroke_weight)
        else:
            g.no_stroke()

        g.begin_shape()
        for pt in self.points:
            g.vertex(pt[0], pt[1])
        if self.fill_col[3] > 0:
            g.end_shape(g.CLOSE)
        else:
            g.end_shape()

def poly(plist: List[Tuple[float, float]],
         xof: float = 0.0, yof: float = 0.0,
         fil: Union[str, tuple] = (0, 0, 0, 0),
         str_: Optional[Union[str, tuple]] = None,
         wid: float = 0.0) -> List[PolyPrimitive]:
    """Generates a closed polygon primitive."""
    fill_col = parse_color(fil)
    stroke_col = parse_color(str_) if str_ is not None else fill_col
    shifted = [(p[0] + xof, p[1] + yof) for p in plist]
    return [PolyPrimitive(shifted, fill_col=fill_col, stroke_col=stroke_col, stroke_weight=wid)]

def stroke(ptlist: List[Tuple[float, float]],
           xof: float = 0.0, yof: float = 0.0,
           wid: float = 2.0,
           col: Union[str, tuple] = (200, 200, 200, 230),
           noi: float = 0.5,
           out: float = 1.0,
           fun: Optional[Callable[[float], float]] = None) -> List[PolyPrimitive]:
    """
    Calligraphic ink brush stroke simulator.
    Evaluates normal offsets along a polyline spine, modulates width with Perlin noise
    to mimic split bristles (feibai), and builds a smooth 2D ribbon mesh polygon.
    """
    if len(ptlist) < 2:
        return []
    if fun is None:
        fun = lambda x: math.sin(x * math.pi)

    color_tuple = parse_color(col)
    vtxlist0 = []
    vtxlist1 = []
    n0 = random.random() * 10.0
    n = len(ptlist)

    for i in range(1, n - 1):
        t = i / float(n)
        w = wid * fun(t)
        w = w * (1.0 - noi) + w * noi * noise(i * 0.5, n0)

        dx1 = ptlist[i][0] - ptlist[i - 1][0]
        dy1 = ptlist[i][1] - ptlist[i - 1][1]
        dx2 = ptlist[i][0] - ptlist[i + 1][0]
        dy2 = ptlist[i][1] - ptlist[i + 1][1]

        a1 = math.atan2(dy1, dx1)
        a2 = math.atan2(dy2, dx2)
        a = (a1 + a2) * 0.5
        if a < a2:
            a += math.pi

        vtxlist0.append((ptlist[i][0] + w * math.cos(a), ptlist[i][1] + w * math.sin(a)))
        vtxlist1.append((ptlist[i][0] - w * math.cos(a), ptlist[i][1] - w * math.sin(a)))

    ribbon = [ptlist[0]] + vtxlist0 + list(reversed(vtxlist1 + [ptlist[-1]])) + [ptlist[0]]
    shifted = [(p[0] + xof, p[1] + yof) for p in ribbon]
    return [PolyPrimitive(shifted, fill_col=color_tuple, stroke_col=color_tuple, stroke_weight=out)]

def blob(x: float, y: float,
         length: float = 20.0, wid: float = 5.0, ang: float = 0.0,
         col: Union[str, tuple] = (200, 200, 200, 230),
         noi: float = 0.5,
         fun: Optional[Callable[[float], float]] = None) -> List[PolyPrimitive]:
    """Generates an organic droplet/leaf polygon with noise perimeter."""
    if fun is None:
        fun = lambda x: math.pow(math.sin(x * math.pi), 0.5) if x <= 1.0 else -math.pow(math.sin((x + 1.0) * math.pi), 0.5)

    reso = 20
    lalist = []
    for i in range(reso + 1):
        p = (i / float(reso)) * 2.0
        xo = length * 0.5 - abs(p - 1.0) * length
        yo = (fun(p) * wid) * 0.5
        a = math.atan2(yo, xo)
        l = math.hypot(xo, yo)
        lalist.append((l, a))

    n0 = random.random() * 10.0
    nslist = [noise(i * 0.05, n0) for i in range(reso + 1)]
    loop_noise(nslist)

    plist = []
    for i in range(len(lalist)):
        ns = nslist[i] * noi + (1.0 - noi)
        nx = x + math.cos(lalist[i][1] + ang) * lalist[i][0] * ns
        ny = y + math.sin(lalist[i][1] + ang) * lalist[i][0] * ns
        plist.append((nx, ny))

    color_tuple = parse_color(col)
    return [PolyPrimitive(plist, fill_col=color_tuple, stroke_col=color_tuple, stroke_weight=0.0)]

def div(plist: List[Tuple[float, float]], reso: int) -> List[Tuple[float, float]]:
    """Polyline subdivision for adding fine detail and smoothing."""
    if len(plist) < 2 or reso <= 1:
        return plist[:]
    total = (len(plist) - 1) * reso
    rlist = []
    for i in range(total):
        idx = i // reso
        p = (i % reso) / float(reso)
        p0 = plist[idx]
        p1 = plist[idx + 1]
        nx = p0[0] * (1.0 - p) + p1[0] * p
        ny = p0[1] * (1.0 - p) + p1[1] * p
        rlist.append((nx, ny))
    rlist.append(plist[-1])
    return rlist

def texture(ptlist: List[List[Tuple[float, float]]],
            xof: float = 0.0, yof: float = 0.0,
            tex: int = 400,
            wid: float = 1.5,
            length: float = 0.2,
            sha: int = 0,
            noi_fn: Optional[Callable[[float], float]] = None,
            col_fn: Optional[Callable[[float], str]] = None,
            dis_fn: Optional[Callable[[], float]] = None) -> List[PolyPrimitive]:
    """
    Chinese landscape texturing (cunfa 皴法).
    Emits hundreds of directional, noise-modulated calligraphic brush strokes across
    the terrain contour mesh, complete with shadow passes and subtle ink washes.
    """
    if not ptlist or not ptlist[0]:
        return []

    if noi_fn is None:
        noi_fn = lambda x: 30.0 / x if x != 0 else 30.0
    if col_fn is None:
        col_fn = lambda t: f"rgba(100,100,100,{(random.random() * 0.3):.3f})"
    if dis_fn is None:
        dis_fn = lambda: (random.random() / 3.0) if random.random() > 0.5 else (2.0 / 3.0 + random.random() / 3.0)

    rows = len(ptlist)
    cols = len(ptlist[0])
    texlist: List[List[Tuple[float, float]]] = []

    for i in range(tex):
        mid = int(dis_fn() * cols)
        hlen = int(random.random() * (cols * length))
        start = max(0, min(cols, mid - hlen))
        end = max(0, min(cols, mid + hlen))

        layer = (i / float(tex)) * (rows - 1)
        r_floor = int(math.floor(layer))
        r_ceil = min(rows - 1, int(math.ceil(layer)))
        p = layer - r_floor

        stroke_pts = []
        for j in range(start, end):
            x = ptlist[r_floor][j][0] * (1.0 - p) + ptlist[r_ceil][j][0] * p
            y = ptlist[r_floor][j][1] * (1.0 - p) + ptlist[r_ceil][j][1] * p
            n_scale = noi_fn(layer + 1.0)
            ns0 = n_scale * (noise(x, j * 0.5) - 0.5)
            ns1 = n_scale * (noise(y, j * 0.5) - 0.5)
            stroke_pts.append((x + ns0, y + ns1))

        if len(stroke_pts) >= 2:
            texlist.append(stroke_pts)

    primitives: List[PolyPrimitive] = []

    # Optional shadow pass
    if sha > 0:
        step = 1 + (1 if sha != 0 else 0)
        for j in range(0, len(texlist), step):
            primitives.extend(
                stroke(texlist[j], xof=xof, yof=yof,
                       col="rgba(100,100,100,0.1)", wid=float(sha))
            )

    # Main texture pass
    step = 1 + sha
    total = len(texlist)
    for j in range(sha, total, step):
        t_norm = j / float(total) if total > 0 else 0.5
        c = col_fn(t_norm)
        primitives.extend(
            stroke(texlist[j], xof=xof, yof=yof, col=c, wid=wid)
        )

    return primitives
