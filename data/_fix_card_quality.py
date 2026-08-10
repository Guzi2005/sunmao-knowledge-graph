# -*- coding: utf-8 -*-
"""卡片内容质量修复：
1) 原文摘录：清除与原文高度重复的“译文”（仅改数字/略改词序）
2) 节点内原文去重
3) 删除 traits 中的「相关条目：N」
4) 修正若干已知错误/敷衍翻译
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

NUM = {
    "零": "0", "〇": "0", "一": "1", "二": "2", "两": "2", "三": "3", "四": "4",
    "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
    "壹": "1", "贰": "2", "叁": "3", "肆": "4", "伍": "5", "陆": "6",
    "柒": "7", "捌": "8", "玖": "9", "拾": "10", "染": "7",
}
FILLER = re.compile(
    r"(厚度为|构件|各|设|配合|开出|做|为|进行|加以|予以|其|之|等|了|着|过)"
)
PUNCT = re.compile(r"[，,。．.、；;：:\s　（）()\[\]【】“”\"'‘’《》<>·・]+")


def core(s: str) -> str:
    s = s or ""
    for a, b in NUM.items():
        s = s.replace(a, b)
    s = PUNCT.sub("", s)
    s = FILLER.sub("", s)
    return s


def sim(a: str, b: str) -> float:
    a, b = core(a), core(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    sa, sb = set(a), set(b)
    j = len(sa & sb) / max(1, len(sa | sb))
    cont = a in b or b in a
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    hit = sum(1 for ch in shorter if ch in longer)
    seq = hit / max(1, len(shorter))
    return max(j, seq, 1.0 if cont else 0.0)


# 明确重写的译文（cn 前缀 -> 新 tr；空串表示删除 tr）
TR_FIX = {
    ("《热河工程则例》", "捌角柱子两头做榫"): "",  # 仅大小写数字差异，删译文
    ("《热河工程则例》", "打透榫眼厚伍寸至染寸"): "透榫眼厚度做成五寸至七寸。",
    ("《热河工程则例》", "打透榫眼厚捌寸至壹尺"): "透榫眼厚度做成八寸至一尺。",
    ("《热河工程则例》", "地伏落槽打榫窝"): "地伏构件开槽并凿榫窝，兼作过水沟。",
    ("《江南制造局记》", "查"): "",  # 与原文几乎同句复述，删
    ("《江南制造局记》", "阳榫二只"): "两只阳榫，各长六分半；滑板与床架对应处开出笋槽。",
    ("《江南制造局记》", "装膛上开螺丝"): "炮闩部位开斜槽、销眼与机槽，供零件精密啮合。",
    ("《江南制造局记》", "扳机旁孔卯"): "扳机旁与扳机架后端均设卯孔，以销钉连接扳机构件。",
}

# 英文错误修正（节点名 -> 字段补丁）
EN_FIX = {
    # 示例位：后续按需扩展
}


def match_fix(name: str, cn: str):
    for (nm, pref), new_tr in TR_FIX.items():
        if name == nm and cn.startswith(pref):
            return new_tr
    return None


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))

    cleared_tr = 0
    fixed_tr = 0
    dropped_quote = 0
    cleared_traits = 0

    for n in data["nodes"]:
        name = n.get("name") or ""

        # traits: 删除「相关条目：N」
        traits = n.get("traits")
        if traits:
            kept = [t for t in traits if not re.match(r"^\s*相关条目\s*[：:]", str(t))]
            if len(kept) != len(traits):
                cleared_traits += len(traits) - len(kept)
                if kept:
                    n["traits"] = kept
                else:
                    n.pop("traits", None)

        # quotes cleanup
        quotes = n.get("quotes")
        if not quotes:
            continue
        new_quotes = []
        seen_cn = []
        for q in quotes:
            cn = (q.get("cn") or "").strip()
            tr = (q.get("tr") or "").strip()
            if not cn:
                dropped_quote += 1
                continue
            # 节点内原文近重去重
            dup = False
            for prev in seen_cn:
                if sim(cn, prev) >= 0.92:
                    dup = True
                    break
            if dup:
                dropped_quote += 1
                continue
            seen_cn.append(cn)

            # 手工修正优先
            forced = match_fix(name, cn)
            if forced is not None:
                if forced == "":
                    tr = ""
                    cleared_tr += 1
                else:
                    tr = forced
                    fixed_tr += 1
            elif tr:
                # 译文与原文高度重合 → 删除译文
                if sim(cn, tr) >= 0.78:
                    tr = ""
                    cleared_tr += 1

            item = {"cn": cn}
            if tr:
                item["tr"] = tr
            new_quotes.append(item)

        if new_quotes:
            n["quotes"] = new_quotes
        else:
            n.pop("quotes", None)

        # EN fixes
        if name in EN_FIX:
            for k, v in EN_FIX[name].items():
                n[k] = v

    out = text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    DATA.write_text(out, encoding="utf-8")
    print("cleared near-dup tr:", cleared_tr)
    print("fixed tr:", fixed_tr)
    print("dropped quote blocks:", dropped_quote)
    print("removed 相关条目 traits:", cleared_traits)


if __name__ == "__main__":
    main()
