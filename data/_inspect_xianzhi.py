# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"
text = DATA.read_text(encoding="utf-8")
m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
data = json.loads(m.group(2))
by = {n["id"]: n for n in data["nodes"]}

lit = []
for n in data["nodes"]:
    if n.get("type") != "literature":
        continue
    blob = (n.get("name") or "") + (n.get("desc") or "") + (n.get("detail") or "")
    if re.search(r"县志|府志|州志|厅志|通志|乡镇志|gazetteer", blob, re.I) or "志》" in (n.get("name") or ""):
        lit.append(n)

print("literature gazetteers", len(lit))
for n in lit:
    rels = []
    for l in data["links"]:
        if l["source"] != n["id"] and l["target"] != n["id"]:
            continue
        o = l["target"] if l["source"] == n["id"] else l["source"]
        on = by.get(o)
        rels.append(f"{(on or {}).get('type','?')}:{o}/{(on or {}).get('name','')}/{l.get('relation')}")
    print(n["id"], n["name"][:30], "|", " ; ".join(rels[:10]))
