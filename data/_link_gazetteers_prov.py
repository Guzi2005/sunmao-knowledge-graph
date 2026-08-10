# -*- coding: utf-8 -*-
"""把县志/方志类典籍挂到对应省级（二级地域）节点。"""
from __future__ import annotations

import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"

# 书名关键词 → 省级节点 id（可一对多）
GAZETTEER_PROV = {
    "南皮县志": ["prov_hebei"],
    "威县志": ["prov_hebei"],
    "博山县乡土志": ["prov_shandong"],
    "临朐续志": ["prov_shandong"],
    "定海县志": ["prov_zhejiang"],
    "镇海县志": ["prov_zhejiang"],
    "永定河志": ["prov_beijing", "prov_hebei"],  # 永定河京冀
    "畿辅安澜志": ["prov_hebei", "prov_beijing", "prov_tianjin"],  # 畿辅
    "酌中志": ["prov_beijing"],  # 宫禁见闻，系于京师
}


def main() -> None:
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    by = {n["id"]: n for n in data["nodes"]}
    exist = {(l["source"], l["target"]) for l in data["links"]}
    added = 0
    matched = []

    for n in data["nodes"]:
        if n.get("type") != "literature":
            continue
        name = n.get("name") or ""
        bare = name.strip("《》")
        provs = None
        for key, pids in GAZETTEER_PROV.items():
            if key in name or key in bare:
                provs = pids
                break
        if not provs:
            # 通用：书名含「××县志/府志/州志」时尝试从已有省名匹配
            mm = re.search(r"([\u4e00-\u9fff]{2,8})(?:县|府|州|厅)?(?:乡土)?(?:续)?志", bare)
            if not mm:
                continue
            # fallback only if already mapped keys missed
            continue

        matched.append((n["id"], name, provs))
        for pid in provs:
            if pid not in by:
                print("missing prov", pid)
                continue
            if (n["id"], pid) in exist or (pid, n["id"]) in exist:
                continue
            data["links"].append({
                "source": n["id"],
                "target": pid,
                "relation": "记述地域",
                "relationEn": "Locale of gazetteer",
            })
            exist.add((n["id"], pid))
            added += 1

    DATA.write_text(
        m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("matched", len(matched))
    for row in matched:
        print(" ", row)
    print("added links", added)


if __name__ == "__main__":
    main()
