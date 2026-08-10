# -*- coding: utf-8 -*-
"""《东南周末讲坛选粹 11》p.260 线描 → 荧光插图，并写入对应榫卯节点。"""
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

REF = (
    "《东南周末讲坛选粹》编委会：《东南周末讲坛选粹》11，"
    "福建海峡文艺出版社，2021年9月，第260页。"
)

# 源图特征串 → 节点 id
JOBS = [
    ("b82c69da", "chajian", "插肩榫"),
    ("cfabb1fa", "jiatou", "夹头榫"),
    ("d4f4d50d", "baojian", "抱肩榫"),
    ("7dc2023b", "xieding", "楔钉榫"),
]

KNOWLEDGE = {
    "chajian": {
        "traits_add": [
            "腿足出榫并削斜肩，牙板端做斜口包夹",
            "转角呈 V 形包肩，外观简洁、受力明确",
            "多用于无束腰案形结体桌案",
        ],
        "detail_append": (
            "插肩榫见于案形结体：腿足上端出榫，外侧削成斜肩；"
            "牙条端头开相应斜口插合包夹，装配后转角常见 V 形包肩线。"
            "结构与观感兼顾，是无束腰案类的典型节点。"
        ),
    },
    "jiatou": {
        "traits_add": [
            "腿足上端开口，夹住牙条与牙头",
            "案面大边压合，形成“夹头”承托",
            "圆足常见；牙头两侧张开增强稳定与装饰",
        ],
        "detail_append": (
            "夹头榫是案类家具标志做法：圆足（或方足）上端开长口，"
            "夹持牙条与两侧牙头，其上再承大边与案面，重量经牙头分散至腿足。"
            "爆炸图可见案面、大边、牙条、牙头与圆足正侧面关系。"
        ),
    },
    "baojian": {
        "traits_add": [
            "有束腰家具腿足与束腰、牙条的 45° 斜肩扣合",
            "腿足出榫入大边卯眼，斜肩与牙条相抱",
            "外观转角斜缝清晰，结构复杂而稳固",
        ],
        "detail_append": (
            "抱肩榫用于有束腰家具：腿足上端出榫穿入大边，"
            "肩部做成 45° 斜肩并开槽，与牙条斜口相抱扣合，"
            "束腰、牙条与腿足在转角形成一体。工艺难度高于夹头榫。"
        ),
    },
    "xieding": {
        "traits_add": [
            "弧形材对接：两端出榫相叠，中贯楔钉锁死",
            "常见于圈椅扶手等曲材接长",
            "楔钉防止受拉开榫，可拆可紧",
        ],
        "detail_append": (
            "楔钉榫专用于圈椅等曲材接长：两段圆材端头做高低相叠的榫口，"
            "合拢后中部留出钉眼，打入楔钉（销）锁紧，防止拉开。"
            "装配后外轮廓圆顺，仅见楔钉端头。"
        ),
    },
}


def find_src(key: str) -> Path:
    for f in ASSETS.iterdir():
        if key in f.name:
            return f
    raise FileNotFoundError(key)


def to_fluo(im_in: Image.Image) -> Image.Image:
    # 裁掉底部书名大字，保留图与小标注
    w, h = im_in.size
    im_in = im_in.crop((int(w * 0.02), int(h * 0.02), int(w * 0.98), int(h * 0.88)))
    arr = np.asarray(im_in.convert("RGB")).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    bright = 0.299 * r + 0.587 * g + 0.114 * b
    med = float(np.median(bright))
    dark = (med - bright) / max(med, 1.0)
    stroke = dark > 0.12
    gray = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8), "L")
    inv = ImageOps.invert(gray)
    opened = inv.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    th = np.asarray(ImageChops.subtract(inv, opened)).astype(np.float32) / 255.0
    line = stroke & ((th > 0.03) | (dark > 0.22))
    a = np.zeros_like(bright, np.float32)
    a[line] = np.clip(dark[line] * 2.4, 0.3, 1.0)
    core = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.MedianFilter(3))
    a = np.asarray(core).astype(np.float32) / 255.0
    g1 = np.asarray(core.filter(ImageFilter.GaussianBlur(1.4))).astype(np.float32) / 255.0
    g2 = np.asarray(core.filter(ImageFilter.GaussianBlur(3.6))).astype(np.float32) / 255.0
    alpha = np.clip(a * 0.95 + g1 * 0.42 + g2 * 0.2, 0, 1)
    alpha[alpha < 0.05] = 0
    hh, ww = alpha.shape
    out = np.zeros((hh, ww, 4), np.uint8)
    out[:, :, 0] = 255
    out[:, :, 1] = 255
    out[:, :, 2] = 255
    out[:, :, 3] = (alpha * 255).astype(np.uint8)
    ys, xs = np.where(alpha > 0.08)
    if len(xs) == 0:
        return Image.fromarray(out, "RGBA")
    pad = 10
    art = Image.fromarray(
        out[
            max(0, ys.min() - pad) : min(hh, ys.max() + pad + 1),
            max(0, xs.min() - pad) : min(ww, xs.max() + pad + 1),
        ],
        "RGBA",
    )
    if art.width > 720:
        art = art.resize((720, int(art.height * 720 / art.width)), Image.LANCZOS)
    return art


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    by = {n["id"]: n for n in data["nodes"]}

    for key, nid, name in JOBS:
        src = find_src(key)
        art = to_fluo(Image.open(src))
        rel = f"data/illus/{nid}.png"
        art.save(OUT / f"{nid}.png", optimize=True)
        print(name, art.size, "->", rel)

        n = by[nid]
        n["illus"] = rel
        n["illusStyle"] = "line"  # 荧光线描
        if "illusStyle" in n and n["illusStyle"] == "photo":
            n["illusStyle"] = "line"
        refs = n.get("refs") or []
        if REF not in refs:
            refs.append(REF)
        n["refs"] = refs

        info = KNOWLEDGE.get(nid) or {}
        traits = n.get("traits") or []
        for t in info.get("traits_add") or []:
            if t not in traits:
                traits.append(t)
        n["traits"] = traits
        ap = info.get("detail_append") or ""
        d = n.get("detail") or n.get("desc") or ""
        if ap and ap[:12] not in d:
            n["detail"] = (d + "\n" + ap).strip() if d else ap

    DATA.write_text(
        m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("done")


if __name__ == "__main__":
    main()
