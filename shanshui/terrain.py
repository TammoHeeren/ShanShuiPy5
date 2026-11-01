"""
terrain.py - Mountain generation, peak styles, water, and procedural scene planner
Faithful reproduction of Mount.*, water, and mountplanner from shanshui/index.html.
"""

import math
import random
from typing import List, Tuple, Optional, Callable, Dict, Any

from .utils import (
    PolyPrimitive, PolyTools, poly, stroke, div, texture,
    noise, rand_choice, norm_rand, distance
)
from .flora import (
    tree01, tree02, tree03, tree04, tree05, tree06, tree07, tree08
)
from .architecture import (
    arch01, arch02, arch03, arch04, boat01, transmission_tower01
)

# -----------------------------------------------------------------------------
# 1. Mountain Foot Blending
# -----------------------------------------------------------------------------
def foot(ptlist: List[List[Tuple[float, float]]],
         xof: float = 0.0, yof: float = 0.0) -> List[PolyPrimitive]:
    """Generates soft mist contour strokes at the foot of a mountain to blend with water."""
    ftlist: List[List[Tuple[float, float]]] = []
    span = 10
    ni = 0
    prims: List[PolyPrimitive] = []

    for i in range(len(ptlist) - 2):
        if i == ni:
            ni = min(ni + random.choice([1, 2]), len(ptlist) - 1)
            ftlist.append([])
            ftlist.append([])
            sample_len = int(min(len(ptlist[i]) / 8.0, 10))

            for j in range(sample_len):
                ftlist[-2].append((
                    ptlist[i][j][0] + noise(j * 0.1, float(i)) * 10.0,
                    ptlist[i][j][1]
                ))
                ftlist[-1].append((
                    ptlist[i][len(ptlist[i]) - 1 - j][0] - noise(j * 0.1, float(i)) * 10.0,
                    ptlist[i][len(ptlist[i]) - 1 - j][1]
                ))

            ftlist[-2].reverse()
            ftlist[-1].reverse()

            for j in range(span):
                p = j / float(span)
                x1 = ptlist[i][0][0] * (1.0 - p) + ptlist[ni][0][0] * p
                y1 = ptlist[i][0][1] * (1.0 - p) + ptlist[ni][0][1] * p
                x2 = ptlist[i][-1][0] * (1.0 - p) + ptlist[ni][-1][0] * p
                y2 = ptlist[i][-1][1] * (1.0 - p) + ptlist[ni][-1][1] * p

                vib = -1.7 * (p - 1.0) * math.pow(max(0.0, p), 1.0 / 5.0)
                y1 += vib * 5.0 + noise(xof * 0.05, float(i)) * 5.0
                y2 += vib * 5.0 + noise(xof * 0.05, float(i)) * 5.0

                ftlist[-2].append((x1, y1))
                ftlist[-1].append((x2, y2))

    for ft in ftlist:
        prims.extend(poly(ft, xof=xof, yof=yof, fil="white", str_="none"))
        c = f"rgba(100,100,100,{(0.1 + random.random() * 0.1):.3f})"
        prims.extend(stroke([(x[0] + xof, x[1] + yof) for x in ft], col=c, wid=1.0))

    return prims

# -----------------------------------------------------------------------------
# 2. Weathered Rock Boulders
# -----------------------------------------------------------------------------
def rock(xoff: float, yoff: float, seed: float = 0.0,
         hei: float = 80.0, wid: float = 100.0, tex: int = 40,
         sha: int = 10) -> List[PolyPrimitive]:
    """Organic weathered river/cliff boulder with noise deformation and texturing."""
    reso = [10, 50]
    ptlist: List[List[Tuple[float, float]]] = []

    for i in range(reso[0]):
        ptlist.append([])
        nslist = [noise(i, j * 0.2, seed) for j in range(reso[1])]
        from .utils import loop_noise
        loop_noise(nslist)

        for j in range(reso[1]):
            a = (j / float(reso[1])) * math.pi * 2.0 - math.pi * 0.5
            denom = math.sqrt(math.pow(hei * math.cos(a), 2.0) + math.pow(wid * math.sin(a), 2.0))
            l = (wid * hei) / denom if denom > 0 else wid
            l *= 0.7 + 0.3 * nslist[j]

            p = 1.0 - i / float(reso[0])
            nx = math.cos(a) * l * p
            ny = -math.sin(a) * l * p

            if math.pi < a or a < 0:
                ny *= 0.2
            ny += hei * (i / float(reso[0])) * 0.2
            ptlist[-1].append((nx, ny))

    prims: List[PolyPrimitive] = []
    # Solid white backing polygon
    prims.extend(poly(ptlist[0] + [(0.0, 0.0)], xof=xoff, yof=yoff, fil="white", str_="none"))
    # Contour outline stroke
    prims.extend(stroke(
        [(x[0] + xoff, x[1] + yoff) for x in ptlist[0]],
        col="rgba(100,100,100,0.3)", noi=1.0, wid=3.0
    ))
    # Texture hatching
    def dis_fn():
        return (0.15 + 0.15 * random.random()) if random.random() > 0.5 else (0.85 - 0.15 * random.random())

    prims.extend(texture(
        ptlist, xof=xoff, yof=yoff, tex=tex, wid=3.0, sha=sha,
        col_fn=lambda _: f"rgba(180,180,180,{(0.3 + random.random() * 0.3):.3f})",
        dis_fn=dis_fn
    ))
    return prims

# -----------------------------------------------------------------------------
# 3. Primary Mountain Massif (Mountain)
# -----------------------------------------------------------------------------
def mountain(xoff: float, yoff: float, seed: float = 0.0,
             hei: Optional[float] = None, wid: Optional[float] = None,
             tex: int = 200, veg: bool = True) -> List[PolyPrimitive]:
    """
    Primary layered mountain peak deformed by cosine curves and 3D Perlin noise.
    Includes white background occlusion hull, foot mist, cunfa texture strokes,
    and rule-based vegetation/architecture placement.
    """
    if hei is None:
        hei = 100.0 + random.random() * 400.0
    if wid is None:
        wid = 400.0 + random.random() * 200.0

    reso = [10, 50]
    ptlist: List[List[Tuple[float, float]]] = []
    hoff = 0.0

    for j in range(reso[0]):
        hoff += (random.random() * yoff) / 100.0
        ptlist.append([])
        for i in range(reso[1]):
            x = (i / float(reso[1]) - 0.5) * math.pi
            y = math.cos(x)
            y *= noise(x + 10.0, j * 0.15, seed)
            p = 1.0 - j / float(reso[0])
            ptlist[-1].append((
                (x / math.pi) * wid * p,
                -y * hei * p + hoff
            ))

    prims: List[PolyPrimitive] = []

    def vegetate(tree_func: Callable[[float, float], List[PolyPrimitive]],
                 growth_rule: Callable[[int, int], bool],
                 proof_rule: Callable[[List[Tuple[float, float]], int], bool] = lambda *_: True):
        veglist: List[Tuple[float, float]] = []
        for r_idx in range(len(ptlist)):
            for c_idx in range(len(ptlist[r_idx])):
                if growth_rule(r_idx, c_idx):
                    veglist.append(ptlist[r_idx][c_idx])
        for idx, pt in enumerate(veglist):
            if proof_rule(veglist, idx):
                prims.extend(tree_func(pt[0], pt[1]))

    # 1. Rim foliage
    vegetate(
        lambda vx, vy: tree02(
            vx + xoff, vy + yoff - 5.0,
            col=f"rgba(100,100,100,{(noise(0.01 * vx, 0.01 * vy) * 0.15 + 0.5):.3f})",
            clu=2
        ),
        lambda i, j: i == 0 and math.pow(noise(j * 0.1, seed), 3) < 0.1 and abs(ptlist[i][j][1]) / hei > 0.2
    )

    # 2. White backing occlusion hull (occludes everything behind this mountain)
    prims.extend(poly(
        ptlist[0] + [(0.0, reso[0] * 4.0)],
        xof=xoff, yof=yoff, fil="white", str_="none"
    ))

    # 3. Outline stroke
    prims.extend(stroke(
        [(x[0] + xoff, x[1] + yoff) for x in ptlist[0]],
        col="rgba(100,100,100,0.3)", noi=1.0, wid=3.0
    ))

    # 4. Foot contour mist
    prims.extend(foot(ptlist, xof=xoff, yof=yoff))

    # 5. Cunfa texture hatching
    sha_val = random.choice([0, 0, 0, 0, 5])
    prims.extend(texture(ptlist, xof=xoff, yof=yoff, tex=tex, sha=sha_val))

    # 6. Peak-top foliage
    vegetate(
        lambda vx, vy: tree02(
            vx + xoff, vy + yoff,
            col=f"rgba(100,100,100,{(noise(0.01 * vx, 0.01 * vy) * 0.15 + 0.5):.3f})"
        ),
        lambda i, j: math.pow(noise(i * 0.1, j * 0.1, seed + 2.0), 3) < 0.1 and abs(ptlist[i][j][1]) / hei > 0.5
    )

    if veg:
        # Middle forest trees (tree01)
        def middle_proof(vlist, i):
            count = sum(1 for j, pt in enumerate(vlist) if i != j and math.hypot(vlist[i][0] - pt[0], vlist[i][1] - pt[1]) < 30.0)
            return count > 2

        vegetate(
            lambda vx, vy: tree01(
                vx + xoff, vy + yoff,
                hei=((hei + vy) / hei) * 70.0 * (0.3 + random.random() * 0.7),
                wid=random.random() * 3.0 + 1.0,
                col=f"rgba(100,100,100,{(noise(0.01 * vx, 0.01 * vy) * 0.15 + 0.3):.3f})"
            ),
            lambda i, j: (j % 2 == 1) and (math.pow(noise(i * 0.2, j * 0.05, seed), 4) < 0.012) and (abs(ptlist[i][j][1]) / hei < 0.3),
            middle_proof
        )

        # Bottom leaning pine trees (tree03)
        bc = random.random() * 0.1
        vegetate(
            lambda vx, vy: tree03(
                vx + xoff, vy + yoff,
                hei=((hei + vy) / hei) * 120.0 * (0.5 + random.random() * 0.5),
                ben=lambda x: math.pow(x * bc, 1.0),
                col=f"rgba(100,100,100,{(noise(0.01 * vx, 0.01 * vy) * 0.15 + 0.3):.3f})"
            ),
            lambda i, j: (j == 0 or j == len(ptlist[i]) - 1) and (math.pow(noise(i * 0.2, j * 0.05, seed), 4) < 0.012)
        )

    # Bottom architecture (cliffside gazebos / arched bridges)
    def arch_func(vx, vy):
        tt = random.choice([0, 0, 1, 1, 1, 2])
        if tt == 1:
            return arch02(vx + xoff, vy + yoff, seed, wid=norm_rand(40, 70), sto=random.choice([1, 2, 2, 3]), rot=random.random(), sty=random.choice([1, 2, 3]))
        elif tt == 2:
            return arch04(vx + xoff, vy + yoff, seed, sto=random.choice([1, 1, 1, 2, 2]))
        return []

    vegetate(
        arch_func,
        lambda i, j: i != 0 and (j == 1 or j == len(ptlist[i]) - 2) and math.pow(noise(i * 0.2, j * 0.05, seed + 10.0), 4) < 0.008
    )

    # Top pagoda tower (arch03)
    vegetate(
        lambda vx, vy: arch03(vx + xoff, vy + yoff, seed, sto=random.choice([5, 7]), wid=40.0 + random.random() * 20.0),
        lambda i, j: i == 1 and abs(j - len(ptlist[i]) / 2.0) < 1.0 and random.random() < 0.02
    )

    # Power transmission tower easter egg
    vegetate(
        lambda vx, vy: transmission_tower01(vx + xoff, vy + yoff, seed),
        lambda i, j: (i % 2 == 0) and (j == 1 or j == len(ptlist[i]) - 2) and math.pow(noise(i * 0.2, j * 0.05, seed + 20.0 * math.pi), 4) < 0.002
    )

    # Bottom boulders (rock)
    vegetate(
        lambda vx, vy: rock(vx + xoff, vy + yoff, seed, wid=20.0 + random.random() * 20.0, hei=20.0 + random.random() * 20.0, sha=2),
        lambda i, j: (j == 0 or j == len(ptlist[i]) - 1) and random.random() < 0.1
    )

    return prims

# -----------------------------------------------------------------------------
# 4. Terraced Plateau Mountains (FlatMount)
# -----------------------------------------------------------------------------
def flat_mount(xoff: float, yoff: float, seed: float = 0.0,
               hei: Optional[float] = None, wid: Optional[float] = None,
               tex: int = 80, cho: float = 0.5) -> List[PolyPrimitive]:
    """Table mountain / terraced plateau populated with rocks, cottages, and trees."""
    if hei is None:
        hei = 40.0 + random.random() * 400.0
    if wid is None:
        wid = 400.0 + random.random() * 200.0

    reso = [5, 50]
    hoff = 0.0
    ptlist: List[List[Tuple[float, float]]] = []
    flat: List[List[Tuple[float, float]]] = []

    for j in range(reso[0]):
        hoff += (random.random() * yoff) / 100.0
        ptlist.append([])
        flat.append([])
        for i in range(reso[1]):
            x = (i / float(reso[1]) - 0.5) * math.pi
            y = math.cos(x * 2.0) + 1.0
            y *= noise(x + 10.0, j * 0.1, seed)
            p = 1.0 - (j / float(reso[0])) * 0.6
            nx = (x / math.pi) * wid * p
            ny = -y * hei * p + hoff
            h = 100.0
            if ny < -h * cho + hoff:
                ny = -h * cho + hoff
                if len(flat[-1]) % 2 == 0:
                    flat[-1].append((nx, ny))
            else:
                if len(flat[-1]) % 2 == 1:
                    flat[-1].append(ptlist[-1][-1])
            ptlist[-1].append((nx, ny))

    prims: List[PolyPrimitive] = []
    # White occlusion hull
    prims.extend(poly(ptlist[0] + [(0.0, reso[0] * 4.0)], xof=xoff, yof=yoff, fil="white", str_="none"))
    # Outline stroke
    prims.extend(stroke([(x[0] + xoff, x[1] + yoff) for x in ptlist[0]], col="rgba(100,100,100,0.3)", noi=1.0, wid=3.0))

    # Texture pass
    def dis_fn():
        return (0.1 + 0.4 * random.random()) if random.random() > 0.5 else (0.9 - 0.4 * random.random())

    prims.extend(texture(ptlist, xof=xoff, yof=yoff, tex=tex, wid=2.0, dis_fn=dis_fn))

    # Extract plateau terrace bounds
    grlist1: List[Tuple[float, float]] = []
    grlist2: List[Tuple[float, float]] = []
    for i in range(0, len(flat), 2):
        if len(flat[i]) >= 2:
            grlist1.append(flat[i][0])
            grlist2.append(flat[i][-1])

    if not grlist1:
        return prims

    wb = (grlist1[0][0], grlist2[0][0])
    for i in range(3):
        p = 0.8 - i * 0.2
        grlist1.insert(0, (wb[0] * p, grlist1[0][1] - 5.0))
        grlist2.insert(0, (wb[1] * p, grlist2[0][1] - 5.0))

    wb_end = (grlist1[-1][0], grlist2[-1][0])
    for i in range(3):
        p = 0.6 - i * i * 0.1
        grlist1.append((wb_end[0] * p, grlist1[-1][1] + 1.0))
        grlist2.append((wb_end[1] * p, grlist2[-1][1] + 1.0))

    d = 5
    grlist1 = div(grlist1, d)
    grlist2 = div(grlist2, d)
    grlist = list(reversed(grlist1)) + grlist2 + [grlist1[0]]

    for i in range(len(grlist)):
        v = (1.0 - abs((i % d) - d * 0.5) / (d * 0.5)) * 0.12
        gx = grlist[i][0] * (1.0 - v + noise(grlist[i][1] * 0.5) * v)
        grlist[i] = (gx, grlist[i][1])

    prims.extend(poly(grlist, xof=xoff, yof=yoff, str_="none", fil="white", wid=2.0))
    prims.extend(stroke([(x[0] + xoff, x[1] + yoff) for x in grlist], wid=3.0, col="rgba(100,100,100,0.2)"))

    # Plateau decorations
    xmin = min(p[0] for p in grlist)
    xmax = max(p[0] for p in grlist)
    ymin = min(p[1] for p in grlist)
    ymax = max(p[1] for p in grlist)

    tt = random.choice([0, 0, 1, 2, 3, 4])
    ymid = (ymin + ymax) * 0.5

    for _ in range(int(random.random() * 5)):
        prims.extend(rock(xoff + norm_rand(xmin, xmax), yoff + ymid + norm_rand(-10, 10) + 10, random.random() * 100, wid=10 + random.random() * 20, hei=10 + random.random() * 20, sha=2))

    for _ in range(random.choice([0, 0, 1, 2])):
        xr = xoff + norm_rand(xmin, xmax)
        yr = yoff + ymid + norm_rand(-5, 5) + 20
        for _ in range(int(2 + random.random() * 3)):
            prims.extend(tree08(xr + min(max(norm_rand(-30, 30), xmin), xmax), yr, hei=60 + random.random() * 40))

    if tt == 0:
        for _ in range(int(random.random() * 3)):
            prims.extend(rock(xoff + norm_rand(xmin, xmax), yoff + ymid + norm_rand(-5, 5) + 20, random.random() * 100, wid=50 + random.random() * 20, hei=40 + random.random() * 20, sha=5))
    elif tt == 1:
        pmin = random.random() * 0.5
        pmax = random.random() * 0.5 + 0.5
        x_start = xmin * (1.0 - pmin) + xmax * pmin
        x_end = xmin * (1.0 - pmax) + xmax * pmax
        step_x = 30.0
        cur_x = x_start
        while cur_x < x_end:
            prims.extend(tree05(xoff + cur_x + 20.0 * norm_rand(-1, 1), yoff + ymid + 20.0, hei=100 + random.random() * 200))
            cur_x += step_x
    elif tt == 2:
        for _ in range(random.choice([1, 1, 1, 1, 2, 2, 3])):
            xr = norm_rand(xmin, xmax)
            yr = ymid
            prims.extend(tree04(xoff + xr, yoff + yr + 20.0))
            for j in range(int(random.random() * 2)):
                prims.extend(rock(xoff + max(xmin, min(xmax, xr + norm_rand(-50, 50))), yoff + yr + norm_rand(-5, 5) + 20, j * random.random() * 100, wid=50 + random.random() * 20, hei=40 + random.random() * 20, sha=5))
    elif tt == 3:
        for _ in range(random.choice([1, 1, 1, 1, 2, 2, 3])):
            prims.extend(tree06(xoff + norm_rand(xmin, xmax), yoff + ymid, hei=60 + random.random() * 60))
    elif tt == 4:
        pmin = random.random() * 0.5
        pmax = random.random() * 0.5 + 0.5
        x_start = xmin * (1.0 - pmin) + xmax * pmin
        x_end = xmin * (1.0 - pmax) + xmax * pmax
        cur_x = x_start
        while cur_x < x_end:
            prims.extend(tree07(xoff + cur_x + 20.0 * norm_rand(-1, 1), yoff + ymid + norm_rand(-1, 1), hei=norm_rand(40, 80)))
            cur_x += 20.0

    for _ in range(int(50 * random.random())):
        rx = norm_rand(xmin, xmax)
        ry = norm_rand(ymin, ymax)
        if PolyTools.pt_in_poly((rx, ry), grlist):
            prims.extend(tree02(xoff + rx, yoff + ry))

    if random.choice([0, 0, 0, 0, 1]) == 1 and tt != 4:
        prims.extend(arch01(xoff + norm_rand(xmin, xmax), yoff + ymid + 20.0, random.random(), wid=norm_rand(160, 200), hei=norm_rand(80, 100)))

    return prims

# -----------------------------------------------------------------------------
# 5. Distant Mountain Silhouettes (DistMount)
# -----------------------------------------------------------------------------
def dist_mount(xoff: float, yoff: float, seed: float = 0.0,
               hei: float = 300.0, len_: float = 2000.0, seg: int = 5) -> List[PolyPrimitive]:
    """Triangulated distant mountain range rendered in soft atmospheric ink washes."""
    span = 10.0
    ptlist: List[List[Tuple[float, float]]] = []
    num_sections = int(len_ / span / seg)

    def top_pt(k):
        p_arg = (math.pi * k) / (len_ / span)
        sin_val = math.pow(max(0.0, math.sin(p_arg)), 0.5)
        y = yoff - hei * noise(k * 0.05, seed) * sin_val
        return (xoff + k * span, y)

    def bot_pt(k):
        p_arg = (math.pi * k) / (len_ / span)
        sin_val = math.pow(max(0.0, math.sin(p_arg)), 1.0)
        y = yoff + 24.0 * noise(k * 0.05, 2.0, seed) * sin_val
        return (xoff + k * span, y)

    for i in range(num_sections):
        k_start = i * seg
        k_end = (i + 1) * seg
        top_pts = [top_pt(k) for k in range(k_start, k_end + 1)]
        bot_pts = [bot_pt(k) for k in range(k_end, k_start - 1, -1)]
        ptlist.append(top_pts + bot_pts)

    prims: List[PolyPrimitive] = []

    def get_col(x, y):
        c = int(noise(x * 0.02, y * 0.02, yoff) * 55.0 + 200.0)
        return f"rgb({c},{c},{c})"

    for poly_pts in ptlist:
        if len(poly_pts) < 3:
            continue
        col_str = get_col(poly_pts[-1][0], poly_pts[-1][1])
        prims.extend(poly(poly_pts, fil=col_str, str_="none", wid=1.0))

        triangles = PolyTools.triangulate(poly_pts, area=100.0, convex=True, optimize=False)
        for tri in triangles:
            m = PolyTools.mid_pt(tri)
            co = get_col(m[0], m[1])
            prims.extend(poly(tri, fil=co, str_=co, wid=1.0))

    return prims

# -----------------------------------------------------------------------------
# 6. Procedural Water Ripples
# -----------------------------------------------------------------------------
def water(xoff: float, yoff: float, seed: float = 0.0,
          hei: float = 2.0, len_: float = 800.0, clu: int = 10) -> List[PolyPrimitive]:
    """Horizontal wave strokes clustering beneath mountain bases."""
    prims: List[PolyPrimitive] = []
    ptlist: List[List[Tuple[float, float]]] = []
    yk = 0.0

    for _ in range(clu):
        ptlist.append([])
        xk = (random.random() - 0.5) * (len_ / 8.0)
        yk += random.random() * 5.0
        lk = len_ / 4.0 + random.random() * (len_ / 4.0)
        reso = 5.0
        j = -lk
        while j < lk:
            ptlist[-1].append((
                j + xk,
                math.sin(j * 0.2) * hei * noise(j * 0.1) - 20.0 + yk
            ))
            j += reso

    for j in range(1, len(ptlist)):
        c = f"rgba(100,100,100,{(0.3 + random.random() * 0.3):.3f})"
        shifted = [(x[0] + xoff, x[1] + yoff) for x in ptlist[j]]
        prims.extend(stroke(shifted, col=c, wid=1.0))

    return prims

# -----------------------------------------------------------------------------
# 7. Procedural Landscape Scene Planner (MountPlanner)
# -----------------------------------------------------------------------------
class MountPlanner:
    """
    Infinite horizontal procedural scene planner matching mountplanner from shanshui/index.html.
    Evaluates noise fields, detects local maxima, maintains minimum clearance buffers,
    and returns scheduled scene items tagged with their coordinates and styles.
    """
    def __init__(self):
        self.planmtx: Dict[int, int] = {}

    def plan_chunk(self, xmin: float, xmax: float) -> List[Dict[str, Any]]:
        reg: List[Dict[str, Any]] = []
        samp = 0.03
        xstep = 5
        mwid = 200

        ns = lambda x, y: max(0.0, noise(x * samp) - 0.55) * 2.0
        yr = lambda x: noise(x * 0.01, math.pi)

        def locmax(x, y, f, r=2):
            z0 = f(x, y)
            if z0 <= 0.3:
                return False
            for i in range(int(x - r), int(x + r)):
                for j in range(int(y - r), int(y + r)):
                    if f(i, j) > z0:
                        return False
            return True

        def chadd(item: Dict[str, Any], mind: float = 10.0) -> bool:
            for existing in reg:
                if abs(existing["x"] - item["x"]) < mind:
                    return False
            reg.append(item)
            return True

        i = xmin
        while i < xmax:
            i1 = int(math.floor(i / float(xstep)))
            if i1 not in self.planmtx:
                self.planmtx[i1] = 0
            i += xstep

        i = xmin
        while i < xmax:
            j = 0.0
            max_j = yr(i) * 480.0
            while j < max_j:
                if locmax(i, j, ns, 2):
                    xof = i + 2.0 * (random.random() - 0.5) * 500.0
                    yof = j + 300.0
                    item = {"tag": "mount", "x": xof, "y": yof, "h": ns(i, j)}
                    if chadd(item):
                        k_start = int(math.floor((xof - mwid) / float(xstep)))
                        k_end = int((xof + mwid) / float(xstep))
                        for k in range(k_start, k_end):
                            self.planmtx[k] = self.planmtx.get(k, 0) + 1
                j += 30.0

            if abs(i) % 1000 < max(1, xstep - 1):
                chadd({
                    "tag": "distmount",
                    "x": i,
                    "y": 280.0 - random.random() * 50.0,
                    "h": ns(i, j)
                })
            i += xstep

        i = xmin
        while i < xmax:
            i1 = int(math.floor(i / float(xstep)))
            if self.planmtx.get(i1, 0) == 0:
                if random.random() < 0.01:
                    num_flat = int(4 * random.random())
                    for j in range(num_flat):
                        chadd({
                            "tag": "flatmount",
                            "x": i + 2.0 * (random.random() - 0.5) * 700.0,
                            "y": 700.0 - j * 50.0,
                            "h": ns(i, j)
                        })
            i += xstep

        i = xmin
        while i < xmax:
            if random.random() < 0.2:
                chadd({
                    "tag": "boat",
                    "x": i,
                    "y": 300.0 + random.random() * 390.0
                }, mind=400.0)
            i += xstep

        return reg
