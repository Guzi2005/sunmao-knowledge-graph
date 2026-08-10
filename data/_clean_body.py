# -*- coding: utf-8 -*-
"""精简正文：去除“时代/作者”行与开头重复的节点名；古籍原文+译文结构化为 quotes 字段。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"
GUJI = Path(r"D:\D盘桌面\榫卯\code\extracted\guji_rows.json")


def bare_title(s: str) -> str:
    return (s or "").strip().strip("《》")


def clean_cn(text: str, name: str) -> str:
    s = (text or "").strip()
    if not s:
        return s
    # 摘句列表已结构化为 quotes，正文里删掉
    s = re.sub(r"\s*原文摘句：.*$", "", s, flags=re.S)
    s = re.sub(r"\s*相关摘句：.*$", "", s, flags=re.S)
    # 删除“作者：/时代：”句
    s = re.sub(r"作者：[^。；]*[。；]?", "", s)
    s = re.sub(r"时代：[^。；]*[。；]?", "", s)
    # 开头重复节点名（仅当后随标点，避免误伤自然句）
    b = bare_title(name)
    for v in (name, f"《{b}》", b):
        if v and s.startswith(v):
            rest = s[len(v):]
            if rest[:1] in ("，", ",", "。", "：", ":", "、", "；", ""):
                s = rest.lstrip("，,。：:、； ")
                break
    return s.strip()


def clean_en(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return s
    s = re.sub(r"Title:\s*[^.]*\.\s*", "", s)
    s = re.sub(r"Author:\s*[^.]*\.\s*", "", s)
    s = re.sub(r"Period(?: label)?:\s*[^.]*\.\s*", "", s)
    s = re.sub(r"Sample:\s*$", "", s).strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))

    guji = json.loads(GUJI.read_text(encoding="utf-8"))
    by_book: dict[str, list[dict]] = {}
    for r in guji:
        b = bare_title(r.get("书名") or "")
        if b:
            by_book.setdefault(b, []).append(r)

    quoted = cleaned = 0
    for n in data["nodes"]:
        name = n.get("name") or ""
        # 古籍：结构化 quotes（古文 + 译文）
        if n.get("type") == "literature":
            rows = by_book.get(bare_title(name)) or []
            quotes = []
            for r in rows:
                cn = (r.get("原文片段") or "").strip()
                tr = (r.get("翻译") or "").strip()
                if not cn:
                    continue
                quotes.append({"cn": cn, "tr": tr})
                if len(quotes) >= 4:
                    break
            if quotes:
                n["quotes"] = quotes
                quoted += 1

        for k in ("desc", "detail"):
            v = n.get(k)
            if v:
                nv = clean_cn(v, name)
                if nv != v:
                    n[k] = nv
                    cleaned += 1
        for k in ("enDesc", "enDetail"):
            v = n.get(k)
            if v:
                nv = clean_en(v)
                if nv != v:
                    n[k] = nv
                    cleaned += 1

        # 古籍正文清空后给极简兜底（内容主体交给 quotes）
        if n.get("type") == "literature":
            if len((n.get("detail") or "").strip()) < 6:
                n["detail"] = ""
            if len((n.get("desc") or "").strip()) < 6:
                n["desc"] = "古籍文献，载有榫卯相关记述。"
            if len((n.get("enDetail") or "").strip()) < 6:
                n["enDetail"] = ""
            if len((n.get("enDesc") or "").strip()) < 6:
                n["enDesc"] = "Historical text preserving passages on mortise-and-tenon joinery."

    print("quotes added:", quoted, " fields cleaned:", cleaned)
    DATA.write_text(text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
