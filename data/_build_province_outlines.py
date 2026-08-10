# -*- coding: utf-8 -*-
"""从阿里云 DataV 省级 GeoJSON 生成归一化轮廓，供 THREE.ExtrudeGeometry 使用；
并补齐图谱中缺失的省级行政区节点（共 34 个）。
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GEO = Path(
    r"C:\Users\16152\.cursor\projects\d-xwechat-files-wxid-mrim2zak1zta12-50f6-msg-file-2026-08"
    r"\agent-tools\dc721689-09f6-47fb-bab2-fb7c7951e288.txt"
)
OUT_JS = ROOT / "province-outlines.js"
DATA = ROOT / "sunmao-graph.source.js"

# 官方省级行政区 → 节点 id / 英文 / 默认隶属一级分区
PROV_META = {
    "北京": ("beijing", "Beijing", "north"),
    "天津": ("tianjin", "Tianjin", "north"),
    "河北": ("hebei", "Hebei", "north"),
    "山西": ("shanxi", "Shanxi", "north"),
    "内蒙古": ("neimenggu", "Inner Mongolia", "north"),
    "辽宁": ("liaoning", "Liaoning", "north"),
    "吉林": ("jilin", "Jilin", "north"),
    "黑龙江": ("heilongjiang", "Heilongjiang", "north"),
    "上海": ("shanghai", "Shanghai", "jiangnan"),
    "江苏": ("jiangsu", "Jiangsu", "jiangnan"),
    "浙江": ("zhejiang", "Zhejiang", "jiangnan"),
    "安徽": ("anhui", "Anhui", "jiangnan"),
    "福建": ("fujian", "Fujian", "lingnan"),
    "江西": ("jiangxi", "Jiangxi", "jiangnan"),
    "山东": ("shandong", "Shandong", "north"),
    "河南": ("henan", "Henan", "north"),
    "湖北": ("hubei", "Hubei", "jiangnan"),
    "湖南": ("hunan", "Hunan", "jiangnan"),
    "广东": ("guangdong", "Guangdong", "lingnan"),
    "广西": ("guangxi", "Guangxi", "lingnan"),
    "海南": ("hainan", "Hainan", "lingnan"),
    "重庆": ("chongqing", "Chongqing", "xinan"),
    "四川": ("sichuan", "Sichuan", "xinan"),
    "贵州": ("guizhou", "Guizhou", "xinan"),
    "云南": ("yunnan", "Yunnan", "xinan"),
    "西藏": ("xizang", "Tibet", "qingzang"),
    "陕西": ("shaanxi", "Shaanxi", "xinan"),
    "甘肃": ("gansu", "Gansu", "xinan"),
    "青海": ("qinghai", "Qinghai", "qingzang"),
    "宁夏": ("ningxia", "Ningxia", "xinan"),
    "新疆": ("xinjiang", "Xinjiang", "xinan"),
    "台湾": ("taiwan", "Taiwan", "lingnan"),
    "香港": ("xianggang", "Hong Kong", "lingnan"),
    "澳门": ("aomen", "Macau", "lingnan"),
}


def short_name(full: str) -> str | None:
    if not full:
        return None
    for p in sorted(PROV_META, key=len, reverse=True):
        if full.startswith(p):
            return p
    return None


def ring_area(ring):
    a = 0.0
    n = len(ring)
    for i in range(n - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        a += x1 * y2 - x2 * y1
    return abs(a) * 0.5


def largest_outer_ring(geom):
    rings = []
    if geom["type"] == "Polygon":
        rings.append(geom["coordinates"][0])
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            rings.append(poly[0])
    if not rings:
        return None
    return max(rings, key=ring_area)


def dist_point_seg(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def douglas_peucker(pts, eps):
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = dist_point_seg(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = douglas_peucker(pts[: idx + 1], eps)
        right = douglas_peucker(pts[idx:], eps)
        return left[:-1] + right
    return [pts[0], pts[-1]]


def simplify_ring(ring, target=56):
    # 去闭合点
    pts = [(float(p[0]), float(p[1])) for p in ring]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) <= target:
        return pts
    # 按经纬跨度估 epsilon
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    eps = span * 0.012
    for _ in range(12):
        simp = douglas_peucker(pts + [pts[0]], eps)[:-1]
        if abs(len(simp) - target) <= 8 or len(simp) <= target:
            pts = simp
            if len(pts) <= target + 4:
                break
            eps *= 1.35
        else:
            eps *= 0.72
    # 仍过多则均匀抽样
    if len(pts) > target + 10:
        step = len(pts) / target
        pts = [pts[int(i * step) % len(pts)] for i in range(target)]
    return pts


def normalize(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    cx = (minx + maxx) * 0.5
    cy = (miny + maxy) * 0.5
    # 经度→x，纬度→y；按纬度缩放经度近似等积观感
    mid_lat = math.radians(cy)
    sx = math.cos(mid_lat) if abs(math.cos(mid_lat)) > 0.2 else 0.2
    hx = (maxx - minx) * sx * 0.5 or 1e-6
    hy = (maxy - miny) * 0.5 or 1e-6
    s = 0.92 / max(hx, hy)
    out = []
    for x, y in pts:
        # 地图 y 北为正；Three Shape 通常 y 上为正，保持
        out.append([round((x - cx) * sx * s, 4), round((y - cy) * s, 4)])
    return out


def ensure_ccw(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    if a < 0:
        pts = list(reversed(pts))
    return pts


def build_outlines():
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    outlines = {}
    found = set()
    for f in geo["features"]:
        props = f.get("properties") or {}
        full = props.get("name") or ""
        if props.get("adcode") == "100000_JD":
            continue
        name = short_name(full)
        if not name:
            print("skip", full)
            continue
        py, _, _ = PROV_META[name]
        ring = largest_outer_ring(f["geometry"])
        if not ring:
            continue
        pts = ensure_ccw(normalize(simplify_ring(ring, 60)))
        outlines["prov_" + py] = pts
        found.add(name)
        print(f"OK {name} pts={len(pts)}")
    missing = [p for p in PROV_META if p not in found]
    if missing:
        raise SystemExit("轮廓缺失: " + ",".join(missing))
    lines = [
        "/* 中国省级行政区轮廓（基于官方区划边界简化，已归一化）——挤出成柱体 */",
        "/* 含 34 个省级行政区：23省+5自治区+4直辖市+2特别行政区 */",
        "window.PROVINCE_OUTLINES = " + json.dumps(outlines, ensure_ascii=False, separators=(",", ":")) + ";",
        f"window.PROVINCE_OUTLINE_COUNT = {len(outlines)};",
    ]
    OUT_JS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT_JS, "count", len(outlines))


def ensure_province_nodes():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    if not m:
        raise SystemExit("GRAPH_DATA not found")
    data = json.loads(m.group(2))
    nodes, links = data["nodes"], data["links"]
    by_id = {n["id"]: n for n in nodes}
    exist_pairs = {(l["source"], l["target"]) for l in links}
    added_n = added_l = 0
    for name, (py, en, parent) in PROV_META.items():
        pid = "prov_" + py
        if pid not in by_id:
            node = {
                "id": pid,
                "name": name,
                "en": en,
                "type": "region",
                "level": 2,
                "desc": "二级地域节点：%s（中国%s）。" % (name, {
                    "直辖市": "直辖市", "自治区": "自治区", "特区": "特别行政区"
                }.get(
                    {"北京": "直辖市", "天津": "直辖市", "上海": "直辖市", "重庆": "直辖市",
                     "内蒙古": "自治区", "广西": "自治区", "西藏": "自治区", "宁夏": "自治区", "新疆": "自治区",
                     "香港": "特区", "澳门": "特区"}.get(name, "省"),
                    "省",
                )),
                "enDesc": "Second-level region node: %s." % en,
                "detail": "%s为中国%s。" % (name, {
                    "直辖市": "直辖市", "自治区": "自治区", "特区": "特别行政区"
                }.get(
                    {"北京": "直辖市", "天津": "直辖市", "上海": "直辖市", "重庆": "直辖市",
                     "内蒙古": "自治区", "广西": "自治区", "西藏": "自治区", "宁夏": "自治区", "新疆": "自治区",
                     "香港": "特区", "澳门": "特区"}.get(name, "省"),
                    "省",
                )),
                "enDetail": "%s is a provincial-level administrative division of China." % en,
                "traits": [],
                "refs": [],
                "adminType": {"北京": "直辖市", "天津": "直辖市", "上海": "直辖市", "重庆": "直辖市",
                     "内蒙古": "自治区", "广西": "自治区", "西藏": "自治区", "宁夏": "自治区", "新疆": "自治区",
                     "香港": "特区", "澳门": "特区"}.get(name, "省"),
            }
            nodes.append(node)
            by_id[pid] = node
            added_n += 1
        # 隶属分区边：仅当尚无省→一级分区边时补上
        has_parent = any(
            l["source"] == pid and by_id.get(l["target"], {}).get("type") == "region"
            and by_id[l["target"]].get("level") != 2
            and not str(l["target"]).startswith("prov_")
            for l in links
        )
        # 一级分区 id 无 level；用非 prov_ 的 region
        if not has_parent and parent in by_id:
            if (pid, parent) not in exist_pairs:
                links.append({
                    "source": pid,
                    "target": parent,
                    "relation": "隶属分区",
                    "relationEn": "Subregion of",
                })
                exist_pairs.add((pid, parent))
                added_l += 1
    DATA.write_text(
        m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("graph: +nodes", added_n, "+links", added_l, "L2=", sum(1 for n in nodes if n.get("type")=="region" and n.get("level")==2))


if __name__ == "__main__":
    build_outlines()
    ensure_province_nodes()
