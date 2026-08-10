# -*- coding: utf-8 -*-
"""梁思成手稿 → 星座数据 v2（线描骨架版）
流程：裁剪图形单体 → 墨线二值化 → 连通域过滤文字 → 骨架化(中心线) →
骨架图路径追踪（端点/交点为节点）→ 剪除短毛刺 → RDP 折线简化 →
星点=折线顶点（转角处），连线=顺次线段 → 输出 liang-constellations.js
星点稀疏、连线沿笔画，具备星座图的抽象线描感。
"""
from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.morphology import skeletonize, binary_dilation, disk

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_liang"
OUT = ROOT / "liang-constellations.js"

# (文件, 名称, 裁剪框 l,t,r,b, 星点上限)
FIGURES = [
    ("foguang.png", "foguang-section", (40, 100, 758, 600), 160),
    ("foguang.png", "foguang-plan", (700, 30, 970, 235), 70),
    ("pagodas.png", "miaoying-pagoda", (50, 80, 240, 335), 90),
    ("pagodas.png", "kuanghui-pagoda", (285, 25, 495, 270), 90),
    ("pagodas.png", "zhenjue-pagoda", (275, 420, 504, 645), 95),
    ("pagodas.png", "tayuan-pagoda", (60, 480, 235, 700), 80),
    ("pagodas.png", "beihai-pagoda", (80, 738, 210, 830), 65),
    ("pagodas.png", "biyun-pagoda", (250, 706, 504, 960), 100),
    ("taihe.png", "taihe-hall", (30, 10, 935, 430), 160),
    # 独乐寺观音阁正立面
    ("dule-pavilion.png", "dule-pavilion-elev", (40, 20, 990, 720), 180),
    # 六幅剖面（2×3）：佛光寺 / 独乐寺 / 广济寺 / 善化寺大殿 / 隆兴寺转轮藏 / 善化寺山门
    ("sections-six.png", "foguang-daxiong", (8, 28, 360, 330), 140),
    ("sections-six.png", "dule-guanyin-sec", (370, 28, 720, 330), 150),
    ("sections-six.png", "guangji-sansheng", (8, 355, 360, 665), 130),
    ("sections-six.png", "shanhua-main", (370, 355, 720, 665), 130),
    ("sections-six.png", "longxing-zang", (8, 688, 360, 1010), 140),
    ("sections-six.png", "shanhua-shanmen", (370, 688, 720, 1010), 120),
]

MIN_COMP = 58     # 连通域宽或高 ≥ 此值则保留（大图块）
MIN_AREA = 90     # 或像素面积 ≥ 此值则保留（细长线描笔画）
MIN_PATH = 14     # 骨架路径短于此像素数视为毛刺剪除（抬高以强化线描主骨）
MIN_LOOP = 36     # 独立小回环短于此周长剔除
MIN_SEG_NORM = 0.018  # 归一化后过短的连线丢弃，避免网眼填充感


def binarize(img: Image.Image, box):
    g = np.asarray(img.convert("L").crop(box), dtype=np.float32)
    mean = float(g.mean())
    # 浅灰线描手稿：均值偏高，按分位取暗部；深墨手稿仍用均值阈值
    if mean > 180:
        thr = float(np.percentile(g, 24))
        thr = min(215.0, max(130.0, thr))
    else:
        thr = min(140.0, max(90.0, mean * 0.62))
    ink = g < thr
    # 细线轻微膨胀，避免骨架断裂成碎片
    if mean > 180:
        ink = binary_dilation(ink, disk(1))
    return ink


def remove_small_components(ink: np.ndarray) -> np.ndarray:
    h, w = ink.shape
    seen = np.zeros_like(ink, dtype=bool)
    keep = np.zeros_like(ink, dtype=bool)
    for sy in range(h):
        row = ink[sy]
        for sx in np.nonzero(row & ~seen[sy])[0]:
            comp = []
            dq = deque([(sy, int(sx))])
            seen[sy, sx] = True
            minx = maxx = int(sx)
            miny = maxy = sy
            while dq:
                y, x = dq.popleft()
                comp.append((y, x))
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
                y0, y1 = max(0, y - 1), min(h, y + 2)
                x0, x1 = max(0, x - 1), min(w, x + 2)
                for ny in range(y0, y1):
                    for nx in range(x0, x1):
                        if ink[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            dq.append((ny, nx))
            # 大图块（宽或高够）或细长线描（像素面积够）保留；短小文字剔除
            if ((maxx - minx) >= MIN_COMP or (maxy - miny) >= MIN_COMP
                    or len(comp) >= MIN_AREA):
                for y, x in comp:
                    keep[y, x] = True
    return keep


NB8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def trace_paths(skel: np.ndarray):
    """骨架像素图 → 路径列表。端点/交点作节点，路径为两节点间的像素链。"""
    h, w = skel.shape
    pix = set(zip(*np.nonzero(skel)))

    def nbrs(p):
        y, x = p
        return [(y + dy, x + dx) for dy, dx in NB8 if (y + dy, x + dx) in pix]

    deg = {p: len(nbrs(p)) for p in pix}
    nodes = {p for p in pix if deg[p] != 2}
    visited_edges = set()
    paths = []

    def walk(start, first):
        """从节点 start 沿 first 方向走到下一个节点，返回像素链。"""
        chain = [start, first]
        prev, cur = start, first
        while cur not in nodes:
            nxt = [q for q in nbrs(cur) if q != prev]
            if not nxt:
                break
            # 8 邻域可能同时含 prev 的对角伙伴，取未回头的第一个
            prev, cur = cur, nxt[0]
            chain.append(cur)
        return chain

    for nd in nodes:
        for first in nbrs(nd):
            ek = frozenset((nd, first))
            if ek in visited_edges:
                continue
            chain = walk(nd, first)
            for a, b in zip(chain, chain[1:]):
                visited_edges.add(frozenset((a, b)))
            paths.append(chain)

    # 纯回环（无端点/交点）：任取一点断开成路径
    covered = set()
    for p in paths:
        covered.update(p)
    rest = pix - covered
    while rest:
        start = next(iter(rest))
        loop = [start]
        prev, cur = None, start
        while True:
            cand = [q for q in nbrs(cur) if q != prev and q in rest]
            if not cand:
                break
            prev, cur = cur, cand[0]
            if cur == start:
                break
            loop.append(cur)
        rest -= set(loop)
        if len(loop) >= MIN_LOOP:
            loop.append(start)  # 闭合
            paths.append(loop)
    return paths


def rdp(points, eps):
    """Ramer-Douglas-Peucker 折线简化（迭代栈版）"""
    pts = np.asarray(points, dtype=np.float64)
    n = len(pts)
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i0, i1 = stack.pop()
        if i1 <= i0 + 1:
            continue
        a, b = pts[i0], pts[i1]
        ab = b - a
        lab = math.hypot(ab[0], ab[1])
        seg = pts[i0 + 1:i1]
        if lab < 1e-9:
            d = np.hypot(seg[:, 0] - a[0], seg[:, 1] - a[1])
        else:
            d = np.abs(ab[0] * (a[1] - seg[:, 1]) - (a[0] - seg[:, 0]) * ab[1]) / lab
        imax = int(np.argmax(d))
        if d[imax] > eps:
            j = i0 + 1 + imax
            keep[j] = True
            stack.append((i0, j))
            stack.append((j, i1))
    return [tuple(p) for p in pts[keep]]


def simplify_figure(paths, cap):
    """长笔画优先：按路径像素长度降序纳入，星点预算用完为止。
    主轮廓线保留、碎线舍弃；eps 偏大以强化星座折线抽象感。"""
    eps = 4.6
    polys, total = [], 0
    for chain in sorted(paths, key=len, reverse=True):
        if len(chain) < MIN_PATH:
            break  # 已按长度降序，后面全是毛刺
        poly = rdp([(x, y) for y, x in chain], eps)
        if len(poly) < 2:
            continue
        if total + len(poly) > cap:
            continue  # 塞不下就跳过，继续尝试更短的
        polys.append(poly)
        total += len(poly)
        if total >= cap:
            break
    return polys, eps, total


def main():
    out = []
    for fname, name, box, cap in FIGURES:
        img = Image.open(SRC / fname)
        ink = binarize(img, box)
        ink = remove_small_components(ink)
        skel = skeletonize(ink)
        paths = trace_paths(skel)
        polys, eps, total = simplify_figure(paths, cap)

        h, w = ink.shape
        stars, links = [], []
        index = {}

        def pid(p):
            key = (round(p[0], 1), round(p[1], 1))
            if key not in index:
                index[key] = len(stars)
                stars.append([round(p[0] / w, 4), round(p[1] / h, 4)])
            return index[key]

        for poly in polys:
            ids = [pid(p) for p in poly]
            for a, b in zip(ids, ids[1:]):
                if a == b:
                    continue
                # 丢弃过短线段，避免密网眼；保留主笔画折线
                dx = stars[a][0] - stars[b][0]
                dy = stars[a][1] - stars[b][1]
                if (dx * dx + dy * dy) ** 0.5 < MIN_SEG_NORM:
                    continue
                links.append((a, b))

        # 剔除完全无连线的孤立星（噪声残留）
        used = {i for a, b in links for i in (a, b)}
        if len(used) < len(stars):
            remap = {old: i for i, old in enumerate(sorted(used))}
            stars = [stars[old] for old in sorted(used)]
            links = [(remap[a], remap[b]) for a, b in links]

        out.append({
            "name": name,
            "ar": round(w / h, 4),
            "stars": stars,
            "links": links,
        })
        print("%-18s eps=%-5.2f stars=%-4d links=%-4d paths=%d" %
              (name, eps, len(stars), len(links), len(polys)))

    js = "window.LIANG_CONSTELLATIONS = " + json.dumps(out, separators=(",", ":")) + ";\n"
    OUT.write_text(js, encoding="utf-8")
    print("written:", OUT.name, "%.1f KB" % (len(js) / 1024))


if __name__ == "__main__":
    main()
