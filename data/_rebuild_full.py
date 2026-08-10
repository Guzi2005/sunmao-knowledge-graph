# -*- coding: utf-8 -*-
"""Rebuild knowledge graph from both Excel-derived JSONs + clean conceptual core."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"d:\xwechat_files\wxid_mrim2zak1zta12_50f6\msg\file\2026-08\知识图谱")
DATA = ROOT / "data" / "sunmao-graph.source.js"
KG = Path(r"D:\D盘桌面\榫卯\code\extracted\knowledge_graph.json")
ROWS = Path(r"D:\D盘桌面\榫卯\code\extracted\guobao_rows.json")
GUJI = Path(r"D:\D盘桌面\榫卯\code\extracted\guji_rows.json")

# load current to keep conceptual EN where good
old = json.loads(
    re.search(
        r"window\.GRAPH_DATA\s*=\s*(\{.*\})\s*;?\s*$",
        DATA.read_text(encoding="utf-8"),
        re.S,
    ).group(1)
)
old_by = {n["id"]: n for n in old["nodes"]}

kg = json.loads(KG.read_text(encoding="utf-8"))
sites = kg["nodes"]["site"]
books_meta = {b["name"]: b for b in kg["nodes"]["book"]}
guji_rows = json.loads(GUJI.read_text(encoding="utf-8"))
# group passages by book
passages_by_book = {}
for r in guji_rows:
    b = r.get("书名") or ""
    if not b:
        continue
    title = b if b.startswith("《") else f"《{b}》"
    passages_by_book.setdefault(title, []).append(r)

nodes = []
links = []
by_id = {}
by_name = {}


def add_node(n):
    if n["id"] in by_id:
        return by_id[n["id"]]
    # never allow slash-stitched names
    if "/" in n["name"] or "／" in n["name"]:
        raise ValueError(f"stitched name forbidden: {n['name']}")
    nodes.append(n)
    by_id[n["id"]] = n
    by_name[n["name"]] = n
    return n


def add_link(s, t, rel, rel_en):
    if s not in by_id or t not in by_id:
        return
    for l in links:
        if (l["source"] == s and l["target"] == t) or (l["source"] == t and l["target"] == s):
            return
    links.append({"source": s, "target": t, "relation": rel, "relationEn": rel_en})


def keep(oid, **overrides):
    base = dict(old_by[oid]) if oid in old_by else {}
    base.update(overrides)
    # strip slash names
    if "/" in base.get("name", "") or "／" in base.get("name", ""):
        raise ValueError(base.get("name"))
    return add_node(base)


# ─── Core conceptual nodes (no stitched names) ───
# Dynasties
for oid in ["hemudu", "chunqiu", "han", "tang", "song", "yuan", "ming", "qing", "modern"]:
    keep(oid)

# Add 金 / 辽 as proper dynasty nodes (data has many 金/辽 sites)
add_node(
    {
        "id": "jin",
        "name": "金代",
        "en": "Jin Dynasty",
        "type": "dynasty",
        "desc": "金代木构延续宋辽传统，晋冀寺院与文庙遗存丰富。",
        "enDesc": "Jin timber architecture continues Song–Liao traditions across North China temples.",
        "detail": "金代在北方广泛营建寺院、文庙与楼阁，榫卯与斗拱体系承接宋辽而趋于地方化，山西、河北遗存尤多。",
        "enDetail": "Jin builders sustained Song–Liao framing across temples and schools; Shanxi and Hebei preserve many examples with regionally adapted joinery.",
        "traits": ["承宋辽木构传统", "晋冀寺院文庙遗存丰富"],
        "refs": [],
    }
)
add_node(
    {
        "id": "liao",
        "name": "辽代",
        "en": "Liao Dynasty",
        "type": "dynasty",
        "desc": "辽代木塔与楼阁发达，应县木塔即其代表。",
        "enDesc": "Liao wooden pagodas and towers flourish; Yingxian Pagoda is emblematic.",
        "detail": "辽代高层木构成就突出，应县佛宫寺释迦塔以纯木榫卯叠层闻名，影响后世塔式木构。",
        "enDetail": "Liao multi-storey timberwork peaks in the Yingxian Wooden Pagoda—an all-wood stacked-joinery landmark.",
        "traits": ["高层木塔发达", "应县木塔为代表"],
        "refs": ["应县木塔"],
    }
)

# Mortise types from original (skip none)
for oid in [
    "yanwei",
    "xieding",
    "gejian",
    "jiatou",
    "baojian",
    "zongjiao",
    "changduan",
    "chajian",
    "bawang",
    "longfeng",
    "zouma",
    "tao",
    "chuandai",
    "qikou",
    "zhi",
    "ban",
    "tong",
    "dougong",
]:
    keep(oid)

# Extra types from Excel catalog
TYPE_EN = {
    "半榫": ("Blind Tenon", "Tenon stopped short of the far face."),
    "透榫": ("Through Tenon", "Tenon passing fully through the mortised member."),
    "馒头榫": ("Mantou Tenon", "Rounded bun-shaped tenon common in northern framing."),
    "箍头榫": ("Coped Rail Tenon", "Rail end coped onto a post."),
    "管脚榫": ("Foot Stub Tenon", "Short tenon seating a leg or post foot."),
    "交叉榫": ("Cross Halving Joint", "Members notch across each other."),
    "十字卡腰榫": ("Cross Waist Lock", "Cross joint with a locking waist catch."),
    "穿榫": ("Piercing Tenon", "Tenon threading an intermediate member."),
    "暗榫": ("Concealed Tenon", "Hidden tenon without exterior reveal."),
    "巴掌榫": ("Palm Scarf Joint", "Broad scarf-like joining face."),
    "半通榫": ("Half-Through Tenon", "Partially penetrating tenon."),
    "鼻子榫": ("Nose Tenon", "Projecting nose-shaped tenon."),
    "叉子榫": ("Fork Tenon", "Forked end engaging a mating member."),
    "穿带榫": ("Cleat Tenon", "Transverse cleat tenoned into a panel."),
    "雌雄榫": ("Male-Female Pair", "Complementary convex/concave pairing."),
    "大进小出榫": ("Stepped In-Out Tenon", "Stepped tenon with unequal shoulders."),
    "搭掌榫": ("Lapped Palm Joint", "Lapped joining faces."),
    "顶空榫": ("Open-Top Tenon", "Tenon seat left open at the top."),
    "鬭榫": ("Dou Tenon", "Interlocking dou-style join."),
    "对榫": ("Facing Tenon Pair", "Opposed matching tenons."),
    "二蹬榫": ("Two-Step Tenon", "Tenon with two stepped tiers."),
    "二合榫": ("Two-Part Combined Tenon", "Composite two-piece tenon."),
    "二肩蹬榫": ("Two-Shoulder Step Tenon", "Stepped tenon with twin shoulders."),
    "公母榫": ("Male-Female Tenon", "Gendered interlocking pair."),
    "荷包榫": ("Purse Tenon", "Purse-shaped locking tenon."),
    "鸡尾榫": ("Cock-Tail Tenon", "Splayed tail tenon."),
    "交口榫": ("Mouth-Meeting Joint", "Members meet at a mouthed interface."),
    "扣金式箍头榫": ("Metal-Coped Rail Tenon", "Coped rail reinforced in metal-style detailing."),
    "龙舌榫": ("Dragon-Tongue Tenon", "Tongue-like projecting tenon."),
    "龙凤榫": ("Dragon-Phoenix Joint", "Tongue-and-groove edge join."),
    "平接榫": ("Flush Butt Tenon", "Flush end-to-end join."),
    "骑马榫": ("Saddle Joint", "Saddle-shaped seating joint."),
    "全通榫": ("Full Through Tenon", "Fully through-going tenon."),
    "三合榫": ("Three-Part Combined Tenon", "Three-piece composite join."),
    "上下榫": ("Upper-Lower Tenon Pair", "Stacked upper and lower tenons."),
    "双肩直榫": ("Double-Shoulder Straight Tenon", "Straight tenon with twin shoulders."),
    "双榫": ("Twin Tenon", "Two parallel tenons."),
    "螳螂头榫": ("Mantis-Head Tenon", "Mantis-head profiled tenon."),
    "无肩直榫": ("Shoulderless Straight Tenon", "Straight tenon without shoulders."),
    "楔钉榫": ("Wedged Key Tenon", "Curved members locked by a wedge pin."),
    "袖肩燕尾榫": ("Sleeved-Shoulder Dovetail", "Dovetail with sleeved shoulders."),
    "燕尾箍头复合榫": ("Dovetail-Coped Composite", "Composite dovetail and coped rail."),
    "燕尾榫": ("Dovetail Joint", "Trapezoidal self-locking tenon."),
    "阳榫": ("Yang Tenon", "Protruding tenon (yang)."),
    "阴榫": ("Yin Mortise Side", "Receiving mortise side (yin)."),
    "阴阳榫": ("Yin-Yang Pair", "Complementary yang tenon and yin mortise."),
    "油桶榫": ("Oil-Drum Joint", "Cylindrical barrel-style join."),
    "元宝榫": ("Yuanbao Tenon", "Ingot-shaped locking tenon."),
    "鸳鸯榫": ("Mandarin-Duck Pair", "Paired interlocking tenons."),
    "直榫": ("Straight Tenon", "Rectangular prismatic tenon."),
    "中半通榫": ("Mid Half-Through Tenon", "Half-through tenon at mid depth."),
    "周肩直榫": ("Full-Shoulder Straight Tenon", "Straight tenon with continuous shoulders."),
    "柱脚榫": ("Column-Foot Tenon", "Tenon at the foot of a column."),
    "柱内键榫": ("Internal Column Key", "Key tenon inside a column assembly."),
    "斗拱": ("Dougong Bracket Set", "Layered interlocking bracket clusters."),
}

# map existing names to ids
EXISTING_TYPE_NAME = {n["name"]: n["id"] for n in nodes if n["type"] == "mortise"}
EXISTING_TYPE_NAME.update(
    {
        "半榫": "ban",
        "通榫": "tong",
        "直榫": "zhi",
        "燕尾榫": "yanwei",
        "龙凤榫": "longfeng",
        "企口榫": "qikou",
        "楔钉榫": "xieding",
        "穿带榫": "chuandai",
        "斗拱": "dougong",
        "格肩榫": "gejian",
        "夹头榫": "jiatou",
        "抱肩榫": "baojian",
        "粽角榫": "zongjiao",
        "插肩榫": "chajian",
        "霸王枨": "bawang",
        "透榫": "tousun",
        "馒头榫": "mantou",
        "箍头榫": "goutou",
        "管脚榫": "guanjiao",
        "交叉榫": "jiaocha",
        "十字卡腰榫": "shizi_kaya",
        "穿榫": "chuansun",
    }
)

type_id_map = dict(EXISTING_TYPE_NAME)
# ensure tousun etc exist from previous
for tname, (en, en_detail) in TYPE_EN.items():
    if tname in type_id_map and type_id_map[tname] in by_id:
        continue
    tid = type_id_map.get(tname) or re.sub(r"\W+", "_", tname)
    if tid in by_id:
        type_id_map[tname] = tid
        continue
    # skip if essentially duplicate of existing chinese name already added
    if tname in by_name:
        type_id_map[tname] = by_name[tname]["id"]
        continue
    add_node(
        {
            "id": tid,
            "name": tname,
            "en": en,
            "type": "mortise",
            "desc": f"{tname}，传统木构榫卯类型。",
            "enDesc": en_detail,
            "detail": f"{tname}是中国传统木结构中的接合做法。{en_detail}",
            "enDetail": en_detail,
            "traits": [f"榫卯类型：{tname}"],
            "refs": [],
        }
    )
    type_id_map[tname] = tid

# Regions / craft / culture (fix slash names)
keep("north")
keep("jiangnan")
keep("lingnan")
keep("xinan")
add_node(
    {
        "id": "qingzang",
        "name": "青藏地区",
        "en": "Qinghai–Tibet Region",
        "type": "region",
        "desc": "青藏高原及其周边的木构与庄园建筑传统。",
        "enDesc": "Timber and manor traditions of the Qinghai–Tibet highland and its fringes.",
        "detail": "青藏分区涵盖高原寺院、庄园与地方木作。朗色林庄园等遗存记录了半榫、穿带榫、龙凤榫等具体做法，宜按站点实证连边，不可按分区滥连。",
        "enDetail": "The highland belt includes monasteries and manors. Sites such as Langselin preserve attested joins (blind, cleat, dragon-phoenix, etc.)—link types only with site-level evidence.",
        "traits": ["高原庄园与寺院", "站点级类型实证"],
        "refs": [],
    }
)
for oid in ["moju", "bangang", "shouli", "jingdu", "tailiangchuandou"]:
    keep(oid)

# culture - fix slash names
keep("japan")
keep("iseshrine")
add_node(
    {
        "id": "korea",
        "name": "朝鲜半岛",
        "en": "Korean Peninsula",
        "type": "culture",
        "desc": "半岛宫殿与寺院木构与中国官式传统长期对话。",
        "enDesc": "Palace and temple timberwork in dialogue with Chinese official styles.",
        "detail": "朝鲜半岛宫廷与寺院建筑吸收中国斗拱与木构语汇，并发展出本地比例与彩画体系，如景福宫等遗存可见一脉。",
        "enDetail": "Korean court and temple carpentry absorbed Chinese bracket language while developing local proportions, as seen in complexes such as Gyeongbokgung.",
        "traits": ["与中国官式传统对话", "本地比例与彩画体系"],
        "refs": [],
    }
)
keep("oumei")
keep("banmao")
keep("kengoyama")
keep("yuerang")
add_node(
    {
        "id": "taikong",
        "name": "太空舱节点",
        "en": "Space Habitat Joints",
        "type": "culture",
        "desc": "可展开舱体节点借鉴榫卯互锁逻辑。",
        "enDesc": "Deployable cabin nodes inspired by interlocking timber logic.",
        "detail": "航天概念设计借用可折叠、互锁的节点几何，以紧凑发射与在轨展开为目标，与传统榫卯的干式咬合思维相通。",
        "enDetail": "Aerospace concepts borrow foldable interlocking nodes for compact launch and on-orbit expansion—echoing dry-join logic.",
        "traits": ["可展开互锁", "干式咬合思维"],
        "refs": [],
    }
)

# building types — SPLIT 塔/家具
keep("tailiang")
keep("chuandou")
keep("jinggan")
keep("gongdian")
keep("yuanlin")
add_node(
    {
        "id": "ta",
        "name": "塔",
        "en": "Pagoda",
        "type": "buildingType",
        "desc": "多层木塔依赖叠层梁柱与斗拱榫卯，应县木塔为其典范。",
        "enDesc": "Multi-storey wooden pagodas rely on stacked beams, columns and dougong joinery.",
        "detail": "塔式木构逐层积累梁枋、斗拱与楼梯榫卯。辽应县佛宫寺释迦塔以纯木叠层闻名，是高层榫卯的标志。",
        "enDetail": "Pagodas accumulate floors of beams, brackets and stair joinery. The Yingxian Wooden Pagoda remains the emblem of stacked all-wood tenon ambition.",
        "traits": ["多层叠梁柱", "斗拱与楼梯榫卯", "应县木塔为代表"],
        "refs": ["应县木塔"],
    }
)
add_node(
    {
        "id": "jiaju",
        "name": "家具",
        "en": "Furniture",
        "type": "buildingType",
        "desc": "明式家具以榫卯为灵魂，发展出燕尾、抱肩、夹头等精密接合。",
        "enDesc": "Ming furniture centers on joinery—dovetail, embracing-shoulder, clamp-head and more.",
        "detail": "家具榫卯把建筑接合下沉到器物尺度：燕尾、格肩、夹头、抱肩、粽角等构成明式家具的技术与美学核心，并可拆装、少用钉胶。",
        "enDetail": "Furniture joinery scales building logic to objects: dovetails, mitred shoulders, clamp-heads and zongjiao corners define Ming craft—knockdown-friendly and largely fastener-free.",
        "traits": ["明式家具榫卯体系", "可拆装、少钉胶", "燕尾榫", "抱肩榫", "夹头榫"],
        "refs": ["《明式家具研究》"],
    }
)

# literature core
for oid in ["yingzaofashi", "gongcheng", "tiangong", "kaogong", "mingshi", "chuci"]:
    keep(oid)
keep("feiyi2006")
keep("feiyi2009")

# original links except those involving old ta-only semantics — rebuild carefully from old
SKIP_REL_TARGETS = set()
for l in old["links"]:
    s, t = l["source"], l["target"]
    # skip links to removed stitched cultures if ids changed
    if s not in by_id or t not in by_id:
        continue
    add_link(s, t, l.get("relation", "相关"), l.get("relationEn", "related"))

# extra links for split nodes
add_link("tailiang", "ta", "构成", "constitutes")
add_link("chuandou", "ta", "构成", "constitutes")
add_link("jinggan", "ta", "构成", "constitutes")
add_link("ta", "dougong", "依赖", "depends on")
add_link("jiaju", "yanwei", "常用", "commonly uses")
add_link("jiaju", "jiatou", "常用", "commonly uses")
add_link("jiaju", "baojian", "常用", "commonly uses")
add_link("jiaju", "ming", "鼎盛于", "peaks in")
add_link("mingshi", "jiaju", "研究", "studies")
add_link("liao", "ta", "代表", "exemplified by")
add_link("liao", "song", "并行/影响", "parallel with")
add_link("jin", "song", "承袭", "inherits from")

# ─── ALL 国保 sites ───
DYN = {
    "明": "ming",
    "清": "qing",
    "元": "yuan",
    "宋": "song",
    "北宋": "song",
    "南宋": "song",
    "金": "jin",
    "辽": "liao",
    "唐": "tang",
    "汉": "han",
    "民国": "modern",
    "近现代": "modern",
    "先秦": "hemudu",
}
REG = {
    "北方地区": "north",
    "南方地区": "jiangnan",
    "西北地区": "xinan",
    "青藏地区": "qingzang",
}

SITE_TYPE_ALLOW = {"朗色林庄园"}  # only site-level evidenced type edges


def site_id(name, i):
    return f"site_{i:03d}"


SITE_EN_MAP = {
    "朗色林庄园": "Langselin Manor",
    "乔家大院": "Qiao Family Compound",
    "西递村古建筑群": "Xidi Ancient Buildings",
    "宏村古建筑群": "Hongcun Ancient Buildings",
    "平遥文庙": "Pingyao Confucian Temple",
    "潭柘寺": "Tanzhe Temple",
    "三原城隍庙": "Sanyuan City God Temple",
    "徐霞客故居及晴山堂石刻": "Xu Xiake Residence & Qingshan Hall",
}

for i, s in enumerate(sites, 1):
    name = s["name"]
    sid = site_id(name, i)
    # avoid colliding with conceptual names — keep the site under a disambiguated label
    if name in by_name:
        name = f"{name}（国保）"
        if name in by_name:
            name = f"{s['name']}（国保{i}）"
    en = SITE_EN_MAP.get(name, name)
    dyns = s.get("dynasties") or []
    era_txt = "、".join(dyns) if dyns else "见记述"
    loc = " / ".join([x for x in [s.get("province"), s.get("address")] if x])
    desc = f"{name}，全国重点文物保护单位。时代：{era_txt}。位置：{loc}。"
    if s.get("region"):
        desc += f"分区：{s['region']}。"
    if s.get("备注") or (s.get("desc") and "备注" in s.get("desc", "")):
        # prefer structured note from desc field already built
        pass
    detail = s.get("desc") or desc
    en_detail = (
        f"National Priority Protected Cultural Heritage Site. "
        f"Period: {era_txt}. Location: {loc}. "
        f"Region tag: {s.get('region') or 'n/a'}."
    )
    traits = []
    if loc:
        traits.append(f"位置：{loc}")
    if s.get("region"):
        traits.append(f"分区：{s['region']}")
    traits.append("国保单位")
    add_node(
        {
            "id": sid,
            "name": name,
            "en": en,
            "type": "heritage",
            "desc": desc,
            "enDesc": en_detail,
            "detail": detail,
            "enDetail": en_detail,
            "traits": traits,
            "refs": ["全国重点文物保护单位名录"],
        }
    )
    for d in dyns:
        did = DYN.get(d)
        if did:
            add_link(sid, did, "年代", "dated to")
    rid = REG.get(s.get("region") or "")
    if rid:
        add_link(sid, rid, "地域", "in region")
    # type edges only if allowlisted
    if name in SITE_TYPE_ALLOW:
        # parse types from detail text after 已记录榫卯类型：
        m = re.search(r"已记录榫卯类型：([^。]+)", detail)
        raw_types = []
        if m:
            raw_types = [x.strip() for x in m.group(1).replace("、", ",").split(",") if x.strip()]
        else:
            # from kg typed sites
            for ts in kg["meta"]["type_edge_policy"].get("allow_sites", []):
                pass
            raw_types = ["半榫", "穿带榫", "龙凤榫", "馒头榫", "透榫"]
        for tn in raw_types:
            tid = type_id_map.get(tn)
            if tid:
                add_link(sid, tid, "采用", "uses")

# ─── ALL books from guji ───
BOOK_EN = {
    "《热河工程则例》": "Rehe Engineering Regulations",
    "《营造法式》": "Yingzao Fashi",
    "《园冶》": "Yuan Ye (The Craft of Gardens)",
    "《内庭工程做法》": "Inner Court Engineering Methods",
    "《内廷做法》": "Inner Court Methods",
    "《工程做法》": "Engineering Methods",
    "《扬州画舫录》": "Record of the Painted Barges of Yangzhou",
    "《天工开物》": "Tiangong Kaiwu",
    "《考工记》": "Kaogongji",
    "《明式家具研究》": "Studies in Ming Furniture",
}


def book_id(title, i):
    return f"book_{i:03d}"


bi = 0
for title, rows in passages_by_book.items():
    bi += 1
    # skip if already have core lit with same bare name
    bare = title.strip("《》")
    skip = False
    for existing in ["yingzaofashi", "gongcheng", "tiangong", "kaogong", "mingshi", "chuci"]:
        if existing in by_id and bare in by_id[existing]["name"]:
            # merge passages into existing detail
            excerpts = []
            for r in rows[:5]:
                if r.get("原文片段"):
                    excerpts.append(r["原文片段"])
            if excerpts:
                by_id[existing]["detail"] = (
                    by_id[existing].get("detail") or ""
                ) + " 相关摘句：" + " / ".join(excerpts[:3])
            # still link dynasties from rows
            for r in rows:
                d = DYN.get((r.get("朝代") or "").strip())
                if d:
                    add_link(existing, d, "文献年代", "textual period")
            skip = True
            break
    if skip:
        continue
    if title in by_name:
        continue
    bid = book_id(title, bi)
    author = rows[0].get("作者") or ""
    dynasty_raw = rows[0].get("朝代") or ""
    excerpts = [r.get("原文片段") for r in rows if r.get("原文片段")]
    translations = [r.get("翻译") for r in rows if r.get("翻译")]
    desc = f"{title}" + (f"，作者：{author}。" if author else "。") + (f"时代：{dynasty_raw}。" if dynasty_raw else "")
    detail = desc
    if excerpts:
        detail += " 原文摘句：" + "；".join(excerpts[:4])
    en_name = BOOK_EN.get(title, title.strip("《》"))
    en_detail = (
        f"Historical text {en_name}."
        + (f" Author: {author}." if author else "")
        + (f" Period label: {dynasty_raw}." if dynasty_raw else "")
    )
    if translations:
        en_detail += " Sample: " + translations[0][:180]
    add_node(
        {
            "id": bid,
            "name": title,
            "en": en_name,
            "type": "literature",
            "desc": desc,
            "enDesc": en_detail,
            "detail": detail,
            "enDetail": en_detail,
            "traits": [
                x
                for x in [
                    f"作者：{author}" if author else "",
                    "榫卯文献记述",
                ]
                if x
            ],
            "refs": [title],
        }
    )
    d = DYN.get(dynasty_raw.strip())
    if d:
        add_link(bid, d, "成书/传抄年代", "compiled in")
    # careful term links from excerpts only when explicit type names appear
    blob = " ".join(excerpts[:6])
    for tn, tid in type_id_map.items():
        if len(tn) >= 2 and tn in blob and tid in by_id:
            add_link(bid, tid, "记述", "describes")

out = {
    "nodes": nodes,
    "links": links,
}

header = """/*
 * 中国古代榫卯结构知识图谱 · 数据源码
 * 来源：既有概念图谱 +《国保+朝代+位置+榫卯类型》全量 +《榫卯（明-清）古籍相关描述》全量书目
 * 规则：节点名纯净（禁止用 / 缝合）；年代写入说明并连朝代；国保→类型仅站点级实证；古籍默认不与国保滥连
 * nodeType：mortise / dynasty / region / craft / culture / buildingType / literature / heritage
 */
window.GRAPH_DATA = """

DATA.write_text(header + json.dumps(out, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")

from collections import Counter

c = Counter(n["type"] for n in nodes)
print("nodes", len(nodes), "links", len(links))
print(dict(c))
print("has ta/jiaju", by_id["ta"]["name"], by_id["jiaju"]["name"])
print("slash names", [n["name"] for n in nodes if "/" in n["name"] or "／" in n["name"]])
