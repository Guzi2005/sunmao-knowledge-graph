# -*- coding: utf-8 -*-
"""从构架示意图中裁切小图插图：穿榫 / 阴阳榫 / 巴掌榫。"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps

ASSETS = Path(
    r"C:\Users\16152\.cursor\projects\d-xwechat-files-wxid-mrim2zak1zta12-50f6-msg-file-2026-08\assets"
)
OUT = Path(__file__).resolve().parent / "illus"
DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"

JOBS = [
    # key in filename, node id, crop fractions (x0,y0,x1,y1)
    ("786dd2de", "chuansun", (0.52, 0.02, 0.98, 0.52), "穿榫"),
    ("84298f73", "阴阳榫", (0.52, 0.01, 0.99, 0.38), "阴阳榫"),
    ("84298f73", "巴掌榫", (0.52, 0.34, 0.99, 0.72), "巴掌榫"),
]

KNOWLEDGE = {
    "chuansun": {
        "desc": "榫头穿过柱身卯眼后外露，常以销或楔钉锁紧；多用于川、不连续枋与柱的节点。",
        "enDesc": "A through-tenon pierces the column mortise and is often keyed with a wedge; used where discontinuous fang meet columns.",
        "detail_append": (
            "穿榫用于川枋或不连续枋与柱的交接：枋端出长榫穿透柱身，榫头外露端再贯销（楔）锁紧，"
            "使枋与柱在轴向与侧向均不易脱出。常见于穿斗等构架中横向构件穿柱的节点。"
        ),
        "traits_add": [
            "榫头穿透柱身，外露端可贯销锁紧",
            "用于川、不连续枋与柱节点",
            "穿斗构架中横向构件穿柱的典型做法",
        ],
    },
    "阴阳榫": {
        "desc": "连续枋与柱节点的对穿做法：两枋榫头高低错叠（阴阳）同入柱卯，再以销固定。",
        "enDesc": "Yin–yang tenons: opposing continuous fang enter one column with stepped overlapping tenons, then keyed.",
        "detail_append": (
            "阴阳榫（阔榫一类）用于连续枋与柱：左右枋榫做成高低错口，在柱身卯眼内相叠咬合，"
            "再以销钉固定，既保持枋路贯通，又避免两榫在柱心互相顶死。"
        ),
        "traits_add": [
            "连续枋左右入柱，榫头阴阳错叠",
            "柱身同卯收纳，销钉锁紧",
            "利于纵向枋路贯通的构架",
        ],
    },
    "巴掌榫": {
        "desc": "连续枋入柱时榫端做成掌状钩搭，互相扣合后再销紧的节点做法。",
        "enDesc": "Palm tenon: hooked scarf-like tenon ends clasp inside the column, then pinned.",
        "detail_append": (
            "巴掌榫亦用于连续枋与柱：榫端削成掌状（或钩搭斜面），两枋在柱卯内互相扣合，"
            "再贯销固定，外形如双手相握，抗拉拔与防错位性能较好。"
        ),
        "traits_add": [
            "榫端掌状/钩搭，柱内互相扣合",
            "常配合销钉锁紧",
            "多见于连续枋与柱的交接",
        ],
    },
}


def find_src(key: str) -> Path:
    for f in ASSETS.iterdir():
        if key in f.name:
            return f
    raise FileNotFoundError(key)


def to_fluo(im_in: Image.Image) -> Image.Image:
    arr = np.asarray(im_in.convert("RGB")).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    bright = 0.299 * r + 0.587 * g + 0.114 * b
    med = float(np.median(bright))
    dark = (med - bright) / max(med, 1.0)
    # keep brown-highlighted wood + ink lines
    brown = (r > g + 5) & (r > 80) & (bright < 210)
    stroke = (dark > 0.10) | brown
    gray = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8), "L")
    inv = ImageOps.invert(gray)
    opened = inv.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    th = np.asarray(ImageChops.subtract(inv, opened)).astype(np.float32) / 255.0
    line = stroke & ((th > 0.025) | (dark > 0.18) | brown)
    a = np.zeros_like(bright, np.float32)
    a[line] = np.clip(np.maximum(dark[line], 0.25) * 2.2, 0.35, 1.0)
    a[brown] = np.maximum(a[brown], 0.75)
    core = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.MedianFilter(3))
    a = np.asarray(core).astype(np.float32) / 255.0
    g1 = np.asarray(core.filter(ImageFilter.GaussianBlur(1.3))).astype(np.float32) / 255.0
    g2 = np.asarray(core.filter(ImageFilter.GaussianBlur(3.2))).astype(np.float32) / 255.0
    alpha = np.clip(a * 0.95 + g1 * 0.4 + g2 * 0.18, 0, 1)
    alpha[alpha < 0.05] = 0
    h, w = alpha.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[:, :, 0] = 255
    out[:, :, 1] = 255
    out[:, :, 2] = 255
    out[:, :, 3] = (alpha * 255).astype(np.uint8)
    ys, xs = np.where(alpha > 0.08)
    if len(xs) == 0:
        return Image.fromarray(out, "RGBA")
    pad = 8
    art = Image.fromarray(
        out[
            max(0, ys.min() - pad) : min(h, ys.max() + pad + 1),
            max(0, xs.min() - pad) : min(w, xs.max() + pad + 1),
        ],
        "RGBA",
    )
    if art.width > 560:
        art = art.resize((560, int(art.height * 560 / art.width)), Image.LANCZOS)
    return art


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    by = {n["id"]: n for n in data["nodes"]}

    for key, nid, box, label in JOBS:
        src = find_src(key)
        im = Image.open(src).convert("RGBA")
        w, h = im.size
        x0, y0, x1, y1 = box
        crop = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        art = to_fluo(crop)
        path = OUT / f"{nid}.png"
        # Windows-safe filename for Chinese ids
        safe = {"阴阳榫": "yinyang", "巴掌榫": "bazhang"}.get(nid, nid)
        path = OUT / f"{safe}.png"
        art.save(path, optimize=True)
        rel = f"data/illus/{safe}.png"
        print(label, art.size, "->", rel)

        n = by[nid]
        n["illus"] = rel
        n["illusStyle"] = "line"
        info = KNOWLEDGE[nid]
        if info.get("desc"):
            n["desc"] = info["desc"]
        if info.get("enDesc"):
            n["enDesc"] = info["enDesc"]
        traits = n.get("traits") or []
        for t in info.get("traits_add") or []:
            if t not in traits:
                traits.append(t)
        n["traits"] = traits
        ap = info.get("detail_append") or ""
        d = n.get("detail") or ""
        if ap and ap[:10] not in d:
            n["detail"] = (d + "\n" + ap).strip() if d else ap

        # light cross-links
    exist = {(l["source"], l["target"]) for l in data["links"]}
    for s, t, rel, ren in [
        ("chuansun", "阴阳榫", "近缘", "related"),
        ("chuansun", "巴掌榫", "近缘", "related"),
        ("阴阳榫", "巴掌榫", "近缘", "related"),
        ("chuandou", "chuansun", "常用", "commonly uses"),
    ]:
        if s in by and t in by and (s, t) not in exist and (t, s) not in exist:
            data["links"].append({"source": s, "target": t, "relation": rel, "relationEn": ren})
            exist.add((s, t))

    DATA.write_text(
        m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("done")


if __name__ == "__main__":
    main()
