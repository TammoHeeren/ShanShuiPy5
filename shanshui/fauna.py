"""
fauna.py - Articulated human figures (travelers, fishermen) and flying birds
Faithful reproduction of Man.man, Man.hat01, Man.hat02, Man.stick01 from shanshui/index.html,
plus ink-wash birds and specialized character poses.
"""

import math
import random
from typing import List, Tuple, Optional, Callable, Dict, Any

from .utils import (
    PolyPrimitive, poly, stroke, bezmh, div,
    noise, distance, norm_rand, rand_gaussian, parse_color
)

def expand(ptlist: List[Tuple[float, float]],
           wfun: Callable[[float], float]) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Expands a polyline into two boundary contour curves using width function wfun."""
    if len(ptlist) < 2:
        return ptlist[:], ptlist[:]

    vtxlist0: List[Tuple[float, float]] = []
    vtxlist1: List[Tuple[float, float]] = []
    n = len(ptlist)

    for i in range(1, n - 1):
        w = wfun(i / float(n))
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

    l = n - 1
    a0 = math.atan2(ptlist[1][1] - ptlist[0][1], ptlist[1][0] - ptlist[0][0]) - math.pi * 0.5
    a1_end = math.atan2(ptlist[l][1] - ptlist[l - 1][1], ptlist[l][0] - ptlist[l - 1][0]) - math.pi * 0.5
    w0 = wfun(0.0)
    w1 = wfun(1.0)

    vtxlist0.insert(0, (ptlist[0][0] + w0 * math.cos(a0), ptlist[0][1] + w0 * math.sin(a0)))
    vtxlist1.insert(0, (ptlist[0][0] - w0 * math.cos(a0), ptlist[0][1] - w0 * math.sin(a0)))
    vtxlist0.append((ptlist[l][0] + w1 * math.cos(a1_end), ptlist[l][1] + w1 * math.sin(a1_end)))
    vtxlist1.append((ptlist[l][0] - w1 * math.cos(a1_end), ptlist[l][1] - w1 * math.sin(a1_end)))

    return vtxlist0, vtxlist1

def tranpoly(p0: Tuple[float, float], p1: Tuple[float, float],
             ptlist: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Transforms local normalized coordinates onto coordinate frame defined by line segment (p0, p1)."""
    plist = [(-v[0], v[1]) for v in ptlist]
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]) - math.pi * 0.5
    scl = distance(p0, p1)
    qlist = []
    for v in plist:
        d = math.hypot(v[0], v[1])
        a = math.atan2(v[1], v[0])
        qlist.append((
            p0[0] + d * scl * math.cos(ang + a),
            p0[1] + d * scl * math.sin(ang + a)
        ))
    return qlist

def flipper(plist: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    return [(-v[0], v[1]) for v in plist]

# -----------------------------------------------------------------------------
# Headgear & Accessories
# -----------------------------------------------------------------------------
def hat01(p0: Tuple[float, float], p1: Tuple[float, float],
          fli: bool = False) -> List[PolyPrimitive]:
    """Conical bamboo hat (douli / kasa) with hanging fringe strings."""
    prims: List[PolyPrimitive] = []
    seed = random.random()
    f = flipper if fli else (lambda x: x)

    crown = [
        (-0.3, 0.5), (0.3, 0.8), (0.2, 1.0), (0.0, 1.1),
        (-0.3, 1.15), (-0.55, 1.0), (-0.65, 0.5)
    ]
    prims.extend(poly(tranpoly(p0, p1, f(crown)), fil="rgba(100,100,100,0.8)"))

    fringe = []
    for i in range(10):
        fringe.append((
            -0.3 - noise(i * 0.2, seed) * i * 0.1,
            0.5 - i * 0.3
        ))
    prims.extend(poly(tranpoly(p0, p1, f(fringe)), str_="rgba(100,100,100,0.8)", wid=1.0))
    return prims

def hat02(p0: Tuple[float, float], p1: Tuple[float, float],
          fli: bool = False) -> List[PolyPrimitive]:
    """Wide-brimmed traditional Chinese hat."""
    f = flipper if fli else (lambda x: x)
    brim = [
        (-0.3, 0.5), (-1.1, 0.5), (-1.2, 0.6), (-1.1, 0.7),
        (-0.3, 0.8), (0.3, 0.8), (1.0, 0.7), (1.3, 0.6),
        (1.2, 0.5), (0.3, 0.5)
    ]
    return poly(tranpoly(p0, p1, f(brim)), fil="rgba(100,100,100,0.8)")

def stick01(p0: Tuple[float, float], p1: Tuple[float, float],
            fli: bool = False) -> List[PolyPrimitive]:
    """Bamboo walking staff with organic noise bending."""
    seed = random.random()
    f = flipper if fli else (lambda x: x)
    qlist1 = []
    l = 12
    for i in range(l):
        qlist1.append((
            -noise(i * 0.1, seed) * 0.1 * math.sin((i / float(l)) * math.pi) * 5.0,
            i * 0.3
        ))
    return poly(tranpoly(p0, p1, f(qlist1)), str_="rgba(100,100,100,0.5)", wid=1.0)

# -----------------------------------------------------------------------------
# Kinematic Human Figure Generator
# -----------------------------------------------------------------------------
# Joint Kinematic Tree:
#      2 (head)
#    1/  (neck)
# 7/  | \_ 6 (arms)
# 8| 0 \ 5
#      /3 (torso/legs)
#     4
SKELETON_TREE = {
    0: {
        1: {
            2: {},
            5: {6: {}},
            7: {8: {}}
        },
        3: {
            4: {}
        }
    }
}

def man(xoff: float, yoff: float,
        sca: float = 0.5,
        hat: Callable = hat01,
        ite: Optional[Callable] = None,
        fli: bool = True,
        ang: Optional[List[float]] = None,
        len_: Optional[List[float]] = None) -> List[PolyPrimitive]:
    """
    Parametric articulated human figure with forward kinematics,
    flowing robes, sleeves, staff, and straw hat.
    """
    if ite is None:
        ite = lambda p0, p1, **kwargs: []
    if ang is None:
        ang = [
            0.0,
            -math.pi * 0.5,
            norm_rand(0.0, 0.0),
            (math.pi / 4.0) * random.random(),
            ((math.pi * 3.0) / 4.0) * random.random(),
            (math.pi * 3.0) / 4.0,
            -math.pi / 4.0,
            (-math.pi * 3.0) / 4.0 - (math.pi / 4.0) * random.random(),
            -math.pi / 4.0
        ]
    if len_ is None:
        len_ = [0.0, 30.0, 20.0, 30.0, 30.0, 30.0, 30.0, 30.0, 30.0]

    scl_len = [v * sca for v in len_]
    prims: List[PolyPrimitive] = []

    def to_global(v: Tuple[float, float]) -> Tuple[float, float]:
        return ((-1.0 if fli else 1.0) * v[0] + xoff, v[1] + yoff)

    def gpar(sct: dict, ind: int):
        for k, v in sct.items():
            if k == ind:
                return [ind]
            r = gpar(v, ind)
            if r is not False:
                return [k] + r
        return False

    def grot(ind: int) -> float:
        par = gpar(SKELETON_TREE, ind)
        rot = 0.0
        if par:
            for node in par:
                rot += ang[node]
        return rot

    def gpos(ind: int) -> Tuple[float, float]:
        par = gpar(SKELETON_TREE, ind)
        pos = [0.0, 0.0]
        if par:
            for node in par:
                a = grot(node)
                pos[0] += scl_len[node] * math.cos(a)
                pos[1] += scl_len[node] * math.sin(a)
        return (pos[0], pos[1])

    pts = [gpos(i) for i in range(len(ang))]
    yoff -= pts[4][1]  # Anchor feet at yoff ground level

    def cloth(plist: List[Tuple[float, float]],
              wfun: Callable[[float], float]) -> List[PolyPrimitive]:
        c_prims: List[PolyPrimitive] = []
        tlist = bezmh(plist, 2.0)
        tlist1, tlist2 = expand(tlist, wfun)
        hull = [to_global(p) for p in (tlist1 + list(reversed(tlist2)))]
        c_prims.extend(poly(hull, fil="white"))
        c_prims.extend(stroke([to_global(p) for p in tlist1], wid=1.0, col="rgba(100,100,100,0.5)"))
        c_prims.extend(stroke([to_global(p) for p in tlist2], wid=1.0, col="rgba(100,100,100,0.6)"))
        return c_prims

    fsleeve = lambda x: sca * 8.0 * (math.sin(0.5 * x * math.pi) * math.pow(max(0.0, math.sin(x * math.pi)), 0.1) + (1.0 - x) * 0.4)
    fbody = lambda x: sca * 11.0 * (math.sin(0.5 * x * math.pi) * math.pow(max(0.0, math.sin(x * math.pi)), 0.1) + (1.0 - x) * 0.5)
    fhead = lambda x: sca * 7.0 * math.pow(max(0.0, 0.25 - math.pow(x - 0.5, 2.0)), 0.3)

    # Hand item (walking stick, fishing pole, etc.)
    prims.extend(ite(to_global(pts[8]), to_global(pts[6]), fli=fli))

    # Flowing garments
    prims.extend(cloth([pts[1], pts[7], pts[8]], fsleeve))
    prims.extend(cloth([pts[1], pts[0], pts[3], pts[4]], fbody))
    prims.extend(cloth([pts[1], pts[5], pts[6]], fsleeve))
    prims.extend(cloth([pts[1], pts[2]], fhead))

    # Head shadow
    hlist = bezmh([pts[1], pts[2]], 2.0)
    hlist1, hlist2 = expand(hlist, fhead)
    hcut1 = hlist1[int(len(hlist1) * 0.1):]
    hcut2 = hlist2[:max(1, int(len(hlist2) * 0.05))]
    prims.extend(poly([to_global(p) for p in (hcut1 + list(reversed(hcut2)))], fil="rgba(100,100,100,0.6)"))

    # Hat
    prims.extend(hat(to_global(pts[1]), to_global(pts[2]), fli=fli))
    return prims

# -----------------------------------------------------------------------------
# High-Level Fauna Presets: Traveler, Fisherman, Birds
# -----------------------------------------------------------------------------
def traveler(x: float, y: float, sca: float = 0.5, fli: bool = False) -> List[PolyPrimitive]:
    """Mountain scholar/wanderer carrying a bamboo staff."""
    return man(x, y, sca=sca, fli=fli, ite=stick01, hat=hat01)

def fisherman(x: float, y: float, sca: float = 0.4, fli: bool = False) -> List[PolyPrimitive]:
    """Seated boatman holding a slender fishing line."""
    def fishing_rod(p0, p1, fli=False):
        # Long flexible bamboo fishing rod with weighted line
        rod_prims = []
        dx = 40.0 * (-1.0 if fli else 1.0)
        dy = -35.0
        rod_tip = (p0[0] + dx, p0[1] + dy)
        rod_pts = div([p0, (p0[0] + dx * 0.5, p0[1] + dy * 0.3), rod_tip], 8)
        rod_prims.extend(stroke(rod_pts, wid=1.0, col="rgba(60,60,60,0.8)"))
        # Line dropping to water
        line_pts = [rod_tip, (rod_tip[0] + (2.0 if fli else -2.0), rod_tip[1] + 55.0)]
        rod_prims.extend(stroke(line_pts, wid=0.5, col="rgba(100,100,100,0.5)"))
        return rod_prims

    ang = [
        0.0, -math.pi * 0.5, 0.0,
        math.pi * 0.35, math.pi * 0.7,
        math.pi * 0.5, -math.pi * 0.3,
        -math.pi * 0.6, -math.pi * 0.2
    ]
    return man(x, y, sca=sca, fli=fli, ang=ang, ite=fishing_rod, hat=hat02)

def bird(x: float, y: float, scale: float = 1.0, wing_ang: float = 0.2) -> List[PolyPrimitive]:
    """Single ink-brush crane/swallow silhouette in flight."""
    # V-shaped curved ink stroke for wings
    w = 12.0 * scale
    h = 5.0 * scale
    left_wing = [
        (x - w, y - h * math.sin(wing_ang)),
        (x - w * 0.4, y - h * 1.2),
        (x, y)
    ]
    right_wing = [
        (x, y),
        (x + w * 0.4, y - h * 1.2),
        (x + w, y - h * math.sin(wing_ang))
    ]
    prims = []
    prims.extend(stroke(left_wing, wid=1.2 * scale, col="rgba(60,60,60,0.8)"))
    prims.extend(stroke(right_wing, wid=1.2 * scale, col="rgba(60,60,60,0.8)"))
    # Subtle tail dab
    prims.extend(stroke([(x, y), (x + (w * 0.1), y + h * 0.5)], wid=0.8 * scale, col="rgba(80,80,80,0.7)"))
    return prims

def bird_flock(x: float, y: float, count: int = 7, scale: float = 1.0) -> List[PolyPrimitive]:
    """Flock of ink birds soaring across the sky in a loose echelon formation."""
    prims: List[PolyPrimitive] = []
    for i in range(count):
        bx = x + i * 22.0 * scale + rand_gaussian() * 10.0 * scale
        by = y - abs(i - count * 0.5) * 15.0 * scale + rand_gaussian() * 6.0 * scale
        s = scale * (0.7 + random.random() * 0.5)
        ang = 0.1 + random.random() * 0.4
        prims.extend(bird(bx, by, scale=s, wing_ang=ang))
    return prims
