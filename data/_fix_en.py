# -*- coding: utf-8 -*-
"""Fix English titles/descriptions: no Chinese leakage; heritage/book titles translated or romanized."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pypinyin import Style, lazy_pinyin

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

DYN = {
    "先秦": "Pre-Qin",
    "汉": "Han",
    "唐": "Tang",
    "宋": "Song",
    "北宋": "Northern Song",
    "南宋": "Southern Song",
    "辽": "Liao",
    "金": "Jin",
    "元": "Yuan",
    "明": "Ming",
    "清": "Qing",
    "民国": "Republican era",
    "近现代": "Modern",
    "现代": "Contemporary",
    "春秋": "Spring and Autumn",
    "战国": "Warring States",
}

REG = {
    "北方地区": "Northern China",
    "南方地区": "Southern China",
    "西北地区": "Northwest China",
    "青藏地区": "Qinghai–Tibet region",
}

PROV = {
    "北京": "Beijing",
    "天津": "Tianjin",
    "上海": "Shanghai",
    "重庆": "Chongqing",
    "河北": "Hebei",
    "山西": "Shanxi",
    "辽宁": "Liaoning",
    "吉林": "Jilin",
    "黑龙江": "Heilongjiang",
    "江苏": "Jiangsu",
    "浙江": "Zhejiang",
    "安徽": "Anhui",
    "福建": "Fujian",
    "江西": "Jiangxi",
    "山东": "Shandong",
    "河南": "Henan",
    "湖北": "Hubei",
    "湖南": "Hunan",
    "广东": "Guangdong",
    "海南": "Hainan",
    "四川": "Sichuan",
    "贵州": "Guizhou",
    "云南": "Yunnan",
    "陕西": "Shaanxi",
    "甘肃": "Gansu",
    "青海": "Qinghai",
    "台湾": "Taiwan",
    "内蒙古": "Inner Mongolia",
    "广西": "Guangxi",
    "西藏": "Tibet",
    "宁夏": "Ningxia",
    "新疆": "Xinjiang",
    "香港": "Hong Kong",
    "澳门": "Macao",
}

# 民族 / 行政建制（地名译名优先于逐字拼音）
ETHNIC = {
    "傈僳族": "Lisu",
    "彝族": "Yi",
    "白族": "Bai",
    "纳西族": "Naxi",
    "藏族": "Tibetan",
    "回族": "Hui",
    "蒙古族": "Mongol",
    "维吾尔族": "Uyghur",
    "苗族": "Miao",
    "侗族": "Dong",
    "壮族": "Zhuang",
    "土家族": "Tujia",
    "哈尼族": "Hani",
    "傣族": "Dai",
    "满族": "Manchu",
    "朝鲜族": "Korean",
}

PLACE_ROMAN = {
    "维西": "Weixi",
    "叶枝": "Yeji",
    "同乐": "Tongle",
    "三原": "Sanyuan",
    "户县": "Huxian",
    "白水": "Baishui",
    "弥渡": "Midu",
    "石屏": "Shiping",
    "建水": "Jianshui",
    "保山": "Baoshan",
    "隆阳": "Longyang",
    "江川": "Jiangchuan",
    "忠": "Zhong",
    "忠县": "Zhongxian",
    "蔚": "Yu",
    "涉": "She",
    "南开": "Nankai",
    "桥东": "Qiaodong",
    "锦州": "Jinzhou",
    "万荣": "Wanrong",
    "五台": "Wutai",
    "介休": "Jiexiu",
    "长治": "Changzhi",
    "陵川": "Lingchuan",
    "浑源": "Hunyuan",
    "太原": "Taiyuan",
    "代": "Dai",
    "平顺": "Pingshun",
    "石楼": "Shilou",
    "门头沟": "Mentougou",
    "宣武": "Xuanwu",
    "呼和浩特": "Hohhot",
    "包头": "Baotou",
    "昆都仑": "Kundulun",
    "丹江口": "Danjiangkou",
    "自贡": "Zigong",
    "自流井": "Ziliujing",
    "景宁": "Jingning",
    "江华": "Jianghua",
    "恭城": "Gongcheng",
}

# Known proper English names (override pinyin)
NAME_EN = {
    "潭柘寺": "Tanzhe Temple",
    "可园": "Keyuan Garden",
    "孚王府": "Prince Fu Mansion",
    "景山": "Jingshan Park",
    "白云观": "White Cloud Temple",
    "法源寺": "Fayuan Temple",
    "先农坛": "Altar of Agriculture",
    "碧云寺": "Biyun Temple",
    "大慧寺": "Dahui Temple",
    "十方普觉寺": "Shifang Pujue Temple",
    "长椿寺": "Changchun Temple",
    "智珠寺": "Zhizhu Temple",
    "北京湖广会馆": "Beijing Huguang Guild Hall",
    "天津广东会馆": "Tianjin Guangdong Guild Hall",
    "乔家大院": "Qiao Family Compound",
    "西递村古建筑群": "Xidi Ancient Building Complex",
    "宏村古建筑群": "Hongcun Ancient Building Complex",
    "平遥文庙": "Pingyao Confucian Temple",
    "朗色林庄园": "Langselin Manor",
    "三原城隍庙": "Sanyuan City God Temple",
    "徐霞客故居及晴山堂石刻": "Xu Xiake Residence & Qingshan Hall Stele",
    "拙政园": "Humble Administrator's Garden",
    "留园": "Lingering Garden",
    "避暑山庄": "Chengde Mountain Resort",
    "故宫": "Forbidden City",
    "太和殿": "Hall of Supreme Harmony",
    "天坛": "Temple of Heaven",
    "应县木塔": "Yingxian Wooden Pagoda",
    "佛光寺": "Foguang Temple",
    "独乐寺": "Dule Temple",
    "同乐傈僳族民居建筑群": "Tongle Lisu Vernacular Architecture Complex",
    "叶枝土司衙署": "Yeji Tusi Yamen (Native Chieftain Office)",
    "石宝寨": "Shibaozhai",
    "古莲花池": "Ancient Lotus Pond",
    "释迦寺": "Shijia Temple (Sakyamuni Temple)",
    "国家级非遗(2006)": "National Intangible Cultural Heritage (2006)",
    "联合国非遗(2009)": "UNESCO Intangible Cultural Heritage (2009)",
}

BOOK_EN = {
    "遵生八笺": "Eight Treatises on Following the Principles of Life",
    "说略": "Brief Discourses",
    "江南陆师学堂武备课程": "Jiangnan Military Academy Drill Curriculum",
    "汉字举例": "Examples of Chinese Characters",
    "神器谱": "Register of Divine Implements",
    "永乐大典": "Yongle Encyclopedia",
    "丹铅总录": "Comprehensive Records of Cinnabar and Lead",
    "直隶五道成规": "Established Rules of the Five Circuits of Zhili",
    "频罗庵遗集": "Collected Works of Pinluo Hermitage",
    "算学": "Mathematics",
    "热河工程则例": "Rehe Engineering Regulations",
    "营造法式": "Yingzao Fashi",
    "园冶": "Yuan Ye (The Craft of Gardens)",
    "内庭工程做法": "Inner Court Engineering Methods",
    "内廷做法": "Inner Court Methods",
    "工程做法": "Engineering Methods",
    "扬州画舫录": "Record of the Painted Barges of Yangzhou",
    "天工开物": "Tiangong Kaiwu",
    "考工记": "Kaogongji",
    "明式家具研究": "Studies in Ming Furniture",
    "楚辞": "Songs of Chu",
}

SUFFIX = [
    ("民居建筑群", " Vernacular Architecture Complex"),
    ("古建筑群", " Ancient Building Complex"),
    ("土司衙署", " Tusi Yamen (Native Chieftain Office)"),
    ("民居", " Vernacular Dwellings"),
    ("会馆", " Guild Hall"),
    ("文庙", " Confucian Temple"),
    ("城隍庙", " City God Temple"),
    ("王府", " Princely Mansion"),
    ("故居", " Former Residence"),
    ("庄园", " Manor"),
    ("石刻", " Stone Inscriptions"),
    ("木塔", " Wooden Pagoda"),
    ("佛塔", " Buddhist Pagoda"),
    ("寺庙", " Temple"),
    ("寺院", " Monastery"),
    ("大殿", " Hall"),
    ("塔", " Pagoda"),
    ("寺", " Temple"),
    ("庙", " Temple"),
    ("观", " Taoist Temple"),
    ("宫", " Palace"),
    ("园", " Garden"),
    ("府", " Mansion"),
    ("坛", " Altar"),
    ("楼", " Tower"),
    ("阁", " Pavilion"),
    ("桥", " Bridge"),
    ("村", " Village"),
    ("城", " City"),
    ("院", " Courtyard"),
    ("堂", " Hall"),
    ("祠", " Ancestral Shrine"),
    ("庵", " Nunnery"),
    ("陵", " Mausoleum"),
    ("墓", " Tomb"),
    ("窟", " Grotto"),
]


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def py_title(name: str) -> str:
    parts = lazy_pinyin(name, style=Style.NORMAL)
    return " ".join(p.capitalize() for p in parts if p)


def romanize_place(name: str) -> str:
    """行政区划：连写拼音，首字母大写（Mentougou / Zhongxian）。"""
    if not name or not has_cjk(name):
        return name or ""
    if name in PLACE_ROMAN:
        return PLACE_ROMAN[name]
    parts = lazy_pinyin(name, style=Style.NORMAL)
    s = "".join(parts)
    return (s[:1].upper() + s[1:].lower()) if s else s


def romanize_stem(name: str) -> str:
    """建筑专名词干：分写拼音（Fayuan / Xiao Hui Ling）。"""
    if not name or not has_cjk(name):
        return name or ""
    if name in PLACE_ROMAN:
        return PLACE_ROMAN[name]
    if name in NAME_EN:
        return NAME_EN[name]
    parts = lazy_pinyin(name, style=Style.NORMAL)
    return " ".join(p.capitalize() for p in parts if p)


def apply_ethnic_tokens(text: str) -> str:
    out = text
    for eth, en in sorted(ETHNIC.items(), key=lambda x: -len(x[0])):
        out = out.replace(eth, f"__{en}__")
    return out


def restore_ethnic_tokens(text: str) -> str:
    out = text
    for eth, en in ETHNIC.items():
        out = out.replace(f"__{en}__", f" {en} ")
    out = re.sub(r"\s{2,}", " ", out).strip()
    if not has_cjk(out):
        return out
    parts = re.findall(r"[\u4e00-\u9fff]+|[^\u4e00-\u9fff\s]+", out)
    eng = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if has_cjk(p):
            eng.append(romanize_stem(p) if len(p) > 2 else romanize_place(p))
        else:
            eng.append(p)
    return " ".join(eng)


def translate_admin_segment(seg: str) -> str:
    seg = seg.strip()
    if not seg:
        return seg
    if seg in PLACE_ROMAN:
        return PLACE_ROMAN[seg]
    if seg in PROV:
        return PROV[seg]
    m = re.match(r"^(.+?)市(.+?)区$", seg)
    if m:
        return f"{romanize_place(m.group(1))} City {romanize_place(m.group(2))} District"
    for eth, eth_en in sorted(ETHNIC.items(), key=lambda x: -len(x[0])):
        for kind, kind_en in (("县", "Autonomous County"), ("州", "Autonomous Prefecture"), ("区", "Autonomous Region")):
            token = eth + "自治" + kind
            if seg.endswith(token):
                geo = seg[: -len(token)]
                return f"{romanize_place(geo)} {eth_en} {kind_en}"
    if seg.endswith("自治县"):
        return f"{romanize_place(seg[:-4])} Autonomous County"
    if seg.endswith("自治州"):
        return f"{romanize_place(seg[:-4])} Autonomous Prefecture"
    if seg.endswith("自治区"):
        return f"{romanize_place(seg[:-4])} Autonomous Region"
    if seg.endswith("区"):
        return f"{romanize_place(seg[:-1])} District"
    if seg.endswith("县"):
        return f"{romanize_place(seg[:-1])} County"
    if seg.endswith("市"):
        return f"{romanize_place(seg[:-1])} City"
    if seg.endswith("州"):
        return f"{romanize_place(seg[:-1])} Prefecture"
    if seg in PROV:
        return PROV[seg]
    if has_cjk(seg):
        for k, v in sorted(PROV.items(), key=lambda x: -len(x[0])):
            if seg.startswith(k):
                rest = seg[len(k):]
                return v + ((" / " + translate_admin_segment(rest)) if rest else "")
        return romanize_place(seg)
    return seg


def translate_name(name: str) -> str:
    if name in NAME_EN:
        return NAME_EN[name]
    bare = name.strip("《》")
    if bare in BOOK_EN:
        return BOOK_EN[bare]
    if name.startswith("《") and name.endswith("》"):
        if bare in BOOK_EN:
            return BOOK_EN[bare]
        return py_title(bare)
    working = apply_ethnic_tokens(name)
    for suf, en_suf in SUFFIX:
        if working.endswith(suf) and len(working) > len(suf):
            stem = working[: -len(suf)]
            stem_en = _translate_name_stem(stem)
            return stem_en + en_suf
    return _translate_name_stem(working)


def _translate_name_stem(stem: str) -> str:
    if not stem:
        return stem
    stem = restore_ethnic_tokens(stem)
    if stem in PLACE_ROMAN:
        return PLACE_ROMAN[stem]
    if stem in NAME_EN:
        return NAME_EN[stem]
    if has_cjk(stem):
        # 专名词干必须罗马化，禁止留下「法源 Temple」「忠 County」这类半截译
        return romanize_stem(stem)
    return stem


def translate_dyn_list(text: str) -> str:
    if not text:
        return "as recorded"
    # split by 、,，,
    parts = re.split(r"[、,，/／\s]+", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p in DYN:
            out.append(DYN[p])
        elif has_cjk(p):
            # try partial
            hit = False
            for k, v in DYN.items():
                if k in p:
                    out.append(v)
                    hit = True
                    break
            if not hit:
                out.append(py_title(p))
        else:
            out.append(p)
    return ", ".join(out) if out else "as recorded"


def translate_place(loc: str) -> str:
    if not loc:
        return "n/a"
    chunks = [c.strip() for c in re.split(r"\s*/\s*", loc) if c.strip()]
    eng = [translate_admin_segment(c) for c in chunks]
    return " / ".join(eng)


def strip_cjk(s: str) -> str:
    return re.sub(r"[\u4e00-\u9fff]+", " ", s or "").strip()


def clean_en_text(s: str) -> str:
    """Remove leftover CJK; compress spaces."""
    if not s:
        return s
    # replace known dyn/region tokens first
    out = s
    for k, v in sorted(DYN.items(), key=lambda x: -len(x[0])):
        out = out.replace(k, v)
    for k, v in REG.items():
        out = out.replace(k, v)
    for k, v in sorted(PROV.items(), key=lambda x: -len(x[0])):
        out = out.replace(k, v)
    out = re.sub(r"[\u4e00-\u9fff]+", "", out)
    out = re.sub(r"[（）]", "", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" ,.;")
    return out


def heritage_en_fields(n: dict) -> tuple[str, str, str]:
    name = re.sub(r"（国保(?:\d+)?）", "", n["name"]).strip()
    en = translate_name(name)
    if has_cjk(en):
        en = re.sub(
            r"[\u4e00-\u9fff]+",
            lambda m: "".join(p.capitalize() for p in lazy_pinyin(m.group(0), style=Style.NORMAL)),
            en,
        )
        en = re.sub(r"\s{2,}", " ", en).strip()
    # 非遗概念节点：不是国保点
    if "非遗" in name:
        return en, en + ".", en + "."
    desc = n.get("desc") or n.get("detail") or ""
    m_era = re.search(r"时代：([^。]+)", desc)
    m_loc = re.search(r"位置：([^。]+)", desc)
    m_reg = re.search(r"分区：([^。]+)", desc)
    era = translate_dyn_list(m_era.group(1) if m_era else "")
    loc = translate_place(m_loc.group(1) if m_loc else "")
    if has_cjk(loc):
        loc = " / ".join(
            translate_admin_segment(c.strip()) if has_cjk(c) else c.strip()
            for c in loc.split("/")
            if c.strip()
        )
        if has_cjk(loc):
            loc = "".join(
                p.capitalize()
                for p in lazy_pinyin(re.sub(r"[^\u4e00-\u9fff]+", "", loc), style=Style.NORMAL)
            ) or "n/a"
    reg_raw = (m_reg.group(1) if m_reg else "").strip()
    reg = REG.get(reg_raw, romanize_place(reg_raw) if reg_raw else "n/a")
    if m_era:
        en_detail = (
            f"National Priority Protected Cultural Heritage Site. "
            f"Period: {era}. Location: {loc}. Region: {reg}."
        )
    else:
        en_detail = (
            f"National Priority Protected Cultural Heritage Site. "
            f"Location: {loc}. Region: {reg}."
        )
    return en, en_detail, en_detail


def book_en_fields(n: dict) -> tuple[str, str, str]:
    bare = n["name"].strip("《》")
    en = BOOK_EN.get(bare) or translate_name(n["name"])
    if has_cjk(en):
        en = py_title(bare)
    # 已有合格英文标题则保留（含括号意译）
    old_en = n.get("en") or ""
    if old_en and not has_cjk(old_en) and re.search(r"[A-Za-z]", old_en):
        # 半截译（汉字+Temple）不要保留
        if not re.search(r"[\u4e00-\u9fff]", old_en):
            en = old_en
    traits = n.get("traits") or []
    author = ""
    for t in traits:
        if t.startswith("作者："):
            author = t.replace("作者：", "").strip()
    author_en = py_title(author) if author and has_cjk(author) else author
    blob = (n.get("desc") or "") + (n.get("detail") or "")
    m = re.search(r"时代：([^。]+)", blob)
    period = translate_dyn_list(m.group(1) if m else "")
    old_desc = n.get("enDesc") or ""
    old_detail = n.get("enDetail") or ""
    # 已有无汉字且像体裁说明的 enDesc，不要覆盖成空壳
    keep_desc = old_desc and not has_cjk(old_desc) and len(old_desc) >= 8 and not old_desc.startswith("Historical text on timber")
    keep_detail = old_detail and not has_cjk(old_detail) and len(old_detail) >= 20 and "Historical text on timber joinery" not in old_detail
    if keep_desc and keep_detail:
        return en, old_desc, old_detail
    en_detail = f"Historical text related to timber joinery and craft vocabulary. Title: {en}."
    if author_en:
        en_detail += f" Author: {author_en}."
    if period and period != "as recorded":
        en_detail += f" Period: {period}."
    en_desc = old_desc if keep_desc else (en_detail.split(". ")[0] + ".")
    return en, en_desc, en_detail


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    if not m:
        raise SystemExit("parse fail")
    prefix, raw, suffix = m.group(1), m.group(2), m.group(3)
    data = json.loads(raw)

    fixed_en = fixed_body = 0
    for n in data["nodes"]:
        t = n.get("type")
        if t == "heritage":
            en, ed, edt = heritage_en_fields(n)
            if n.get("en") != en or has_cjk(n.get("en") or "") or has_cjk(n.get("enDesc") or ""):
                fixed_en += 1
            n["en"], n["enDesc"], n["enDetail"] = en, ed, edt
            fixed_body += 1
        elif t == "literature":
            en, ed, edt = book_en_fields(n)
            n["en"], n["enDesc"], n["enDetail"] = en, ed, edt
            fixed_body += 1
        else:
            for k in ("en", "enDesc", "enDetail"):
                v = n.get(k) or ""
                if has_cjk(v):
                    if k == "en":
                        n[k] = translate_name(n["name"])
                        if has_cjk(n[k]):
                            n[k] = py_title(re.sub(r"[《》]|（.*?）", "", n["name"]))
                    else:
                        n[k] = clean_en_text(v)
                    fixed_body += 1

    leaks = [
        (n["id"], k, n[k][:80])
        for n in data["nodes"]
        for k in ("en", "enDesc", "enDetail")
        if has_cjk(n.get(k) or "")
    ]
    print("nodes", len(data["nodes"]), "heritage/lit refreshed; remaining CJK leaks", len(leaks))
    for row in leaks[:20]:
        print(" ", row)

    # 抽查关键样本
    for want in ("石宝寨", "潭柘寺", "法源寺", "释迦寺", "国家级非遗(2006)"):
        for n in data["nodes"]:
            if n.get("name") == want:
                print("SAMPLE", want, "=>", n.get("en"), "|", (n.get("enDesc") or "")[:110])
                break

    DATA.write_text(text[: m.start()] + prefix + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
