# -*- coding: utf-8 -*-
"""纠正文献体裁误译 & 易混淆拼音书名；并同步收紧 GENRES 规则。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"
QUALITY = ROOT / "_fix_quality.py"

# 更严的体裁规则（长模式优先；禁止裸「志」一刀切）
GENRES = [
    (r"县志|乡土志|续志", "County gazetteer"),
    (r"河志|安澜志|安澜|水利", "River-conservancy gazetteer"),
    (r"方志", "Local gazetteer"),
    (r"酌中志", "Ming palace memoir"),
    (r"水法", "Treatise on hydraulics"),
    (r"会典", "Collection of dynastic statutes"),
    (r"实录", "Court annals"),
    (r"图书集成", "Section of the imperial encyclopedia Gujin Tushu Jicheng"),
    (r"大典", "Imperial encyclopedia"),
    (r"格致镜原|格致", "Encyclopedic dictionary of origins"),
    (r"武备|兵录|城守|蹶张|神器|枪|砲|水火攻|耕余剩技", "Military treatise"),
    (r"算|数学|测地", "Mathematical and surveying work"),
    (r"蚕|农学|农政", "Agronomy treatise"),
    (r"营造|做法|作法|工程|清册|则例|地宫", "Building manual"),
    (r"工艺学", "Craft-technology treatise"),
    (r"墨苑|墨谱", "Illustrated ink catalogue"),
    (r"园冶", "Treatise on garden design"),
    (r"遵生", "Treatise on regimen and elegant living"),
    (r"新旧约|旧新约|福音", "Chinese edition of Christian scripture"),
    (r"游记|初使", "Travelogue"),
    (r"制造局", "Record of an industrial arsenal"),
    (r"通书|历眼", "Divination almanac"),
    (r"通义|语录|老子|庄子|道宗", "Philosophical commentary"),
    (r"说文|字|骈雅|通俗编|韵|雅俗|名义考|异名|绀珠|谐声", "Philological and lexicographical work"),
    (r"小说", "Collection of tales"),
    (r"国宪|家猷|治政|经济备要", "Statecraft treatise"),
    (r"集|词|稿|纂|遗书|奏档", "Literary collection"),
    (r"康济谱", "Manual of public welfare and relief"),
    (r"谱", "Practical manual"),
    (r"录", "Miscellaneous records"),
]

# 书名英文：纠正易与榫卯/文体混淆的懒拼音
TITLE_EN = {
    "《酌中志》": "Zhuozhongzhi (An Insider's Record of the Ming Palace)",
    "《格致镜原》": "Gezhi Jingyuan (Mirror of Origins of Investigating Things)",
    "《永定河志》": "Yongding He Zhi (Gazetteer of the Yongding River)",
    "《南皮县志》": "Nanpi Xian Zhi (Nanpi County Gazetteer)",
    "《博山县乡土志》": "Boshan Xian Xiangtu Zhi (Local Gazetteer of Boshan County)",
    "《定海县志》": "Dinghai Xian Zhi (Dinghai County Gazetteer)",
    "《威县志》": "Wei Xian Zhi (Wei County Gazetteer)",
    "《畿辅安澜志》": "Jifu Anlan Zhi (Gazetteer of River Pacification in the Capital Region)",
    "《镇海县志》": "Zhenhai Xian Zhi (Zhenhai County Gazetteer)",
    "《临朐续志》": "Linqu Xuzhi (Continued Gazetteer of Linqu County)",
    "《地宫作法》": "Digong Zuofa (Construction Methods for Underground Palaces)",
    "《工艺学》": "Gongyi Xue (Craft Technology)",
    "《耕余剩技》": "Gengyu Shengji (Martial Skills for Hours after Farming)",
    "《国宪家猷》": "Guoxian Jiayou (State Statutes and Family Precepts)",
}


def genre_of(name: str) -> str:
    for pat, g in GENRES:
        if re.search(pat, name):
            return g
    return "Historical text"


def period_of(node: dict, links: list, by_id: dict) -> str:
    """Try dynasty from linked dynasty node."""
    nid = node.get("id")
    for L in links:
        a, b = L.get("source"), L.get("target")
        other = b if a == nid else a if b == nid else None
        if not other:
            continue
        o = by_id.get(other)
        if o and o.get("type") == "dynasty":
            return o.get("en") or o.get("name") or ""
    # fallback from traits/desc
    for t in node.get("traits") or []:
        m = re.search(r"朝代[：:]\s*(\S+)", str(t))
        if m:
            return m.group(1)
    return ""


def main() -> None:
    raw = DATA.read_text(encoding="utf-8")
    m = re.search(r"window\.GRAPH_DATA\s*=\s*(\{.*\})\s*;?\s*$", raw, re.S)
    if not m:
        raise SystemExit("GRAPH_DATA not found")
    data = json.loads(m.group(1))
    by_id = {n["id"]: n for n in data["nodes"]}
    links = data.get("links") or []

    changed = []
    for n in data["nodes"]:
        if n.get("type") != "literature":
            continue
        name = n.get("name") or ""
        genre = genre_of(name)
        period = period_of(n, links, by_id)
        period_bit = (" (%s)" % period) if period else ""
        new_desc = genre + period_bit + "."
        qn = len(n.get("quotes") or [])
        if qn:
            new_detail = (
                "%s%s. Its text preserves period usage of mortise-and-tenon (sunmao) terminology; see the excerpt%s below."
                % (genre, period_bit, "s" if qn > 1 else "")
            )
        else:
            new_detail = (
                "%s%s. A historical source that preserves period vocabulary related to mortise-and-tenon (sunmao) joinery."
                % (genre, period_bit)
            )

        old_en = n.get("en") or ""
        old_desc = n.get("enDesc") or ""
        old_detail = n.get("enDetail") or ""
        new_en = TITLE_EN.get(name, old_en)

        touch = False
        if new_en != old_en:
            n["en"] = new_en
            touch = True
        # 只改明显错的或弱标签
        should_fix_desc = (
            name in TITLE_EN
            or old_desc.strip() in ("Gazetteer.", "Historical text.", "Text.")
            or (genre != "Gazetteer" and old_desc.startswith("Gazetteer"))
            or (genre.startswith("County") and old_desc.startswith("Gazetteer"))
            or old_desc.rstrip(".") != genre and name in (
                "《酌中志》", "《格致镜原》", "《地宫作法》", "《工艺学》",
                "《耕余剩技》", "《国宪家猷》",
            )
        )
        if should_fix_desc and (old_desc != new_desc or old_detail != new_detail):
            n["enDesc"] = new_desc
            n["enDetail"] = new_detail
            touch = True
        if touch:
            changed.append((name, old_en, new_en, old_desc, new_desc))

    out = "window.GRAPH_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    DATA.write_text(out, encoding="utf-8")

    # 收紧 _fix_quality.py 里的 GENRES，避免以后再跑回错
    q = QUALITY.read_text(encoding="utf-8")
    new_block = "GENRES = [\n" + "".join(
        '    (r"%s", "%s"),\n' % (pat.replace("\\", "\\\\") if False else pat, g)
        for pat, g in GENRES
    ) + "]\n"
    q2, nsub = re.subn(
        r"GENRES = \[[\s\S]*?\]\nDYN_EN",
        new_block + "DYN_EN",
        q,
        count=1,
    )
    if nsub:
        QUALITY.write_text(q2, encoding="utf-8")

    print("updated", len(changed), "literature nodes")
    for row in changed:
        print("---", row[0])
        if row[1] != row[2]:
            print("  en:", row[1], "=>", row[2])
        if row[3] != row[4]:
            print("  desc:", row[3], "=>", row[4])


if __name__ == "__main__":
    main()
