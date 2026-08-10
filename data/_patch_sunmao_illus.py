# -*- coding: utf-8 -*-
"""把海报知识与荧光线描插图写入对应榫卯节点；补齐缺失榫型。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

# illus 文件名 → 节点 id（新建时用拼音 id）
ILLUS_MAP = {
    "caokou": "caokou",
    "shuangsun": "双榫",
    "shuangjia": "shuangjia",
    "yanwei": "yanwei",
    "gejian": "gejian",
    "chuandai": "chuandai",
    "gougua": "gougua",
    "yuansun": "yuansun",
    "zongjiao": "zongjiao",
    "qikou": "qikou",
    "changduan": "changduan",
    "tuojiao": "tuojiao",
    "chajian": "chajian",
}

KNOWLEDGE = {
    "caokou": {
        "name": "槽口榫",
        "en": "Groove Joint",
        "desc": "最基本的通槽嵌榫连接：一料开通长槽，另一料端头或边棱做榫舌，成 T / L 形接合。",
        "enDesc": "A basic groove-and-tongue join: one piece carries a continuous groove, the other a tongue, forming T- or L-shaped assemblies.",
        "detail": "槽口榫是最基本、最简单的榫卯连接之一。木料上开一条通长的槽，另一块木料的端头或边缘制成榫舌，形成“T”形或“L”形连接，接合处常留一条通长缝隙。强度一般，多用于非承重或次要结构。",
        "enDetail": "Among the simplest joins: a continuous groove receives a tongue. Strength is moderate; typical for secondary, non-load-bearing assemblies.",
        "traits": [
            "通长槽口 + 榫舌，结构简明",
            "可成 T 形或 L 形连接，接合缝通长可见",
            "常用于柜背板、隔板、抽屉侧板与面板、箱体简单拼接",
        ],
    },
    "双榫": {
        "traits_add": [
            "同一连接部位并排两榫头，增大胶合与咬合面",
            "适合较宽或受力较大的构件",
            "常见于橱柜门、大型框架等需加固部位",
        ],
        "detail_append": "双榫在同一连接部位制作两个并排榫头，增强胶合面积与咬合力，使连接更稳固，适合较宽或受力较大的构件；橱柜门、大型框架等需特别加固处常用。",
    },
    "shuangjia": {
        "name": "双夹榫",
        "en": "Double Clip Tenon",
        "desc": "双榫的特殊形式：构件一端做成两平行榫头如夹叉，夹入或插入另一构件，形成较隐蔽的复合连接。",
        "enDesc": "A forked double tenon that clips or inserts into another member—often a hidden, multi-directional join.",
        "detail": "双夹榫是双榫的特殊形式。构件一端做成两个平行榫头，像夹子一样插入或夹住另一构件，形成较复杂的隐蔽连接，常用于非常规角度的接合。",
        "enDetail": "Two parallel tenons act like a clip/fork into the mating piece, enabling complex hidden joins and awkward angles.",
        "traits": [
            "端头双平行榫如夹叉，夹持对件",
            "可成隐蔽复合节点，适非常规角度",
            "常用于桌案类腿足与牙板连接，以及需多向承力的框架",
        ],
    },
    "yanwei": {
        "traits_add": [
            "榫头梯台形（燕尾），受拉自锁，抗拉极强",
            "端头可见成排梯形榫，识别度高且具装饰性",
            "多用于明式家具可见部位、抽屉、箱匣、柜框",
        ],
        "detail_append": "燕尾榫被视为最牢固的榫卯之一：榫头呈梯形，制作复杂但抗拉极强；板端可见成排梯形榫，兼具结构与装饰。高档家具可见部位、抽屉、箱匣与柜框常用。",
    },
    "gejian": {
        "traits_add": [
            "榫头两侧做三角格肩，增大接触面与强度",
            "横材端头未必居中于竖材侧面时的直角连接",
            "有大格肩、小格肩、虚格肩等变体；桌凳柜架横枨入腿常用",
        ],
        "detail_append": "格肩榫为增大接触面积与强度，在榫头两侧做出三角形格肩，与卯口缺口严密配合；用于两木成直角连接，且横材端头不必正对竖材中线。桌、凳、柜架的横枨与腿足结合广泛使用，并有大格肩、小格肩、虚格肩等变体。",
    },
    "chuandai": {
        "traits_add": [
            "板背开上小下大（或一端宽一端窄）的梯形通槽",
            "梯形长榫自宽端打入贯通，锁牢防翘曲又容湿胀干缩",
            "用于桌案面、柜门、椅座等大幅薄板背面",
        ],
        "detail_append": "穿带榫专为防止大幅薄板翘曲变形：板背开若干梯形通槽（常一端宽一端窄），以梯形截面长榫自宽端打入贯通。穿带多露于家具背面；桌面、案面、柜门、椅座等大幅薄板常用。",
    },
    "gougua": {
        "name": "勾挂榫",
        "en": "Hook-and-Hang Tenon",
        "desc": "利用榫头特殊造型先斜向插入再平移或旋转勾挂锁合，牢固又可拆卸。",
        "enDesc": "A hooking tenon inserted obliquely then slid or rotated to lock—strong yet demountable.",
        "detail": "勾挂榫利用榫头的特殊形状进行挂接锁合：先斜向插入，再平移或旋转，使榫头勾住卯口，实现牢固且可拆卸的连接。安装方式如“挂钩”，非垂直打入，而是滑入或旋入。",
        "enDetail": "The tenon hooks after an oblique insertion and a slide/turn—like hanging a hook—yielding a firm but demountable joint.",
        "traits": [
            "斜向入卯后平移/旋转勾挂锁定",
            "牢固且可拆，便于搬运组装",
            "常见于霸王枨与腿足/桌面连接，以及案几类可拆家具",
        ],
    },
    "yuansun": {
        "name": "圆榫",
        "en": "Dowel / Round Tenon",
        "desc": "以独立圆柱木销插入两构件对应圆孔完成连接，加工高效，多依赖胶合与对位精度。",
        "enDesc": "A separate cylindrical dowel into matched round holes—fast to make, glue- and alignment-dependent.",
        "detail": "圆榫使用独立的圆柱形木棍作为连接件，插入两构件对应圆孔中。优点是加工效率高；缺点是多依赖胶水和钻孔对位精度。传统榫头不可见，内部圆形木销是现代板式家具的典型特征。",
        "enDetail": "A loose cylindrical pin joins two bored holes. Efficient to produce; relies on glue and hole alignment. Typical of modern panel furniture when no tenon end shows.",
        "traits": [
            "独立圆柱销连接，榫头外不可见",
            "加工快，但对孔位与胶合要求高",
            "用于现代实木/板式框架，亦用于修复加固",
        ],
    },
    "zongjiao": {
        "traits_add": [
            "三根材端均做 45° 格角，内部再出榫卯咬合",
            "外观呈粽子尖角，六条 45° 斜线交汇",
            "多用于高档柜匣顶角；外观简练、工艺极难",
        ],
        "detail_append": "粽角榫将三根木料端头均裁成 45° 斜角，内部再挖榫卯相互咬合，于直角转角相遇；外观如粽子尖角。柜类、匣类顶角常见，表面简洁而做工极复杂。",
    },
    "qikou": {
        "traits_add": [
            "板边一凸榫舌、一凹槽口，企口相嵌拼大平面",
            "防错动与翘曲，拼缝齐平",
            "多用于地板、门心板、桌面、柜门等宽板拼合",
        ],
        "detail_append": "企口榫可视为槽口榫用于板边拼合的形式：一板边做凸出榫舌，另一板边做凹槽，两板紧密嵌合成更大平面，有效防止错动与翘曲。地板、门板、桌面、柜门等宽板拼接常用。",
    },
    "changduan": {
        "traits_add": [
            "腿足上端分出长短（或粗细）两榫，分入面框不同卯眼",
            "分散应力，降低开裂风险",
            "桌案椅凳等腿足与面框结合的基本做法",
        ],
        "detail_append": "长短榫主要用于腿足与面框的连接：将一榫分为长短两段（或一粗一细），分别插入面框不同卯眼，分散应力、减少木材开裂。桌、案、椅、凳等面框与腿足结合处常见。",
    },
    "tuojiao": {
        "name": "托角榫",
        "en": "Supporting Corner Tenon",
        "desc": "腿足上端做成复合榫形，与束腰、牙条严密扣合，在承面转角形成托承式节点。",
        "enDesc": "A compound tenon at the leg top locking waist and apron—supporting the panel corner in waisted furniture.",
        "detail": "托角榫是一种复合榫卯：腿足上端做成特定榫形，与家具的束腰、牙条严密结合，在转角形成具有托承作用的结构节点。常见于有束腰家具腿足与承面交接处。",
        "enDetail": "A compound join where the leg top locks into the waist and apron, cradling the corner—typical of Ming-style waisted tables, luohan beds and chairs.",
        "traits": [
            "腿足上端复合榫，扣合束腰与牙条",
            "转角托承，结构与造型一体",
            "明式有束腰家具（束腰方桌、罗汉床、椅具）标志做法",
        ],
    },
    "chajian": {
        "traits_add": [
            "腿足出榫同时外侧削成斜肩，牙板端做斜口包夹",
            "转角常见 V 形包肩口，外观流畅且强度高",
            "无束腰案形结体桌案常用",
        ],
        "detail_append": "插肩榫主要用于腿足与牙板连接：腿足出榫，外侧削成斜肩；牙板端头做相应斜口包夹斜肩，形成强度高、过渡流畅的节点，转角常呈 V 形包口。无束腰案形结体家具常用。",
    },
}

NEW_LINKS = [
    # 新榫型挂到家具/工艺语境
    ("jiaju", "caokou", "常用", "commonly uses"),
    ("jiaju", "shuangjia", "常用", "commonly uses"),
    ("jiaju", "gougua", "常用", "commonly uses"),
    ("bawang", "gougua", "采用", "employs"),
    ("jiaju", "yuansun", "亦用", "also uses"),
    ("baojian", "tuojiao", "近缘", "related"),
    ("jiaju", "tuojiao", "常用", "commonly uses"),
    ("双榫", "shuangjia", "变体", "variant of"),
    ("qikou", "caokou", "近缘", "related"),
]


def merge_traits(old, add):
    seen = set(old or [])
    out = list(old or [])
    for t in add or []:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    nodes, links = data["nodes"], data["links"]
    by_id = {n["id"]: n for n in nodes}
    exist_pairs = {(l["source"], l["target"]) for l in links}

    added = updated = 0
    for illus_key, nid in ILLUS_MAP.items():
        info = KNOWLEDGE.get(nid) or KNOWLEDGE.get(illus_key) or {}
        illus_path = f"data/illus/{illus_key}.png"

        if nid not in by_id:
            # 必须是新建条目
            base = info
            if not base.get("name"):
                raise SystemExit(f"missing new node meta for {nid}")
            node = {
                "id": nid,
                "name": base["name"],
                "en": base.get("en", ""),
                "type": "mortise",
                "desc": base.get("desc", ""),
                "enDesc": base.get("enDesc", ""),
                "detail": base.get("detail", ""),
                "enDetail": base.get("enDetail", ""),
                "traits": list(base.get("traits") or []),
                "refs": [],
                "illus": illus_path,
            }
            nodes.append(node)
            by_id[nid] = node
            added += 1
        else:
            node = by_id[nid]
            node["illus"] = illus_path
            if info.get("traits"):
                node["traits"] = merge_traits(node.get("traits"), info["traits"])
            if info.get("traits_add"):
                node["traits"] = merge_traits(node.get("traits"), info["traits_add"])
            if info.get("detail_append"):
                d = node.get("detail") or node.get("desc") or ""
                ap = info["detail_append"]
                if ap not in d:
                    node["detail"] = (d + "\n" + ap).strip() if d else ap
            if info.get("detail") and not (node.get("detail") or "").strip():
                node["detail"] = info["detail"]
            updated += 1

    for s, t, rel, rel_en in NEW_LINKS:
        if s not in by_id or t not in by_id:
            continue
        if (s, t) in exist_pairs or (t, s) in exist_pairs:
            continue
        links.append({"source": s, "target": t, "relation": rel, "relationEn": rel_en})
        exist_pairs.add((s, t))

    DATA.write_text(
        m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"added={added} updated={updated} mortise={sum(1 for n in nodes if n.get('type')=='mortise')}")


if __name__ == "__main__":
    main()
