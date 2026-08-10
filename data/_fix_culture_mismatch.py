# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "sunmao-graph.source.js"
text = DATA.read_text(encoding="utf-8")
m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
data = json.loads(m.group(2))
by = {n["id"]: n for n in data["nodes"]}

n = by["kengoyama"]
n["en"] = "Kengo Kuma"
n["enDesc"] = (
    "Japanese architect Kengo Kuma; CNC-precise joinery in works such as "
    "the Bamboo House at the Great Wall."
)
n["enDetail"] = (
    "Kengo Kuma advocates anti-object architecture of material humility. "
    "In works like the Bamboo House at the foot of the Great Wall, CNC-precise joints "
    "let steel and timber interlock with the grace of wood joinery, carrying East Asian "
    "node wisdom into contemporary materials."
)
n["desc"] = "日本建筑师隈研吾；长城脚下“竹屋”等作品以数控精密榫卯让钢、木如木作般优雅咬合。"
n["detail"] = (
    "隈研吾主张“负建筑”，强调材料谦和。长城脚下竹屋等作品用数控（CNC）精密榫卯，"
    "使钢与木优雅咬合，把东方节点智慧带入当代材料体系。"
)
n["traits"] = [
    "隈研吾：“负建筑”与材料谦和",
    "CNC精密榫卯连接钢木",
    "东方节点智慧入当代材料",
]

n = by["oumei"]
n["name"] = "欧美井干造"
n["en"] = "Euro-American Log Construction"
n["enDesc"] = (
    "Log / well-frame timber houses with corner notches—"
    "Western parallels to interlocking dry joins."
)
n["enDetail"] = (
    "Across Europe and North America, horizontally stacked log houses use corner notches "
    "akin to a well-curb (jinggan). Though distinct from Chinese tenon systems, the dry "
    "interlock at corners is a cognate solution for all-timber envelopes."
)
n["desc"] = "原木如井字层叠的全木屋（井干造）见于欧美各地，角部咬合方式各异，与东方榫卯异曲同工。"
n["detail"] = (
    "欧美传统原木屋将圆木水平层叠，角部开槽互卡，形如井栏（井干）。"
    "节点多为角部榫槽而非东方榫卯体系，但“干式咬合、全木围合”的思路可对照理解。"
)
n["traits"] = [
    "原木水平层叠的井干/木屋",
    "角部开槽咬合，各地做法不同",
    "与东方榫卯异曲同工的干式互锁",
]

# 朝鲜半岛英文标题与正文一致
n = by["korea"]
n["en"] = "Korean Peninsula"
if n.get("enDesc") == "Palace and temple woodwork in dialogue with Chinese official styles.":
    pass  # already fine

DATA.write_text(m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print("ok", by["kengoyama"]["en"], by["oumei"]["en"], by["korea"]["en"])
