# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps

ASSETS = Path(
    r"C:\Users\16152\.cursor\projects\d-xwechat-files-wxid-mrim2zak1zta12-50f6-msg-file-2026-08\assets"
)
OUT = Path(__file__).resolve().parent / "illus"
DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"


def find_src() -> Path:
    for f in ASSETS.iterdir():
        if "255b51c3" in f.name:
            return f
    raise FileNotFoundError("走马销源图未找到")


def to_fluo_line(im_in: Image.Image) -> Image.Image:
    arr = np.asarray(im_in.convert("RGB")).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    bright = 0.299 * r + 0.587 * g + 0.114 * b
    med = float(np.median(bright))
    dark = (med - bright) / max(med, 1.0)
    stroke = dark > 0.16
    gray = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8), "L")
    inv = ImageOps.invert(gray)
    opened = inv.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    th = np.asarray(ImageChops.subtract(inv, opened)).astype(np.float32) / 255.0
    line = stroke & ((th > 0.035) | (dark > 0.28))
    a = np.zeros_like(bright, np.float32)
    a[line] = np.clip(dark[line] * 2.2, 0.35, 1.0)
    core = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.MedianFilter(3))
    a = np.asarray(core).astype(np.float32) / 255.0
    g1 = np.asarray(core.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255.0
    g2 = np.asarray(core.filter(ImageFilter.GaussianBlur(3.8))).astype(np.float32) / 255.0
    alpha = np.clip(a * 0.95 + g1 * 0.45 + g2 * 0.22, 0, 1)
    alpha[alpha < 0.06] = 0
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
    return Image.fromarray(
        out[
            max(0, ys.min() - pad) : min(h, ys.max() + pad + 1),
            max(0, xs.min() - pad) : min(w, xs.max() + pad + 1),
        ],
        "RGBA",
    )


def cut_photo(im_in: Image.Image) -> Image.Image:
    arr = np.asarray(im_in.convert("RGBA")).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    bright = (r + g + b) / 3.0
    bg = (bright > 215) & (np.abs(r - g) < 25) & (np.abs(g - b) < 25)
    alpha = np.where(bg, 0, 255).astype(np.float32)
    core = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.MedianFilter(3))
    soft = core.filter(ImageFilter.GaussianBlur(0.7))
    out = arr.copy()
    out[:, :, 3] = np.asarray(soft)
    ys, xs = np.where(out[:, :, 3] > 20)
    pad = 6
    crop = out[
        max(0, ys.min() - pad) : min(out.shape[0], ys.max() + pad + 1),
        max(0, xs.min() - pad) : min(out.shape[1], xs.max() + pad + 1),
    ]
    return Image.fromarray(crop.astype(np.uint8), "RGBA")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    im = Image.open(find_src()).convert("RGBA")
    w, h = im.size
    photo = cut_photo(im.crop((int(w * 0.42), int(h * 0.02), int(w * 0.98), int(h * 0.42))))
    schem = to_fluo_line(im.crop((int(w * 0.04), int(h * 0.44), int(w * 0.96), int(h * 0.96))))

    maxw = max(photo.width, schem.width, 640)
    ps = int(maxw * 0.58)
    photo_r = photo.resize((ps, int(photo.height * ps / photo.width)), Image.LANCZOS)
    schem_r = schem.resize((maxw, int(schem.height * maxw / schem.width)), Image.LANCZOS)
    gap = 18
    canvas = Image.new("RGBA", (maxw, photo_r.height + gap + schem_r.height), (0, 0, 0, 0))
    canvas.paste(photo_r, ((maxw - photo_r.width) // 2, 0), photo_r)
    canvas.paste(schem_r, (0, photo_r.height + gap), schem_r)
    if canvas.width > 700:
        canvas = canvas.resize((700, int(canvas.height * 700 / canvas.width)), Image.LANCZOS)
    canvas.save(OUT / "zouma.png", optimize=True)
    schem_r.save(OUT / "zouma-schem.png", optimize=True)
    print("saved", OUT / "zouma.png", canvas.size)

    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    n = next(x for x in data["nodes"] if x["id"] == "zouma")
    n["illus"] = "data/illus/zouma.png"
    n["illusStyle"] = "photo"
    n["desc"] = "栽榫的一种：榫卯结合后须横向推移方可锁紧，故称走马销；常用于活动构件固定。"
    n["enDesc"] = (
        "A planted tenon that locks only after a lateral slide"
        " (galloping-horse pin); used to fix movable parts."
    )
    n["detail"] = (
        "走马销属于栽榫：先将榫头垂直落入卯眼宽端，再横向推移，使榫头楔入窄端锁紧，"
        "无法上下抽出；反向推移即可拆卸。名称即取横向挪移之意。"
        "常用于传统家具中椅面与扶手等可活动部位的连接，亦见于罗汉床围子等可卸构件。"
    )
    n["enDetail"] = (
        "Zouma pin is a planted tenon: drop the wedge into the wide mouth of the mortise, "
        "then slide sideways so the tenon seats in the narrow end and cannot be pulled out "
        "vertically. Reverse the slide to demount. Common where a chair seat meets the arms, "
        "and on knockdown parts such as luohan-bed rails."
    )
    traits = [
        "栽榫：先垂直落入宽口，再横向推移锁紧",
        "卯眼一端宽一端窄，推移后防上下拔出",
        "反向推移即可拆卸，便于搬运组装",
        "常用于椅面与扶手、罗汉床围子等活动/可卸构件",
    ]
    old = n.get("traits") or []
    for t in traits:
        if t not in old:
            old.append(t)
    n["traits"] = old
    DATA.write_text(m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    print("node updated")


if __name__ == "__main__":
    main()
