# -*- coding: utf-8 -*-
"""English translation review: enrich key nodes, fix empty quote tr, fu jian zhu."""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"
text = DATA.read_text(encoding="utf-8")
m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
data = json.loads(m.group(2))
by = {n["id"]: n for n in data["nodes"]}

# 隈研吾：负建筑 fu jian zhu
n = by["kengoyama"]
n["enDetail"] = (
    "Kengo Kuma advocates fu jian zhu ('negative architecture')—architecture that yields to site, "
    "climate and material rather than asserting a solitary object. In works like the Bamboo House at "
    "the foot of the Great Wall, CNC-precise joints let steel and timber interlock with the grace of "
    "wood joinery, carrying East Asian node wisdom into contemporary materials."
)

# 核心典籍英文摘要补全
LIT_EN = {
    "yingzaofashi": (
        "Song-dynasty state building manual (1103) codifying modular timber joinery.",
        "Li Jie's Yingzao Fashi (1103) is China's first systematic official treatise on timber "
        "joinery and construction. Its caifen module governs member sizes, bracket ranks and labour "
        "quotas—foundational for later palace carpentry.",
    ),
    "gongcheng": (
        "Qing imperial building regulations using the doukou module.",
        "The Qing Gongcheng Zuofa Zeli replaced Song caifen with the doukou module while extending "
        "Song framing logic. It became the standard for palace and temple construction in the High Qing.",
    ),
    "kaogong": (
        "Warring States craft treatise—the earliest classical record of woodworking.",
        "The Kaogongji documents the 'gong mu' (woodworking) craft among state artificers, preserving "
        "early terminology and practice that foreshadows later mortise-and-tenon development.",
    ),
    "tiangong": (
        "Ming encyclopedia of crafts by Song Yingxing.",
        "Song Yingxing's Tiangong Kaiwu (1637) surveys Ming crafts including bow-making with "
        "'interlocking tenon' assembly—showing joinery logic beyond buildings and furniture.",
    ),
    "mingshi": (
        "Wang Shixiang's landmark study of Ming furniture joinery.",
        "Wang Shixiang's Studies in Ming Furniture argues that Ming classic furniture is essentially "
        "a joinery system—fastener-free, knockdown-friendly, and structurally expressive.",
    ),
}
for nid, (ed, edt) in LIT_EN.items():
    if nid in by:
        by[nid]["enDesc"] = ed
        by[nid]["enDetail"] = edt

# 圣经摘录：补全空白译文
BIBLE_TR = {
    "book_025": [
        "用皂策木作帐幕竖板，每块两端各出一榫相对，板底设带卯的银座承接两榫。",
        "竖板每块长十肘、宽一肘半，两端各出一榫，以带卯银座固定承接。",
    ],
    "book_026": [
        "皂荚木竖板每块两端各出一榫，板下以带卯银座对接两榫。",
        "帐幕竖板每块设两榫，下方以带卯银座承接榫头。",
    ],
    "book_051": [
        "皂荚木竖板每块两端各出一榫，板下置带卯银座承接。",
        "竖板每块长十肘、宽一肘半，两端必各出一榫，以带卯银座承接固定。",
    ],
}
for bid, trs in BIBLE_TR.items():
    n = by.get(bid)
    if not n or not n.get("quotes"):
        continue
    for i, q in enumerate(n["quotes"]):
        if not (q.get("tr") or "").strip() and i < len(trs):
            q["tr"] = trs[i]

# 日本节点：补 traits 英文对应已在 enDetail，微调 enDesc
by["japan"]["enDesc"] = "Tang-derived timber framing and refined kiwari proportioning in Japanese temples."

DATA.write_text(m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print("patched", len(LIT_EN), "literature,", len(BIBLE_TR), "bible books, kengoyama")
