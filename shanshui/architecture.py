"""
architecture.py - Pagodas, pavilions, cottages, arched bridges, railings, boats, and transmission towers
Faithful reproduction of Arch.* from shanshui/index.html.
"""

import math
import random
from typing import List, Tuple, Optional, Callable, Dict, Any, Union

from .utils import (
    PolyPrimitive, PolyTools, poly, stroke, div, texture,
    noise, rand_choice, norm_rand, wtrand
)
from .fauna import man, stick01, hat02

def flip(ptlist: List[Any], axis: float = 0.0) -> List[Any]:
    """Flips 2D points or lists of points horizontally across an axis."""
    out = []
    for item in ptlist:
        if isinstance(item, list) and item and isinstance(item[0], (list, tuple)):
            out.append([(axis - (pt[0] - axis), pt[1]) for pt in item])
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append((axis - (item[0] - axis), item[1]))
        else:
            out.append(item)
    return out

# -----------------------------------------------------------------------------
# Base Architectural Primitives
# -----------------------------------------------------------------------------
def hut(xoff: float, yoff: float, hei: float = 40.0, wid: float = 180.0,
        tex: int = 300) -> List[PolyPrimitive]:
    """Rustic thatched hut with textured wall planks."""
    reso = [10, 10]
    ptlist: List[List[Tuple[float, float]]] = []

    for i in range(reso[0]):
        ptlist.append([])
        heir = hei + hei * 0.2 * random.random()
        for j in range(reso[1]):
            nx = wid * (i / float(reso[0] - 1) - 0.5) * math.pow(j / float(reso[1] - 1), 0.7)
            ny = heir * (j / float(reso[1] - 1))
            ptlist[-1].append((nx, ny))

    prims: List[PolyPrimitive] = []
    hull = ptlist[0][:-1] + list(reversed(ptlist[-1][:-1]))
    prims.extend(poly(hull, xof=xoff, yof=yoff, fil="white", str_="none"))
    prims.extend(poly(ptlist[0], xof=xoff, yof=yoff, fil="none", str_="rgba(100,100,100,0.3)", wid=2.0))
    prims.extend(poly(ptlist[-1], xof=xoff, yof=yoff, fil="none", str_="rgba(100,100,100,0.3)", wid=2.0))

    prims.extend(texture(
        ptlist, xof=xoff, yof=yoff, tex=tex, wid=1.0, length=0.25,
        col_fn=lambda _: f"rgba(120,120,120,{(0.3 + random.random() * 0.3):.3f})",
        dis_fn=lambda: wtrand(lambda a: a * a),
        noi_fn=lambda _: 5.0
    ))
    return prims

def deco(style: int, pul: Tuple[float, float] = (0, 0), pur: Tuple[float, float] = (0, 100),
         pdl: Tuple[float, float] = (100, 0), pdr: Tuple[float, float] = (100, 100),
         hsp: Tuple[int, int] = (1, 3), vsp: Tuple[int, int] = (1, 2)) -> List[List[Tuple[float, float]]]:
    """Generates traditional lattice window and door grid patterns."""
    plist: List[List[Tuple[float, float]]] = []
    dl = div([pul, pdl], vsp[1])
    dr = div([pur, pdr], vsp[1])
    du = div([pul, pur], hsp[1])
    dd = div([pdl, pdr], hsp[1])

    if style == 1:
        mlu = du[hsp[0]]
        mru = du[len(du) - 1 - hsp[0]]
        mld = dd[hsp[0]]
        mrd = dd[len(du) - 1 - hsp[0]]
        for i in range(vsp[0], len(dl) - vsp[0], vsp[0]):
            mml = div([mlu, mld], vsp[1])[i]
            mmr = div([mru, mrd], vsp[1])[i]
            ml = dl[i]
            mr = dr[i]
            plist.append(div([mml, ml], 5))
            plist.append(div([mmr, mr], 5))
        plist.append(div([mlu, mld], 5))
        plist.append(div([mru, mrd], 5))
    elif style == 2:
        for i in range(hsp[0], len(du) - hsp[0], hsp[0]):
            mu = du[i]
            md = dd[i]
            plist.append(div([mu, md], 5))
    elif style == 3:
        mlu = du[hsp[0]]
        mru = du[len(du) - 1 - hsp[0]]
        mld = dd[hsp[0]]
        mrd = dd[len(du) - 1 - hsp[0]]
        for i in range(vsp[0], len(dl) - vsp[0], vsp[0]):
            mml = div([mlu, mld], vsp[1])[i]
            mmr = div([mru, mrd], vsp[1])[i]
            mmu = div([mlu, mru], vsp[1])[i]
            mmd = div([mld, mrd], vsp[1])[i]
            ml = dl[i]
            mr = dr[i]
            plist.append(div([mml, mmr], 5))
            plist.append(div([mmu, mmd], 5))
        plist.append(div([mlu, mld], 5))
        plist.append(div([mru, mrd], 5))

    return plist

def box(xoff: float, yoff: float, hei: float = 20.0, wid: float = 120.0,
        rot: float = 0.7, per: float = 4.0, tra: bool = True, bot: bool = True,
        wei: float = 3.0, dec: Optional[Callable] = None) -> List[PolyPrimitive]:
    """3D perspective pavilion room with corner posts and lattice walls."""
    mid = -wid * 0.5 + wid * rot
    bmid = -wid * 0.5 + wid * (1.0 - rot)
    ptlist: List[List[Tuple[float, float]]] = []

    ptlist.append(div([(-wid * 0.5, -hei), (-wid * 0.5, 0.0)], 5))
    ptlist.append(div([(wid * 0.5, -hei), (wid * 0.5, 0.0)], 5))
    if bot:
        ptlist.append(div([(-wid * 0.5, 0.0), (mid, per)], 5))
        ptlist.append(div([(wid * 0.5, 0.0), (mid, per)], 5))
    ptlist.append(div([(mid, -hei), (mid, per)], 5))

    if tra:
        if bot:
            ptlist.append(div([(-wid * 0.5, 0.0), (bmid, -per)], 5))
            ptlist.append(div([(wid * 0.5, 0.0), (bmid, -per)], 5))
        ptlist.append(div([(bmid, -hei), (bmid, -per)], 5))

    surf = 1.0 if rot < 0.5 else -1.0
    if dec is not None:
        dec_pts = dec({
            "pul": (surf * wid * 0.5, -hei),
            "pur": (mid, -hei + per),
            "pdl": (surf * wid * 0.5, 0.0),
            "pdr": (mid, per)
        })
        ptlist.extend(dec_pts)

    polist = [
        (-wid * 0.5, -hei), (wid * 0.5, -hei),
        (wid * 0.5, 0.0), (mid, per), (-wid * 0.5, 0.0)
    ]

    prims: List[PolyPrimitive] = []
    if not tra:
        prims.extend(poly(polist, xof=xoff, yof=yoff, str_="none", fil="white"))

    for pts in ptlist:
        shifted = [(p[0] + xoff, p[1] + yoff) for p in pts]
        prims.extend(stroke(shifted, col="rgba(100,100,100,0.4)", noi=1.0, wid=wei, fun=lambda _: 1.0))

    return prims

def rail(xoff: float, yoff: float, seed: float = 0.0,
         hei: float = 20.0, wid: float = 180.0, rot: float = 0.7,
         per: float = 4.0, seg: int = 4, wei: float = 1.0,
         tra: bool = True, fro: bool = True) -> List[PolyPrimitive]:
    """Balustrades, wooden railings, and fences."""
    mid = -wid * 0.5 + wid * rot
    bmid = -wid * 0.5 + wid * (1.0 - rot)
    ptlist: List[List[Tuple[float, float]]] = []

    if fro:
        ptlist.append(div([(-wid * 0.5, 0.0), (mid, per)], seg))
        ptlist.append(div([(mid, per), (wid * 0.5, 0.0)], seg))
    if tra:
        ptlist.append(div([(-wid * 0.5, 0.0), (bmid, -per)], seg))
        ptlist.append(div([(bmid, -per), (wid * 0.5, 0.0)], seg))
    if fro:
        ptlist.append(div([(-wid * 0.5, -hei), (mid, -hei + per)], seg))
        ptlist.append(div([(mid, -hei + per), (wid * 0.5, -hei)], seg))
    if tra:
        ptlist.append(div([(-wid * 0.5, -hei), (bmid, -hei - per)], seg))
        ptlist.append(div([(bmid, -hei - per), (wid * 0.5, -hei)], seg))

    if tra and ptlist:
        open_idx = random.randint(0, len(ptlist) - 1)
        ptlist[open_idx] = ptlist[open_idx][:-1]
        pair_idx = (open_idx + len(ptlist)) % len(ptlist)
        ptlist[pair_idx] = ptlist[pair_idx][:-1]

    prims: List[PolyPrimitive] = []
    half_len = len(ptlist) // 2

    for i in range(half_len):
        target_idx = (half_len + i) % len(ptlist)
        target_len = len(ptlist[target_idx])
        for j in range(len(ptlist[i])):
            if target_len == 0:
                continue
            tj = j % target_len
            y1 = ptlist[i][j][1] + (noise(i, j * 0.5, seed) - 0.5) * hei
            ptlist[i][j] = (ptlist[i][j][0], y1)
            y2 = ptlist[target_idx][tj][1] + (noise(i + 0.5, j * 0.5, seed) - 0.5) * hei
            ptlist[target_idx][tj] = (ptlist[target_idx][tj][0], y2)

            ln = div([ptlist[i][j], ptlist[target_idx][tj]], 2)
            ln[0] = (ln[0][0] + (random.random() - 0.5) * hei * 0.5, ln[0][1])
            prims.extend(poly(ln, xof=xoff, yof=yoff, fil="none", str_="rgba(100,100,100,0.5)", wid=2.0))

    for pts in ptlist:
        shifted = [(p[0] + xoff, p[1] + yoff) for p in pts]
        prims.extend(stroke(shifted, col="rgba(100,100,100,0.5)", noi=0.5, wid=wei, fun=lambda _: 1.0))

    return prims

def roof(xoff: float, yoff: float, hei: float = 20.0, wid: float = 120.0,
         rot: float = 0.7, per: float = 4.0, cor: float = 5.0, wei: float = 3.0,
         pla: Optional[Tuple[int, str]] = None) -> List[PolyPrimitive]:
    """Swept-eave Chinese gabled roof."""
    opf = lambda pl: flip(pl) if rot < 0.5 else pl
    rrot = 1.0 - rot if rot < 0.5 else rot

    mid = -wid * 0.5 + wid * rrot
    quat = (mid + wid * 0.5) * 0.5 - mid

    ptlist: List[List[Tuple[float, float]]] = []
    ptlist.append(div(opf([
        (-wid * 0.5 + quat, -hei - per * 0.5),
        (-wid * 0.5 + quat * 0.5, -hei * 0.5 - per * 0.25),
        (-wid * 0.5 - cor, 0.0)
    ]), 5))
    ptlist.append(div(opf([
        (mid + quat, -hei),
        ((mid + quat + wid * 0.5) * 0.5, -hei * 0.5),
        (wid * 0.5 + cor, 0.0)
    ]), 5))
    ptlist.append(div(opf([
        (mid + quat, -hei),
        (mid + quat * 0.5, -hei * 0.5 + per * 0.5),
        (mid + cor, per)
    ]), 5))
    ptlist.append(div(opf([(-wid * 0.5 - cor, 0.0), (mid + cor, per)]), 5))
    ptlist.append(div(opf([(wid * 0.5 + cor, 0.0), (mid + cor, per)]), 5))
    ptlist.append(div(opf([(-wid * 0.5 + quat, -hei - per * 0.5), (mid + quat, -hei)]), 5))

    polist = opf([
        (-wid * 0.5, 0.0),
        (-wid * 0.5 + quat, -hei - per * 0.5),
        (mid + quat, -hei),
        (wid * 0.5, 0.0),
        (mid, per)
    ])

    prims: List[PolyPrimitive] = []
    prims.extend(poly(polist, xof=xoff, yof=yoff, str_="none", fil="white"))
    for pts in ptlist:
        shifted = [(p[0] + xoff, p[1] + yoff) for p in pts]
        prims.extend(stroke(shifted, col="rgba(100,100,100,0.4)", noi=1.0, wid=wei, fun=lambda _: 1.0))
    return prims

def pagroof(xoff: float, yoff: float, hei: float = 20.0, wid: float = 120.0,
            rot: float = 0.7, per: float = 4.0, cor: float = 10.0,
            sid: int = 4, wei: float = 3.0) -> List[PolyPrimitive]:
    """Curved multi-sided pagoda roof with upturned eaves."""
    ptlist: List[List[Tuple[float, float]]] = []
    polist = [(0.0, -hei)]
    prims: List[PolyPrimitive] = []

    for i in range(sid):
        p = i / float(sid - 1)
        fx = wid * (p - 0.5)
        fy = per * (1.0 - abs(p - 0.5) * 2.0)
        fxx = (wid + cor) * (p - 0.5)
        if i > 0 and ptlist:
            ptlist.append([ptlist[-1][2], (fxx, fy)])
        ptlist.append([(0.0, -hei), (fx * 0.5, (-hei + fy) * 0.5), (fxx, fy)])
        polist.append((fxx, fy))

    prims.extend(poly(polist, xof=xoff, yof=yoff, str_="none", fil="white"))
    for pts in ptlist:
        shifted = [(p[0] + xoff, p[1] + yoff) for p in div(pts, 5)]
        prims.extend(stroke(shifted, col="rgba(100,100,100,0.4)", noi=1.0, wid=wei, fun=lambda _: 1.0))
    return prims

# -----------------------------------------------------------------------------
# Compound Structures
# -----------------------------------------------------------------------------
def arch01(xoff: float, yoff: float, seed: float = 0.0,
           hei: float = 70.0, wid: float = 180.0, rot: float = 0.7,
           per: float = 5.0) -> List[PolyPrimitive]:
    """Rustic scholar cottage with thatched roof, balustrade, and visiting traveler."""
    p = 0.4 + random.random() * 0.2
    h0 = hei * p
    h1 = hei * (1.0 - p)
    prims: List[PolyPrimitive] = []

    prims.extend(hut(xoff, yoff - hei, hei=h0, wid=wid))
    prims.extend(box(xoff, yoff, hei=h1, wid=(wid * 2.0) / 3.0, per=per, bot=False))
    prims.extend(rail(xoff, yoff, seed=seed, tra=True, fro=False, hei=10.0, wid=wid, per=per * 2.0, seg=int(3 + random.random() * 3)))

    mcnt = random.choice([0, 1, 1, 2])
    if mcnt == 1:
        prims.extend(man(xoff + norm_rand(-wid / 3.0, wid / 3.0), yoff, fli=random.choice([True, False]), sca=0.42))
    elif mcnt == 2:
        prims.extend(man(xoff + norm_rand(-wid / 4.0, -wid / 5.0), yoff, fli=False, sca=0.42))
        prims.extend(man(xoff + norm_rand(wid / 5.0, wid / 4.0), yoff, fli=True, sca=0.42))

    prims.extend(rail(xoff, yoff, seed=seed, tra=False, fro=True, hei=10.0, wid=wid, per=per * 2.0, seg=int(3 + random.random() * 3)))
    return prims

def arch02(xoff: float, yoff: float, seed: float = 0.0,
           hei: float = 10.0, wid: float = 50.0, rot: float = 0.3,
           per: float = 5.0, sto: int = 3, sty: int = 1,
           rai: bool = False) -> List[PolyPrimitive]:
    """Lookout pavilion / gazebo nestled on mountain cliffs."""
    prims: List[PolyPrimitive] = []
    hoff = 0.0

    for i in range(sto):
        cur_wid = wid * math.pow(0.85, i)
        def dec_fn(a):
            h_sp = [(), (1, 5), (1, 5), (1, 4)][sty]
            v_sp = [(), (1, 2), (1, 2), (1, 3)][sty]
            return deco(sty, pul=a["pul"], pur=a["pur"], pdl=a["pdl"], pdr=a["pdr"], hsp=h_sp, vsp=v_sp)

        prims.extend(box(xoff, yoff - hoff, tra=False, hei=hei, wid=cur_wid, rot=rot, wei=1.5, per=per, dec=dec_fn))
        if rai:
            prims.extend(rail(xoff, yoff - hoff, seed=i * 0.2, wid=cur_wid * 1.1, hei=hei * 0.5, per=per, rot=rot, wei=0.5, tra=False))
        prims.extend(roof(xoff, yoff - hoff - hei, hei=hei, wid=wid * math.pow(0.9, i), rot=rot, wei=1.5, per=per))
        hoff += hei * 1.5

    return prims

def arch03(xoff: float, yoff: float, seed: float = 0.0,
           hei: float = 10.0, wid: float = 50.0, rot: float = 0.7,
           per: float = 5.0, sto: int = 7) -> List[PolyPrimitive]:
    """Grand multi-story pagoda tower (5-7 tiers) tapering toward the sky."""
    prims: List[PolyPrimitive] = []
    hoff = 0.0

    for i in range(sto):
        cur_wid = wid * math.pow(0.85, i)
        dec_fn = lambda a: deco(1, pul=a["pul"], pur=a["pur"], pdl=a["pdl"], pdr=a["pdr"], hsp=(1, 4), vsp=(1, 2))
        prims.extend(box(xoff, yoff - hoff, tra=False, hei=hei, wid=cur_wid, rot=rot, wei=1.5, per=per * 0.5, dec=dec_fn))
        prims.extend(rail(xoff, yoff - hoff, seed=i * 0.2, seg=5, wid=cur_wid * 1.1, hei=hei * 0.5, per=per * 0.5, rot=rot, wei=0.5, tra=False))
        prims.extend(pagroof(xoff, yoff - hoff - hei, hei=hei * 1.5, wid=wid * math.pow(0.9, i), rot=rot, wei=1.5, per=per))
        hoff += hei * 1.5

    return prims

def arch04(xoff: float, yoff: float, seed: float = 0.0,
           hei: float = 15.0, wid: float = 30.0, rot: float = 0.7,
           per: float = 5.0, sto: int = 2) -> List[PolyPrimitive]:
    """Arched masonry bridge spanning mountain chasms."""
    prims: List[PolyPrimitive] = []
    hoff = 0.0

    for i in range(sto):
        cur_wid = wid * math.pow(0.85, i)
        prims.extend(box(xoff, yoff - hoff, tra=True, hei=hei, wid=cur_wid, rot=rot, wei=1.5, per=per * 0.5))
        prims.extend(rail(xoff, yoff - hoff, seed=i * 0.2, seg=3, wid=cur_wid * 1.2, hei=hei / 3.0, per=per * 0.5, rot=rot, wei=0.5, tra=True))
        prims.extend(pagroof(xoff, yoff - hoff - hei, hei=hei * 1.0, wid=wid * math.pow(0.9, i), rot=rot, wei=1.5, per=per))
        hoff += hei * 1.2

    return prims

def boat01(xoff: float, yoff: float, seed: float = 0.0,
           len_: float = 120.0, sca: float = 1.0, fli: bool = False) -> List[PolyPrimitive]:
    """Traditional wooden sampan fishing boat with fisherman and oar."""
    prims: List[PolyPrimitive] = []
    direction = -1.0 if fli else 1.0

    # Seated fisherman with fishing rod
    prims.extend(man(
        xoff + 20.0 * sca * direction, yoff,
        ite=stick01, hat=hat02, sca=0.5 * sca, fli=not fli,
        len_=[0.0, 30.0, 20.0, 30.0, 10.0, 30.0, 30.0, 30.0, 30.0]
    ))

    plist1 = []
    plist2 = []
    fun1 = lambda px: math.pow(max(0.0, math.sin(px * math.pi)), 0.5) * 7.0 * sca
    fun2 = lambda px: math.pow(max(0.0, math.sin(px * math.pi)), 0.5) * 10.0 * sca

    step = max(2.0, 5.0 * sca)
    total_len = len_ * sca
    curr = 0.0
    while curr < total_len:
        t = curr / total_len
        plist1.append((curr * direction, fun1(t)))
        plist2.append((curr * direction, fun2(t)))
        curr += step

    hull = plist1 + list(reversed(plist2))
    prims.extend(poly(hull, xof=xoff, yof=yoff, fil="white"))
    prims.extend(stroke(
        [(xoff + v[0], yoff + v[1]) for v in hull],
        wid=1.0, fun=lambda sx: math.sin(sx * math.pi * 2.0),
        col="rgba(100,100,100,0.4)"
    ))
    return prims

def transmission_tower01(xoff: float, yoff: float, seed: float = 0.0,
                         hei: float = 100.0, wid: float = 20.0) -> List[PolyPrimitive]:
    """Steel lattice power transmission tower with crossarms and suspension insulators."""
    prims: List[PolyPrimitive] = []

    def quickstroke(pl):
        return stroke(
            [(p[0] + xoff, p[1] + yoff) for p in div(pl, 5)],
            wid=1.0, fun=lambda _: 0.5, col="rgba(100,100,100,0.4)"
        )

    p00 = (-wid * 0.05, -hei)
    p01 = (wid * 0.05, -hei)
    p10 = (-wid * 0.1, -hei * 0.9)
    p11 = (wid * 0.1, -hei * 0.9)
    p20 = (-wid * 0.2, -hei * 0.5)
    p21 = (wid * 0.2, -hei * 0.5)
    p30 = (-wid * 0.5, 0.0)
    p31 = (wid * 0.5, 0.0)

    crossarms = [(0.7, -0.85), (1.0, -0.675), (0.7, -0.5)]
    for arm in crossarms:
        bx = arm[0] * wid
        by = arm[1] * hei
        prims.extend(quickstroke([(-bx, by), (bx, by)]))
        prims.extend(quickstroke([(-bx, by), (0.0, (arm[1] - 0.05) * hei)]))
        prims.extend(quickstroke([(bx, by), (0.0, (arm[1] - 0.05) * hei)]))
        # Insulator strings hanging vertically
        prims.extend(quickstroke([(-bx, by), (-bx, (arm[1] + 0.1) * hei)]))
        prims.extend(quickstroke([(bx, by), (bx, (arm[1] + 0.1) * hei)]))

    l10 = div([p00, p10, p20, p30], 5)
    l11 = div([p01, p11, p21, p31], 5)

    for i in range(len(l10) - 1):
        prims.extend(quickstroke([l10[i], l11[i + 1]]))
        prims.extend(quickstroke([l11[i], l10[i + 1]]))

    prims.extend(quickstroke([p00, p01]))
    prims.extend(quickstroke([p10, p11]))
    prims.extend(quickstroke([p20, p21]))
    prims.extend(quickstroke([p00, p10, p20, p30]))
    prims.extend(quickstroke([p01, p11, p21, p31]))

    return prims
