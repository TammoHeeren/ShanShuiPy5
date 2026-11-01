"""
flora.py - Recursive pine trees, weeping willows, deciduous trees, bamboo, and shrubs
Faithful reproduction of Tree.tree01 through Tree.tree08 from shanshui/index.html.
"""

import math
import random
from typing import List, Tuple, Optional, Callable, Union

from .utils import (
    PolyPrimitive, PolyTools, poly, stroke, blob, div,
    noise, rand_choice, norm_rand, rand_gaussian, distance
)

# -----------------------------------------------------------------------------
# Core Tree Trunk & Branching Primitives
# -----------------------------------------------------------------------------
def branch(hei: float = 300.0, wid: float = 6.0, ang: float = 0.0,
           det: float = 10.0, ben: float = math.pi * 0.2) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Generates 2 outline polylines for an organic tree branch."""
    nx, ny = 0.0, 0.0
    tlist = [(nx, ny)]
    a0 = 0.0
    g = 3
    for _ in range(g):
        a0 += (ben * 0.5 + (random.random() * ben) * 0.5) * random.choice([-1.0, 1.0])
        nx += (math.cos(a0) * hei) / g
        ny -= (math.sin(a0) * hei) / g
        tlist.append((nx, ny))

    ta = math.atan2(tlist[-1][1], tlist[-1][0])
    for i in range(len(tlist)):
        a = math.atan2(tlist[i][1], tlist[i][0])
        d = math.hypot(tlist[i][0], tlist[i][1])
        tlist[i] = (d * math.cos(a - ta + ang), d * math.sin(a - ta + ang))

    trlist1: List[Tuple[float, float]] = []
    trlist2: List[Tuple[float, float]] = []
    span = det if det > 0 else 10.0
    tl = int((len(tlist) - 1) * span)
    lx, ly = 0.0, 0.0

    for i in range(tl):
        idx_floor = int(i // span)
        idx_ceil = min(len(tlist) - 1, int(math.ceil(i / span)))
        p = (i % span) / span
        lastp = tlist[idx_floor]
        nextp = tlist[idx_ceil]

        nx = lastp[0] * (1.0 - p) + nextp[0] * p
        ny = lastp[1] * (1.0 - p) + nextp[1] * p

        ang_cur = math.atan2(ny - ly, nx - lx)
        woff = ((noise(i * 0.3) - 0.5) * wid * hei) / 80.0
        b = random.random() * wid if p == 0 else 0.0

        nw = wid * (((tl - i) / float(tl)) * 0.5 + 0.5) if tl > 0 else wid
        trlist1.append((
            nx + math.cos(ang_cur + math.pi * 0.5) * (nw + woff + b),
            ny + math.sin(ang_cur + math.pi * 0.5) * (nw + woff + b)
        ))
        trlist2.append((
            nx + math.cos(ang_cur - math.pi * 0.5) * (nw - woff + b),
            ny + math.sin(ang_cur - math.pi * 0.5) * (nw - woff + b)
        ))
        lx, ly = nx, ny

    return trlist1, trlist2

def twig(tx: float, ty: float, dep: int,
         dir_: float = 1.0, sca: float = 1.0, wid: float = 1.0,
         ang: float = 0.0, lea: Tuple[bool, int] = (True, 12)) -> List[PolyPrimitive]:
    """Generates fine twigs and pine needle/leaf bundles."""
    prims: List[PolyPrimitive] = []
    twlist: List[Tuple[float, float]] = []
    tl = 10
    hs = random.random() * 0.5 + 0.5

    def fun2(x):
        return -1.0 / math.pow(x + 1.0, 5) + 1.0

    a0 = ((random.random() * math.pi) / 6.0) * dir_ + ang

    for i in range(tl):
        mx = dir_ * fun2(i / float(tl)) * 50.0 * sca * hs
        my = -i * 5.0 * sca
        d = math.hypot(mx, my)
        a = math.atan2(my, mx)

        nx = math.cos(a + a0) * d
        ny = math.sin(a + a0) * d
        twlist.append((nx + tx, ny + ty))

        if (i == (tl // 3) or i == (tl * 2 // 3)) and dep > 0:
            prims.extend(twig(
                nx + tx, ny + ty, dep - 1,
                ang=ang, sca=sca * 0.8, wid=wid,
                dir_=dir_ * random.choice([-1.0, 1.0]), lea=lea
            ))

        if i == tl - 1 and lea[0]:
            for j in range(5):
                dj = (j - 2.5) * 5.0
                prims.extend(blob(
                    nx + tx + math.cos(ang) * dj * wid,
                    ny + ty + (math.sin(ang) * dj - lea[1] / float(dep + 1)) * wid,
                    wid=(6.0 + 3.0 * random.random()) * wid,
                    length=(15.0 + 12.0 * random.random()) * wid,
                    ang=ang * 0.5 + math.pi * 0.5 + math.pi * 0.2 * (random.random() - 0.5),
                    col=f"rgba(100,100,100,{(0.5 + dep * 0.2):.3f})",
                    fun=lambda x: math.pow(math.sin(x * math.pi) * x, 0.5) if x <= 1.0 else -math.pow(math.sin((x - 2.0) * math.pi * (x - 2.0)), 0.5)
                ))

    prims.extend(stroke(
        twlist, wid=1.0,
        fun=lambda x: math.cos((x * math.pi) * 0.5),
        col="rgba(100,100,100,0.5)"
    ))
    return prims

def barkify(x: float, y: float,
            trlist: Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]) -> List[PolyPrimitive]:
    """Generates organic bark surface textures and moss clumps along the trunk."""
    prims: List[PolyPrimitive] = []

    def bark(bx: float, by: float, bwid: float, bang: float) -> List[PolyPrimitive]:
        length = 10.0 + 10.0 * random.random()
        noi_val = 0.5
        reso = 20

        def fun(px):
            return math.pow(math.sin(px * math.pi), 0.5) if px <= 1.0 else -math.pow(math.sin((px + 1.0) * math.pi), 0.5)

        lalist = []
        for i in range(reso + 1):
            p = (i / float(reso)) * 2.0
            xo = length * 0.5 - abs(p - 1.0) * length
            yo = (fun(p) * bwid) * 0.5
            a = math.atan2(yo, xo)
            l = math.hypot(xo, yo)
            lalist.append((l, a))

        n0 = random.random() * 10.0
        nslist = [noise(i * 0.05, n0) for i in range(reso + 1)]
        from .utils import loop_noise
        loop_noise(nslist)

        brklist = []
        for i in range(len(lalist)):
            ns = nslist[i] * noi_val + (1.0 - noi_val)
            nx = bx + math.cos(lalist[i][1] + bang) * lalist[i][0] * ns
            ny = by + math.sin(lalist[i][1] + bang) * lalist[i][0] * ns
            brklist.append((nx, ny))

        fr = random.random()
        return stroke(
            brklist, wid=0.8, noi=0.0,
            col="rgba(100,100,100,0.4)", out=0.0,
            fun=lambda sx: math.sin((sx + fr) * math.pi * 3.0)
        )

    for i in range(2, len(trlist[0]) - 1):
        a0 = math.atan2(trlist[0][i][1] - trlist[0][i - 1][1], trlist[0][i][0] - trlist[0][i - 1][0])
        a1 = math.atan2(trlist[1][i][1] - trlist[1][i - 1][1], trlist[1][i][0] - trlist[1][i - 1][0])
        p = random.random()
        nx = trlist[0][i][0] * (1.0 - p) + trlist[1][i][0] * p
        ny = trlist[0][i][1] * (1.0 - p) + trlist[1][i][1] * p

        if random.random() < 0.2:
            prims.extend(blob(
                nx + x, ny + y, noi=1.0, length=15.0,
                wid=max(0.5, 6.0 - abs(p - 0.5) * 10.0),
                ang=(a0 + a1) * 0.5,
                col="rgba(100,100,100,0.6)"
            ))
        else:
            prims.extend(bark(
                nx + x, ny + y,
                max(0.5, 5.0 - abs(p - 0.5) * 10.0),
                (a0 + a1) * 0.5
            ))

        if random.random() < 0.05:
            jl = random.random() * 2.0 + 2.0
            xya = random.choice([
                (trlist[0][i][0], trlist[0][i][1], a0),
                (trlist[1][i][0], trlist[1][i][1], a1)
            ])
            for j in range(int(jl)):
                prims.extend(blob(
                    xya[0] + x + math.cos(xya[2]) * (j - jl * 0.5) * 4.0,
                    xya[1] + y + math.sin(xya[2]) * (j - jl * 0.5) * 4.0,
                    wid=4.0, length=4.0 + 6.0 * random.random(),
                    ang=a0 + math.pi * 0.5,
                    col="rgba(100,100,100,0.6)"
                ))

    # Bark contour edge shading
    trflist = trlist[0] + list(reversed(trlist[1]))
    rglist: List[List[Tuple[float, float]]] = [[]]
    for pt in trflist:
        if random.random() < 0.5:
            rglist.append([])
        else:
            rglist[-1].append(pt)

    for i in range(len(rglist)):
        if len(rglist[i]) < 2:
            continue
        sub_pts = div(rglist[i], 4)
        for j in range(len(sub_pts)):
            rx = sub_pts[j][0] + (noise(i, j * 0.1, 1.0) - 0.5) * (15.0 + 5.0 * rand_gaussian())
            ry = sub_pts[j][1] + (noise(i, j * 0.1, 2.0) - 0.5) * (15.0 + 5.0 * rand_gaussian())
            sub_pts[j] = (rx, ry)
        prims.extend(stroke(
            [(v[0] + x, v[1] + y) for v in sub_pts],
            wid=1.5, col="rgba(100,100,100,0.7)", out=0.0
        ))

    return prims

# -----------------------------------------------------------------------------
# 8 Tree Archetypes
# -----------------------------------------------------------------------------
def tree01(x: float, y: float, hei: float = 50.0, wid: float = 3.0,
           col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Small mountain conifer / pine tree with stepped triangular branch tiers."""
    reso = 10
    nslist = [(noise(i * 0.5), noise(i * 0.5, 0.5)) for i in range(reso)]
    prims: List[PolyPrimitive] = []
    line1 = []
    line2 = []

    for i in range(reso):
        nx = x
        ny = y - (i * hei) / float(reso)
        if i >= reso // 4:
            count = int((reso - i) / 5.0)
            for _ in range(count):
                prims.extend(blob(
                    nx + (random.random() - 0.5) * wid * 1.2 * (reso - i),
                    ny + (random.random() - 0.5) * wid,
                    length=random.random() * 20.0 * (reso - i) * 0.2 + 10.0,
                    wid=random.random() * 6.0 + 3.0,
                    ang=((random.random() - 0.5) * math.pi) / 6.0,
                    col=f"rgba(100,100,100,{(random.random() * 0.2 + 0.5):.2f})"
                ))
        line1.append((nx + (nslist[i][0] - 0.5) * wid - wid * 0.5, ny))
        line2.append((nx + (nslist[i][1] - 0.5) * wid + wid * 0.5, ny))

    prims.extend(poly(line1, fil=(0, 0, 0, 0), str_=col, wid=1.5))
    prims.extend(poly(line2, fil=(0, 0, 0, 0), str_=col, wid=1.5))
    return prims

def tree02(x: float, y: float, hei: float = 16.0, wid: float = 8.0,
           clu: int = 5, col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Foliage dot cluster / shrub clumps along ridge rims."""
    prims: List[PolyPrimitive] = []
    for _ in range(clu):
        prims.extend(blob(
            x + rand_gaussian() * clu * 4.0,
            y + rand_gaussian() * clu * 4.0,
            ang=math.pi * 0.5,
            wid=random.random() * wid * 0.75 + wid * 0.5,
            length=random.random() * hei * 0.75 + hei * 0.5,
            col=col,
            fun=lambda px: math.pow(math.sin(px * math.pi) * px, 0.5) if px <= 1.0 else -math.pow(math.sin((px - 2.0) * math.pi * (px - 2.0)), 0.5)
        ))
    return prims

def tree03(x: float, y: float, hei: float = 50.0, wid: float = 5.0,
           ben: Optional[Callable[[float], float]] = None,
           col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Curved mountain pine leaning with foliage clusters."""
    if ben is None:
        ben = lambda v: 0.0
    reso = 10
    nslist = [(noise(i * 0.5), noise(i * 0.5, 0.5)) for i in range(reso)]
    prims: List[PolyPrimitive] = []
    blob_prims: List[PolyPrimitive] = []
    line1 = []
    line2 = []

    for i in range(reso):
        nx = x + ben(i / float(reso)) * 100.0
        ny = y - (i * hei) / float(reso)
        if i >= reso // 5:
            count = int((reso - i) * 2)
            for _ in range(count):
                shape = lambda sx: math.log(50.0 * sx + 1.0) / 3.95
                ox = random.random() * wid * 2.0 * shape((reso - i) / float(reso))
                blob_prims.extend(blob(
                    nx + ox * random.choice([-1.0, 1.0]),
                    ny + (random.random() - 0.5) * wid * 2.0,
                    length=ox * 2.0,
                    wid=random.random() * 6.0 + 3.0,
                    ang=((random.random() - 0.5) * math.pi) / 6.0,
                    col=f"rgba(100,100,100,{(random.random() * 0.2 + 0.5):.3f})"
                ))
        p = (reso - i) / float(reso)
        line1.append((nx + (((nslist[i][0] - 0.5) * wid - wid * 0.5) * p), ny))
        line2.append((nx + (((nslist[i][1] - 0.5) * wid + wid * 0.5) * p), ny))

    lc = line1 + list(reversed(line2))
    prims.extend(poly(lc, fil="white", str_=col, wid=1.5))
    prims.extend(blob_prims)
    return prims

def tree04(x: float, y: float, hei: float = 300.0, wid: float = 6.0,
           col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Majestic fractal pine tree with bark cross-hatchings and radial pine needle bundles."""
    prims: List[PolyPrimitive] = []
    trlist_pair = branch(hei=hei, wid=wid, ang=-math.pi * 0.5)
    bark_prims = barkify(x, y, trlist_pair)

    trlist = trlist_pair[0] + list(reversed(trlist_pair[1]))
    trmlist: List[Tuple[float, float]] = []
    tw_prims: List[PolyPrimitive] = []

    for i in range(len(trlist)):
        if ((i >= len(trlist) * 0.3 and i <= len(trlist) * 0.7 and random.random() < 0.1) or
                i == len(trlist) // 2 - 1):
            ba = math.pi * 0.2 - math.pi * 1.4 * (1.0 if i > len(trlist) // 2 else 0.0)
            brlist_pair = branch(hei=hei * (random.random() + 1.0) * 0.3, wid=wid * 0.5, ang=ba)
            b0 = brlist_pair[0][1:]
            b1 = brlist_pair[1][1:]

            foff = lambda v: (v[0] + trlist[i][0], v[1] + trlist[i][1])
            bark_prims.extend(barkify(x, y, ([foff(v) for v in b0], [foff(v) for v in b1])))

            for j in range(len(b0)):
                if random.random() < 0.2 or j == len(b0) - 1:
                    tw_prims.extend(twig(
                        b0[j][0] + trlist[i][0] + x,
                        b0[j][1] + trlist[i][1] + y,
                        1,
                        wid=hei / 300.0,
                        ang=ba if ba > -math.pi * 0.5 else ba + math.pi,
                        sca=(0.5 * hei) / 300.0,
                        dir_=1.0 if ba > -math.pi * 0.5 else -1.0
                    ))
            brlist = b0 + list(reversed(b1))
            trmlist.extend([(v[0] + trlist[i][0], v[1] + trlist[i][1]) for v in brlist])
        else:
            trmlist.append(trlist[i])

    prims.extend(poly(trmlist, xof=x, yof=y, fil="white", str_=col, wid=0.0))
    if len(trmlist) > 2:
        inner_pts = [(v[0] + x, v[1] + y) for v in trmlist[1:-1]]
        prims.extend(stroke(
            inner_pts,
            col=f"rgba(100,100,100,{(0.4 + random.random() * 0.1):.3f})",
            wid=2.5, fun=lambda _: math.sin(1.0), noi=0.9, out=0.0
        ))

    prims.extend(bark_prims)
    prims.extend(tw_prims)
    return prims

def tree05(x: float, y: float, hei: float = 300.0, wid: float = 5.0,
           col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Weeping willow tree with graceful arching trunk and hanging vertical vine strings."""
    prims: List[PolyPrimitive] = []
    trlist_pair = branch(hei=hei, wid=wid, ang=-math.pi * 0.5, ben=0.0)
    bark_prims = barkify(x, y, trlist_pair)

    trlist = trlist_pair[0] + list(reversed(trlist_pair[1]))
    trmlist: List[Tuple[float, float]] = []
    tw_prims: List[PolyPrimitive] = []
    half_len = len(trlist) * 0.5

    for i in range(len(trlist)):
        p = abs(i - half_len) / half_len if half_len > 0 else 0.5
        if ((i >= len(trlist) * 0.2 and i <= len(trlist) * 0.8 and i % 3 == 0 and random.random() > p) or
                i == len(trlist) // 2 - 1):
            bar = random.random() * 0.2
            ba = -bar * math.pi - (1.0 - bar * 2.0) * math.pi * (1.0 if i > len(trlist) // 2 else 0.0)
            brlist_pair = branch(
                hei=hei * max(0.1, 0.3 * p - random.random() * 0.05),
                wid=wid * 0.5, ang=ba, ben=0.5
            )
            b0 = brlist_pair[0][1:]
            b1 = brlist_pair[1][1:]

            for j in range(len(b0)):
                if j % 20 == 0 or j == len(b0) - 1:
                    tw_prims.extend(twig(
                        b0[j][0] + trlist[i][0] + x,
                        b0[j][1] + trlist[i][1] + y,
                        0,
                        wid=hei / 300.0,
                        ang=ba if ba > -math.pi * 0.5 else ba + math.pi,
                        sca=(0.2 * hei) / 300.0,
                        dir_=1.0 if ba > -math.pi * 0.5 else -1.0,
                        lea=(True, 5)
                    ))
            brlist = b0 + list(reversed(b1))
            trmlist.extend([(v[0] + trlist[i][0], v[1] + trlist[i][1]) for v in brlist])
        else:
            trmlist.append(trlist[i])

    prims.extend(poly(trmlist, xof=x, yof=y, fil="white", str_=col, wid=0.0))
    if len(trmlist) > 2:
        inner_pts = [(v[0] + x, v[1] + y) for v in trmlist[1:-1]]
        prims.extend(stroke(
            inner_pts,
            col=f"rgba(100,100,100,{(0.4 + random.random() * 0.1):.3f})",
            wid=2.5, fun=lambda _: math.sin(1.0), noi=0.9, out=0.0
        ))

    prims.extend(bark_prims)
    prims.extend(tw_prims)
    return prims

def tree06(x: float, y: float, hei: float = 100.0, wid: float = 6.0,
           col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Bare winter deciduous tree with recursive fractal branch splitting."""
    prims: List[PolyPrimitive] = []
    bark_prims: List[PolyPrimitive] = []
    tw_prims: List[PolyPrimitive] = []

    def frac_tree(xoff: float, yoff: float, dep: int,
                  fhei: float = 300.0, fwid: float = 5.0, fang: float = 0.0,
                  fben: float = math.pi * 0.2) -> List[Tuple[float, float]]:
        trlist_pair = branch(hei=fhei, wid=fwid, ang=fang, ben=fben, det=max(5.0, fhei / 20.0))
        bark_prims.extend(barkify(xoff, yoff, trlist_pair))
        trlist = trlist_pair[0] + list(reversed(trlist_pair[1]))
        trmlist: List[Tuple[float, float]] = []

        for i in range(len(trlist)):
            if (((random.random() < 0.025 and i >= len(trlist) * 0.2 and i <= len(trlist) * 0.8) or
                 i == len(trlist) // 2 - 1 or i == len(trlist) // 2 + 1) and dep > 0):
                bar = 0.02 + random.random() * 0.08
                ba = bar * math.pi - bar * 2.0 * math.pi * (1.0 if i > len(trlist) // 2 else 0.0)

                brlist = frac_tree(
                    trlist[i][0] + xoff, trlist[i][1] + yoff,
                    dep - 1,
                    fhei=fhei * (0.7 + random.random() * 0.2),
                    fwid=fwid * 0.6,
                    fang=fang + ba,
                    fben=0.55
                )

                for j in range(len(brlist)):
                    if random.random() < 0.03:
                        tw_prims.extend(twig(
                            brlist[j][0] + trlist[i][0] + xoff,
                            brlist[j][1] + trlist[i][1] + yoff,
                            2,
                            ang=ba * (random.random() * 0.5 + 0.75),
                            sca=0.3,
                            dir_=1.0 if ba > 0 else -1.0,
                            lea=(False, 0)
                        ))

                trmlist.extend([(v[0] + trlist[i][0], v[1] + trlist[i][1]) for v in brlist])
            else:
                trmlist.append(trlist[i])
        return trmlist

    trmlist = frac_tree(x, y, 3, fhei=hei, fwid=wid, fang=-math.pi * 0.5, fben=0.0)
    prims.extend(poly(trmlist, xof=x, yof=y, fil="white", str_=col, wid=0.0))
    if len(trmlist) > 2:
        inner_pts = [(v[0] + x, v[1] + y) for v in trmlist[1:-1]]
        prims.extend(stroke(
            inner_pts,
            col=f"rgba(100,100,100,{(0.4 + random.random() * 0.1):.3f})",
            wid=2.5, fun=lambda _: math.sin(1.0), noi=0.9, out=0.0
        ))

    prims.extend(bark_prims)
    prims.extend(tw_prims)
    return prims

def tree07(x: float, y: float, hei: float = 60.0, wid: float = 4.0,
           ben: Optional[Callable[[float], float]] = None,
           col: str = "rgba(100,100,100,1)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Bamboo grove / birch trees with segmented stalks and triangulated leaf fans."""
    if ben is None:
        ben = lambda v: math.sqrt(v) * 0.2
    reso = 10
    nslist = [(noise(i * 0.5), noise(i * 0.5, 0.5)) for i in range(reso)]
    prims: List[PolyPrimitive] = []
    line1 = []
    line2 = []
    t_polys: List[List[Tuple[float, float]]] = []

    for i in range(reso):
        nx = x + ben(i / float(reso)) * 100.0
        ny = y - (i * hei) / float(reso)
        if i >= reso // 4:
            bpl = blob(
                nx + (random.random() - 0.5) * wid * 1.2 * (reso - i) * 0.5,
                ny + (random.random() - 0.5) * wid * 0.5,
                length=random.random() * 50.0 + 20.0,
                wid=random.random() * 12.0 + 12.0,
                ang=(-random.random() * math.pi) / 6.0,
                fun=lambda px: (2.75 * px * math.pow(max(0.0, 1.0 - px), 1.0 / 1.8)) if px <= 1.0 else (2.75 * (px - 2.0) * math.pow(max(0.0, px - 1.0), 1.0 / 1.8))
            )
            if bpl and bpl[0].points:
                t_polys.extend(PolyTools.triangulate(bpl[0].points, area=50.0, convex=True, optimize=False))

        line1.append((nx + (nslist[i][0] - 0.5) * wid - wid * 0.5, ny))
        line2.append((nx + (nslist[i][1] - 0.5) * wid + wid * 0.5, ny))

    stalk = line1 + list(reversed(line2))
    t_polys = PolyTools.triangulate(stalk, area=50.0, convex=True, optimize=True) + t_polys

    for tri in t_polys:
        m = PolyTools.mid_pt(tri)
        c = int(noise(m[0] * 0.02, m[1] * 0.02) * 200.0 + 50.0)
        co = f"rgba({c},{c},{c},0.8)"
        prims.extend(poly(tri, fil=co, str_=co, wid=0.0))

    return prims

def tree08(x: float, y: float, hei: float = 80.0, wid: float = 1.0,
           col: str = "rgba(100,100,100,0.5)", noi: float = 0.5) -> List[PolyPrimitive]:
    """Dry reeds / shore grasses with multi-tier fractal twigs."""
    prims: List[PolyPrimitive] = []
    ang = norm_rand(-1.0, 1.0) * math.pi * 0.2
    trlist_pair = branch(
        hei=hei, wid=wid, ang=-math.pi * 0.5 + ang,
        ben=math.pi * 0.2, det=max(4.0, hei / 20.0)
    )
    trlist = trlist_pair[0] + list(reversed(trlist_pair[1]))
    tw_prims: List[PolyPrimitive] = []

    def frac_reed(xoff: float, yoff: float, dep: int,
                  fang: float = -math.pi * 0.5, flen: float = 15.0, fben: float = 0.0) -> List[PolyPrimitive]:
        fun = (lambda px: math.cos(0.5 * math.pi * px)) if dep == 0 else (lambda _: 1.0)
        spt = (xoff, yoff)
        ept = (xoff + math.cos(fang) * flen, yoff + math.sin(fang) * flen)

        trmlist = [(xoff, yoff), (xoff + flen, yoff)]
        bfun = random.choice([lambda px: math.sin(px * math.pi), lambda px: -math.sin(px * math.pi)])
        trmlist = div(trmlist, 10)

        for idx, pt in enumerate(trmlist):
            trmlist[idx] = (pt[0], pt[1] + bfun(idx / float(len(trmlist))) * 2.0)

        for idx, pt in enumerate(trmlist):
            d = distance(pt, spt)
            a = math.atan2(pt[1] - spt[1], pt[0] - spt[0])
            trmlist[idx] = (spt[0] + d * math.cos(a + fang), spt[1] + d * math.sin(a + fang))

        sub_prims = stroke(trmlist, fun=fun, wid=0.8, col="rgba(100,100,100,0.5)")
        if dep != 0:
            nben = fben + random.choice([-1.0, 1.0]) * math.pi * 0.001 * dep * dep
            if random.random() < 0.5:
                sub_prims.extend(frac_reed(
                    ept[0], ept[1], dep - 1,
                    fang=fang + fben + math.pi * random.choice([norm_rand(-1.0, 0.5), norm_rand(0.5, 1.0)]) * 0.2,
                    flen=flen * norm_rand(0.8, 0.9), fben=nben
                ))
                sub_prims.extend(frac_reed(
                    ept[0], ept[1], dep - 1,
                    fang=fang + fben + math.pi * random.choice([norm_rand(-1.0, -0.5), norm_rand(0.5, 1.0)]) * 0.2,
                    flen=flen * norm_rand(0.8, 0.9), fben=nben
                ))
            else:
                sub_prims.extend(frac_reed(
                    ept[0], ept[1], dep - 1,
                    fang=fang + fben, flen=flen * norm_rand(0.8, 0.9), fben=nben
                ))
        return sub_prims

    for i in range(len(trlist)):
        if random.random() < 0.2:
            tw_prims.extend(frac_reed(
                x + trlist[i][0], y + trlist[i][1],
                int(4 * random.random()),
                flen=20.0, fang=-math.pi * 0.5 - ang * random.random()
            ))
        elif i == len(trlist) // 2:
            tw_prims.extend(frac_reed(
                x + trlist[i][0], y + trlist[i][1], 3,
                flen=25.0, fang=-math.pi * 0.5 + ang
            ))

    prims.extend(poly(trlist, xof=x, yof=y, fil="white", str_=col, wid=0.0))
    prims.extend(stroke(
        [(v[0] + x, v[1] + y) for v in trlist],
        col=f"rgba(100,100,100,{(0.6 + random.random() * 0.1):.3f})",
        wid=2.5, fun=lambda _: math.sin(1.0), noi=0.9, out=0.0
    ))
    prims.extend(tw_prims)
    return prims
