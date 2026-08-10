# -*- coding: utf-8 -*-
"""Rebuild heritage en / enDesc / enDetail without lazy pinyin syllable-splitting."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

PROV = {
    "北京": "Beijing", "天津": "Tianjin", "上海": "Shanghai", "重庆": "Chongqing",
    "河北": "Hebei", "山西": "Shanxi", "辽宁": "Liaoning", "吉林": "Jilin",
    "黑龙江": "Heilongjiang", "江苏": "Jiangsu", "浙江": "Zhejiang", "安徽": "Anhui",
    "福建": "Fujian", "江西": "Jiangxi", "山东": "Shandong", "河南": "Henan",
    "湖北": "Hubei", "湖南": "Hunan", "广东": "Guangdong", "海南": "Hainan",
    "四川": "Sichuan", "贵州": "Guizhou", "云南": "Yunnan", "陕西": "Shaanxi",
    "甘肃": "Gansu", "青海": "Qinghai", "台湾": "Taiwan", "内蒙古": "Inner Mongolia",
    "广西": "Guangxi", "西藏": "Tibet", "宁夏": "Ningxia", "新疆": "Xinjiang",
    "香港": "Hong Kong", "澳门": "Macao",
}

REG = {
    "北方地区": "Northern China",
    "南方地区": "Southern China",
    "西北地区": "Northwest China",
    "青藏地区": "Qinghai–Tibet region",
}

ETHNIC = {
    "傈僳族": "Lisu", "彝族": "Yi", "白族": "Bai", "纳西族": "Naxi", "藏族": "Tibetan",
    "回族": "Hui", "蒙古族": "Mongol", "维吾尔族": "Uyghur", "苗族": "Miao", "侗族": "Dong",
    "壮族": "Zhuang", "土家族": "Tujia", "哈尼族": "Hani", "傣族": "Dai", "畲族": "She",
    "瑶族": "Yao", "满族": "Manchu", "朝鲜族": "Korean",
}

PLACE = {
    "维西": "Weixi", "叶枝": "Yeji", "同乐": "Tongle", "三原": "Sanyuan", "户县": "Huxian",
    "白水": "Baishui", "弥渡": "Midu", "石屏": "Shiping", "建水": "Jianshui", "保山": "Baoshan",
    "隆阳": "Longyang", "江川": "Jiangchuan", "西安": "Xi'an", "墨江": "Mojiang", "芷江": "Zhijiang",
    "江华": "Jianghua", "三江": "Sanjiang", "恭城": "Gongcheng", "石柱": "Shizhu", "景宁": "Jingning",
    "天祝": "Tianzhu", "门头沟": "Mentougou", "东城": "Dongcheng", "西城": "Xicheng",
    "朝阳": "Chaoyang", "海淀": "Haidian", "宣武": "Xuanwu", "正定": "Zhengding", "安国": "Anguo",
    "怀安": "Huai'an", "怀来": "Huailai", "定州": "Dingzhou", "承德": "Chengde", "昌黎": "Changli",
    "泊头": "Botou", "魏县": "Wei County", "顺平": "Shunping", "保定": "Baoding", "涞水": "Laishui",
    "邢台": "Xingtai", "涉县": "She County", "平遥": "Pingyao",
}

NAME_EN = {
    "同乐傈僳族民居建筑群": "Tongle Lisu Vernacular Architecture Complex",
    "叶枝土司衙署": "Yeji Tusi Yamen (Native Chieftain Office)",
    "三原城隍庙": "Sanyuan City God Temple",
    "西安城隍庙": "Xi'an City God Temple",
    "保山光尊寺": "Baoshan Guangzun Temple",
    "洄澜桥阁": "Huilan Bridge Pavilion",
    "江川文庙": "Jiangchuan Confucian Temple",
    "公输堂": "Gongshu Hall",
    "仓颉墓与庙": "Cangjie Tomb and Temple",
    "密渡五台大寺": "Midu Wutai Grand Temple",
}

SUFFIX = [
    ("民居建筑群", " Vernacular Architecture Complex"),
    ("古建筑群", " Ancient Building Complex"),
    ("土司衙署", " Tusi Yamen (Native Chieftain Office)"),
    ("民居", " Vernacular Dwellings"),
    ("会馆", " Guild Hall"), ("文庙", " Confucian Temple"), ("城隍庙", " City God Temple"),
    ("王府", " Princely Mansion"), ("故居", " Former Residence"), ("庄园", " Manor"),
    ("石刻", " Stone Inscriptions"), ("木塔", " Wooden Pagoda"), ("佛塔", " Buddhist Pagoda"),
    ("寺庙", " Temple"), ("寺院", " Monastery"), ("大殿", " Grand Hall"), ("塔", " Pagoda"),
    ("寺", " Temple"), ("庙", " Temple"), ("观", " Taoist Temple"), ("宫", " Palace"),
    ("园", " Garden"), ("府", " Mansion"), ("坛", " Altar"), ("楼", " Tower"), ("阁", " Pavilion"),
    ("桥", " Bridge"), ("村", " Village"), ("城", " City"), ("院", " Courtyard"), ("堂", " Hall"),
    ("祠", " Ancestral Shrine"), ("庵", " Nunnery"), ("陵", " Mausoleum"), ("墓", " Tomb"),
    ("窟", " Grotto"),
]


def romanize(seg: str) -> str:
    if seg in PLACE:
        return PLACE[seg]
    if seg in PROV:
        return PROV[seg]
    return seg


def translate_admin(seg: str) -> str:
    seg = seg.strip()
    if not seg:
        return seg
    m = re.match(r"^(.+?)市(.+?)区$", seg)
    if m:
        return f"{romanize(m.group(1))} City {romanize(m.group(2))} District"
    for eth, eth_en in sorted(ETHNIC.items(), key=lambda x: -len(x[0])):
        for kind, kind_en in (("县", "Autonomous County"), ("州", "Autonomous Prefecture"), ("区", "Autonomous Region")):
            token = eth + "自治" + kind
            if seg.endswith(token):
                geo = seg[: -len(token)]
                return f"{romanize(geo)} {eth_en} {kind_en}"
    if seg.endswith("区"):
        return f"{romanize(seg[:-1])} District"
    if seg.endswith("县"):
        return f"{romanize(seg[:-1])} County"
    if seg.endswith("市"):
        return f"{romanize(seg[:-1])} City"
    if seg.endswith("州"):
        return f"{romanize(seg[:-1])} Prefecture"
    for k, v in sorted(PROV.items(), key=lambda x: -len(x[0])):
        if seg.startswith(k):
            rest = seg[len(k):]
            return v + ((" / " + translate_admin(rest)) if rest else "")
    return romanize(seg)


def translate_place(loc: str) -> str:
    if not loc:
        return "n/a"
    return " / ".join(translate_admin(c.strip()) for c in re.split(r"\s*/\s*", loc) if c.strip())


def translate_name(name: str) -> str:
    name = re.sub(r"（国保(?:\d+)?）", "", name).strip()
    if name in NAME_EN:
        return NAME_EN[name]
    working = name
    for eth, en in sorted(ETHNIC.items(), key=lambda x: -len(x[0])):
        working = working.replace(eth, f" {en} ")
    working = re.sub(r"\s{2,}", " ", working).strip()
    for suf, en_suf in SUFFIX:
        if name.endswith(suf) and len(name) > len(suf):
            stem = name[: -len(suf)]
            for eth, en in sorted(ETHNIC.items(), key=lambda x: -len(x[0])):
                stem = stem.replace(eth, f" {en} ")
            stem = stem.strip()
            parts = []
            i = 0
            while i < len(stem):
                if "\u4e00" <= stem[i] <= "\u9fff":
                    j = i + 1
                    while j < len(stem) and "\u4e00" <= stem[j] <= "\u9fff":
                        j += 1
                    chunk = stem[i:j]
                    parts.append(PLACE.get(chunk, chunk))
                    i = j
                elif stem[i].isspace():
                    i += 1
                else:
                    j = i + 1
                    while j < len(stem) and stem[j].isalpha():
                        j += 1
                    parts.append(stem[i:j])
                    i = j
            return " ".join(parts) + en_suf
    return working


def heritage_fields(n: dict) -> tuple[str, str, str]:
    name = n["name"]
    en = translate_name(name)
    desc = n.get("desc") or n.get("detail") or ""
    m_loc = re.search(r"位置：([^。]+)", desc)
    m_reg = re.search(r"分区：([^。]+)", desc)
    loc = translate_place(m_loc.group(1).strip() if m_loc else "")
    reg = REG.get((m_reg.group(1) if m_reg else "").strip(), "n/a")
    detail = (
        f"National Priority Protected Cultural Heritage Site. "
        f"Location: {loc}. Region: {reg}."
    )
    return en, detail, detail


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    if not m:
        raise SystemExit("parse fail")
    data = json.loads(m.group(2))
    n_fix = 0
    for n in data["nodes"]:
        if n.get("type") != "heritage":
            continue
        en, ed, edt = heritage_fields(n)
        if (n.get("en"), n.get("enDesc"), n.get("enDetail")) != (en, ed, edt):
            n["en"], n["enDesc"], n["enDetail"] = en, ed, edt
            n_fix += 1
    header = text[: m.start()]
    DATA.write_text(header + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    print("heritage nodes updated:", n_fix)


if __name__ == "__main__":
    main()
