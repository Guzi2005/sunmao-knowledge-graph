# -*- coding: utf-8 -*-
"""地域二级节点：从古建 desc 的“位置：省 / 市县”提取省份，
生成省级 region 节点（level=2），省→一级分区挂边，古建→省挂边（保留原一级地域边）。
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

PROV_EN = {
    "北京": "Beijing", "天津": "Tianjin", "上海": "Shanghai", "重庆": "Chongqing",
    "河北": "Hebei", "山西": "Shanxi", "辽宁": "Liaoning", "吉林": "Jilin",
    "黑龙江": "Heilongjiang", "江苏": "Jiangsu", "浙江": "Zhejiang", "安徽": "Anhui",
    "福建": "Fujian", "江西": "Jiangxi", "山东": "Shandong", "河南": "Henan",
    "湖北": "Hubei", "湖南": "Hunan", "广东": "Guangdong", "广西": "Guangxi",
    "海南": "Hainan", "四川": "Sichuan", "贵州": "Guizhou", "云南": "Yunnan",
    "西藏": "Tibet", "陕西": "Shaanxi", "甘肃": "Gansu", "青海": "Qinghai",
    "宁夏": "Ningxia", "新疆": "Xinjiang", "内蒙古": "Inner Mongolia",
    "香港": "Hong Kong", "澳门": "Macau", "台湾": "Taiwan",
}
PY = {
    "北京": "beijing", "天津": "tianjin", "上海": "shanghai", "重庆": "chongqing",
    "河北": "hebei", "山西": "shanxi", "辽宁": "liaoning", "吉林": "jilin",
    "黑龙江": "heilongjiang", "江苏": "jiangsu", "浙江": "zhejiang", "安徽": "anhui",
    "福建": "fujian", "江西": "jiangxi", "山东": "shandong", "河南": "henan",
    "湖北": "hubei", "湖南": "hunan", "广东": "guangdong", "广西": "guangxi",
    "海南": "hainan", "四川": "sichuan", "贵州": "guizhou", "云南": "yunnan",
    "西藏": "xizang", "陕西": "shaanxi", "甘肃": "gansu", "青海": "qinghai",
    "宁夏": "ningxia", "新疆": "xinjiang", "内蒙古": "neimenggu",
    "香港": "xianggang", "澳门": "aomen", "台湾": "taiwan",
}


def norm_prov(raw: str) -> str | None:
    raw = raw.strip()
    for p in sorted(PROV_EN, key=len, reverse=True):
        if raw.startswith(p):
            return p
    return None


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    nodes, links = data["nodes"], data["links"]
    by_id = {n["id"]: n for n in nodes}
    exist_ids = set(by_id)

    # 古建 -> 一级地域
    site_region = {}
    for l in links:
        s, t = l["source"], l["target"]
        ns, nt = by_id.get(s), by_id.get(t)
        if ns and nt and ns.get("type") == "heritage" and nt.get("type") == "region":
            site_region[s] = t

    # 提取省份：优先“位置：省/市”，其次正文中明确的省名（含“浙江省”等）
    site_prov = {}
    prov_alt = re.compile(
        r"(?:位置[：:]\s*|位于|坐落于|在)(" + "|".join(sorted(PROV_EN, key=len, reverse=True)) + r")(?:省|市|自治区|特别行政区)?"
    )
    for n in nodes:
        if n.get("type") != "heritage":
            continue
        blob = (n.get("desc") or "") + (n.get("detail") or "")
        mm = re.search(r"位置[：:]\s*([^/。；\n]+)", blob)
        p = norm_prov(mm.group(1)) if mm else None
        if not p:
            mm2 = prov_alt.search(blob)
            if mm2:
                p = mm2.group(1)
        if p and p in PY:
            site_prov[n["id"]] = p

    # 省份节点 + 省->一级地域（按其下古建的一级分区多数决）
    prov_sites = {}
    for sid, p in site_prov.items():
        prov_sites.setdefault(p, []).append(sid)
    added_nodes = added_links = 0
    existing_names = {n["name"] for n in nodes}
    for p, sids in sorted(prov_sites.items(), key=lambda kv: -len(kv[1])):
        pid = "prov_" + PY[p]
        if pid in exist_ids:
            continue
        parents = Counter(site_region[s] for s in sids if s in site_region)
        parent = parents.most_common(1)[0][0] if parents else None
        parent_name = by_id[parent]["name"] if parent else ""
        node = {
            "id": pid,
            "name": p if p not in existing_names else p + "（省域）",
            "en": PROV_EN[p],
            "type": "region",
            "level": 2,
            "desc": "二级地域节点：%s，共辖 %d 处收录古建%s。" % (p, len(sids), ("，主属「" + parent_name + "」区系") if parent_name else ""),
            "enDesc": "Second-level region: %s, covering %d listed heritage sites%s." % (PROV_EN[p], len(sids), (" within the %s tradition" % by_id[parent].get("en", parent_name)) if parent else ""),
            "detail": "%s域内收录全国重点文物保护单位 %d 处，木构做法%s。" % (p, len(sids), ("总体归入「" + parent_name + "」体系") if parent_name else "各具地方特色"),
            "enDetail": "Province-level grouping of %d heritage sites in %s." % (len(sids), PROV_EN[p]),
            "traits": [],
            "refs": [],
        }
        nodes.append(node)
        by_id[pid] = node
        exist_ids.add(pid)
        added_nodes += 1
        if parent:
            links.append({"source": pid, "target": parent, "relation": "隶属分区", "relationEn": "Subregion of"})
            added_links += 1

    # 古建 -> 省份
    exist_pairs = {(l["source"], l["target"]) for l in links}
    for sid, p in site_prov.items():
        pid = "prov_" + PY[p]
        if (sid, pid) not in exist_pairs and (pid, sid) not in exist_pairs:
            links.append({"source": sid, "target": pid, "relation": "省份", "relationEn": "Province"})
            added_links += 1

    print("provinces added:", added_nodes, "| links added:", added_links,
          "| sites with province:", len(site_prov), "/", sum(1 for n in nodes if n.get("type") == "heritage"))
    print("province histogram:", dict(sorted(((p, len(s)) for p, s in prov_sites.items()), key=lambda kv: -kv[1])))
    DATA.write_text(text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
