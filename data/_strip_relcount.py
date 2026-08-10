# -*- coding: utf-8 -*-
"""彻底删除 traits 中的「相关条目：N」统计。"""
from __future__ import annotations

import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"
PAT = re.compile(r"^\s*相关条目\s*[：:].*$")


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    removed = 0
    for n in data["nodes"]:
        traits = n.get("traits")
        if not traits:
            continue
        kept = [t for t in traits if not PAT.match(str(t))]
        if len(kept) != len(traits):
            removed += len(traits) - len(kept)
            if kept:
                n["traits"] = kept
            else:
                n.pop("traits", None)
    DATA.write_text(
        text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("removed 相关条目 traits:", removed)


if __name__ == "__main__":
    main()
