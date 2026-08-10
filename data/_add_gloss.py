# -*- coding: utf-8 -*-
"""For pinyin-only English names, append a parenthetical free translation when derivable."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pypinyin import Style, lazy_pinyin

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"


def py_title(name: str) -> str:
    parts = lazy_pinyin(name, style=Style.NORMAL)
    return " ".join(p.capitalize() for p in parts if p)


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


# 书名关键词 → 意译片段（按最长匹配优先）
BOOK_KEYWORDS = [
    ("工程做法", "Engineering Methods"),
    ("工程则例", "Engineering Regulations"),
    ("营造法式", "Building Standards"),
    ("做法", "Construction Methods"),
    ("则例", "Regulations"),
    ("成规", "Established Rules"),
    ("章程", "Statutes"),
    ("清册", "Inventory"),
    ("奏销", "Expenditure Records"),
    ("遗集", "Posthumous Anthology"),
    ("全集", "Complete Works"),
    ("文集", "Collected Writings"),
    ("笔记", "Notebooks"),
    ("随笔", "Essays"),
    ("杂记", "Miscellaneous Notes"),
    ("见闻", "Observations"),
    ("日记", "Diary"),
    ("游记", "Travel Notes"),
    ("画舫录", "Record of Painted Barges"),
    ("大典", "Encyclopedia"),
    ("总录", "Comprehensive Records"),
    ("实录", "Veritable Records"),
    ("通志", "Comprehensive Gazetteer"),
    ("县志", "County Gazetteer"),
    ("府志", "Prefecture Gazetteer"),
    ("志", "Gazetteer"),
    ("图说", "Illustrated Explanations"),
    ("图考", "Illustrated Study"),
    ("图", "Illustrations"),
    ("考工记", "Records of Artificers"),
    ("考", "Study"),
    ("记", "Records"),
    ("录", "Records"),
    ("谱", "Manual"),
    ("略", "Outline"),
    ("论", "Discourse"),
    ("说", "Discourse"),
    ("解", "Exposition"),
    ("注", "Commentary"),
    ("笺", "Annotations"),
    ("集", "Anthology"),
    ("书", "Book"),
    ("经", "Classic"),
    ("典", "Canon"),
    ("鉴", "Mirror"),
    ("法", "Methods"),
    ("学", "Studies"),
    ("萃编", "Selected Compilation"),
    ("续稿", "Continued Drafts"),
    ("旧编", "Old Compilation"),
    ("文纂", "Literary Compilation"),
    ("编", "Compilation"),
    ("拾遗", "Supplement"),
    ("纪要", "Summary"),
    ("讲题", "Sermon Topics"),
    ("通义", "General Exposition"),
    ("奏档", "Memorial Archives"),
    ("奏疏", "Memorials"),
    ("墨苑", "Ink Collection"),
    ("绀珠", "Encyclopedia"),
    ("四种", "Four Works"),
    ("剩技", "Miscellaneous Arts"),
    ("稽言", "Verified Sayings"),
    ("词", "Verses"),
    ("稿", "Drafts"),
    ("纂", "Compilation"),
    ("苑", "Collection"),
]

# 主题词 → 意译前缀
BOOK_TOPICS = [
    ("营造", "Construction"),
    ("木经", "Timberwork"),
    ("木工", "Carpentry"),
    ("工部", "Board of Works"),
    ("内廷", "Inner Court"),
    ("内庭", "Inner Court"),
    ("宫殿", "Palace"),
    ("园", "Garden"),
    ("桥", "Bridge"),
    ("河工", "River Works"),
    ("水利", "Waterworks"),
    ("战船", "Warship"),
    ("船", "Ship"),
    ("军器", "Armaments"),
    ("兵", "Military"),
    ("武备", "Military Preparedness"),
    ("农", "Agriculture"),
    ("天文", "Astronomy"),
    ("算", "Mathematics"),
    ("字", "Characters"),
    ("家具", "Furniture"),
]


def gloss_book(bare: str) -> str | None:
    kw_en = None
    kw_len = 0
    for k, v in BOOK_KEYWORDS:
        if k in bare and len(k) > kw_len:
            kw_en, kw_len = v, len(k)
    topic_en = None
    for k, v in BOOK_TOPICS:
        if k in bare:
            topic_en = v
            break
    if kw_en and topic_en and topic_en.lower() not in kw_en.lower():
        return f"{topic_en} {kw_en}"
    return kw_en or (f"On {topic_en}" if topic_en else None)


# 古建名关键词（纯拼音兜底时的意译）
SITE_KEYWORDS = [
    ("古建筑群", "Ancient Building Complex"),
    ("建筑群", "Building Complex"),
    ("大殿", "Great Hall"),
    ("正殿", "Main Hall"),
    ("戏楼", "Opera Tower"),
    ("戏台", "Opera Stage"),
    ("牌坊", "Memorial Archway"),
    ("牌楼", "Memorial Gateway"),
    ("民居", "Vernacular Houses"),
    ("大院", "Grand Courtyard"),
    ("会馆", "Guild Hall"),
    ("书院", "Academy"),
    ("文庙", "Confucian Temple"),
    ("城隍庙", "City God Temple"),
    ("关帝庙", "Guandi Temple"),
    ("清真寺", "Mosque"),
    ("教堂", "Church"),
    ("庄园", "Manor"),
    ("故居", "Former Residence"),
    ("祠堂", "Ancestral Hall"),
    ("祠", "Ancestral Shrine"),
    ("塔", "Pagoda"),
    ("寺", "Temple"),
    ("庙", "Temple"),
    ("观", "Taoist Temple"),
    ("宫", "Palace"),
    ("园", "Garden"),
    ("楼", "Tower"),
    ("阁", "Pavilion"),
    ("殿", "Hall"),
    ("桥", "Bridge"),
    ("井", "Well"),
    ("窑", "Kiln"),
    ("陵", "Mausoleum"),
    ("墓", "Tomb"),
    ("县衙", "County Yamen"),
    ("衙门", "Yamen Offices"),
    ("衙署", "Yamen Offices"),
    ("义仓", "Charity Granary"),
    ("仓", "Granary"),
    ("义庄", "Charitable Estate"),
    ("民宅", "Residence"),
    ("大屋", "Grand House"),
    ("花屋", "Ornate House"),
    ("老宅", "Old Residence"),
    ("三宅", "Three Residences"),
    ("宅", "Residence"),
    ("围屋", "Hakka Walled House"),
    ("围", "Walled Compound"),
    ("土堡群", "Earthen Fort Cluster"),
    ("土堡", "Earthen Fort"),
    ("堡", "Fortress"),
    ("屯", "Fortress"),
    ("寨", "Stockaded Village"),
    ("古厝", "Ancient Houses"),
    ("厅", "Hall"),
    ("考棚", "Examination Hall"),
    ("讲学处", "Lecture Site"),
    ("城墙", "City Wall"),
    ("影壁", "Screen Wall"),
    ("石坊", "Stone Archway"),
    ("山庄", "Mountain Villa"),
    ("莲花池", "Lotus Pond"),
    ("池", "Pond"),
    ("召", "Monastery"),
    ("拉康", "Buddhist Chapel"),
    ("光禄第", "Guanglu Mansion"),
    ("第", "Mansion"),
]


def gloss_site(name: str) -> str | None:
    for k, v in SITE_KEYWORDS:
        if k in name:
            return v
    return None


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))

    added = 0
    for n in data["nodes"]:
        en = n.get("en") or ""
        if not en or "(" in en:
            continue
        name = re.sub(r"（国保(?:\d+)?）", "", n["name"]).strip()
        bare = name.strip("《》")
        pin = py_title(bare)
        # 仅处理「纯拼音」英文名：en 与整名拼音一致
        if en.strip().lower() != pin.strip().lower():
            continue
        if n["type"] == "literature":
            g = gloss_book(bare)
        elif n["type"] == "heritage":
            g = gloss_site(bare)
        else:
            g = gloss_site(bare) or gloss_book(bare)
        if g:
            n["en"] = f"{en} ({g})"
            added += 1

    print("glossed", added)
    # 剩余纯拼音统计
    left = 0
    for n in data["nodes"]:
        en = n.get("en") or ""
        name = re.sub(r"（国保(?:\d+)?）", "", n["name"]).strip().strip("《》")
        if en and "(" not in en and en.strip().lower() == py_title(name).strip().lower():
            left += 1
    print("remaining pure pinyin", left)

    DATA.write_text(text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
