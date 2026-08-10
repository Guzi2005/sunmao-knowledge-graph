# -*- coding: utf-8 -*-
"""书名英译人工润色：知名书用通行译名；长题直译；其余拼音+书名式意译。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

TITLES = {
    "《营造法式》": "Yingzao Fashi (Treatise on Architectural Methods)",
    "《工程做法则例》": "Gongcheng Zuofa Zeli (Imperial Building Regulations)",
    "《天工开物》": "Tiangong Kaiwu (The Exploitation of the Works of Nature)",
    "《考工记》": "Kaogongji (Records of Artificers)",
    "《楚辞·二程遗书》": "Songs of Chu · Posthumous Writings of the Two Chengs",
    "《酌中志》": "Zhuozhong Zhi (An Insider's Record of the Ming Palace)",
    "《蚕桑萃编》": "Cansang Cuibian (Compendium of Sericulture)",
    "《中外农学合编》": "Combined Compilation of Chinese and Foreign Agronomy",
    "《野蚕录》": "Yecan Lu (Records of Wild Silkworms)",
    "《游艺录》": "Youyi Lu (Records of Arts and Crafts)",
    "《安定东直朝阳等门城墙宇墙马道门楼等工丈尺做法清册》":
        "Inventory of Dimensions and Construction Methods for the Walls, Parapets, Ramps and Gate Towers of the Anding, Dongzhi and Chaoyang Gates",
    "《内廷做法》": "Construction Methods of the Inner Court",
    "《内庭工程做法》": "Engineering Methods of the Inner Court",
    "《清实录》": "Veritable Records of the Qing Dynasty",
    "《吹剑录外集》": "Chuijian Lu Waiji (Supplementary Essays to the Chuijian Records)",
    "《永定河志》": "Yongding He Zhi (Gazetteer of the Yongding River)",
    "《方氏墨谱》": "Fangshi Mopu (Master Fang's Ink Catalogue)",
    "《新旧约全书》": "The Complete Old and New Testaments (Chinese Bible)",
    "《旧新约全书串珠》": "The Old and New Testaments with Cross-References",
    "《旧新约全书》": "The Complete Old and New Testaments (Chinese Bible)",
    "《事物异名录》": "Shiwu Yiming Lu (Records of Alternative Names of Things)",
    "《南皮县志》": "Nanpi Xian Zhi (Nanpi County Gazetteer)",
    "《通俗编》": "Tongsu Bian (Compendium of Popular Expressions)",
    "《武备要略》": "Wubei Yaolüe (Essentials of Military Preparedness)",
    "《蹶张心法》": "Juezhang Xinfa (Essential Methods of Crossbow Drawing)",
    "《古今图书集成·考工典》": "Imperial Encyclopedia (Gujin Tushu Jicheng) · Crafts Section",
    "《武备水火攻》": "Wubei Shuihuogong (Military Preparedness: Water and Fire Attacks)",
    "《古今图书集成·字学典》": "Imperial Encyclopedia (Gujin Tushu Jicheng) · Philology Section",
    "《字汇十二集》": "Zihui (Character Dictionary in Twelve Collections)",
    "《博山县乡土志》": "Boshan Xian Xiangtu Zhi (Local Gazetteer of Boshan County)",
    "《名义考》": "Mingyi Kao (Study of Names and Meanings)",
    "《定海县志》": "Dinghai Xian Zhi (Dinghai County Gazetteer)",
    "《程氏墨苑》": "Master Cheng's Ink Garden",
    "《御定韵府拾遗》": "Yuding Yunfu Shiyi (Imperial Supplement to the Rhyme Treasury)",
    "《耕余剩技》": "Gengyu Shengji (Martial Skills for Hours after Farming)",
    "《威县志》": "Wei Xian Zhi (Wei County Gazetteer)",
    "《新刻松盛旧编》": "Xinke Songsheng Jiubian (Newly Engraved Old Compilation of Songsheng)",
    "《永报堂集》": "Yongbaotang Ji (Anthology of the Yongbao Hall)",
    "《畿辅水利四案》": "Four Cases of Water Conservancy in the Capital Region",
    "《治平胜算全书》": "Zhiping Shengsuan Quanshu (Complete Book of Strategic Calculations)",
    "《安澜纪要》": "Anlan Jiyao (Essentials of River Pacification)",
    "《上海毕士大福音堂主日讲题》": "Sunday Sermon Topics of the Bethesda Gospel Hall, Shanghai",
    "《地宫作法》": "Digong Zuofa (Construction Methods for Underground Palaces)",
    "《数学九章》": "Shuxue Jiuzhang (Mathematical Treatise in Nine Chapters)",
    "《四国游记》": "Siguo Youji (Travels in Four Countries)",
    "《初使泰西记》": "Chushi Taixi Ji (Records of the First Mission to the West)",
    "《江南制造局记》": "Jiangnan Zhizaoju Ji (Records of the Jiangnan Arsenal)",
    "《畿辅安澜志》": "Jifu Anlan Zhi (Gazetteer of River Pacification in the Capital Region)",
    "《谐声品字笺》": "Xiesheng Pinzi Jian (Phonetic Annotations for Classifying Characters)",
    "《治政集要》": "Zhizheng Jiyao (Essentials of Governance)",
    "《钦定大清会典》": "Collected Statutes of the Great Qing (Imperially Commissioned)",
    "《镇海县志》": "Zhenhai Xian Zhi (Zhenhai County Gazetteer)",
    "《工艺学》": "Gongyi Xue (Craft Technology)",
    "《增定雅俗稽言》": "Zengding Yasu Jiyan (Expanded Examination of Refined and Popular Sayings)",
    "《雅尚斋遵生八笺》": "Yashangzhai Edition of the Eight Treatises on Following the Principles of Life",
    "《庄子通义》": "Zhuangzi Tongyi (A General Exposition of the Zhuangzi)",
    "《文选集释二十四卷》": "Wenxuan Jishi (Collected Annotations on the Selections of Refined Literature)",
    "《临朐续志》": "Linqu Xuzhi (Continued Gazetteer of Linqu County)",
    "《洹词》": "Huan Ci (Writings from the Huan River)",
    "《道宗六书》": "Daozong Liushu (Six Books of the Daoist Tradition)",
    "《城守筹略》": "Chengshou Choulüe (Strategies for City Defense)",
    "《国朝文纂》": "Guochao Wenzuan (Literary Compilation of the Reigning Dynasty)",
    "《兵录》": "Bing Lu (Records of Military Affairs)",
    "《字触补》": "Zichu Bu (Supplement to Character Riddles)",
    "《康济谱》": "Kangji Pu (Manual of Public Welfare and Relief)",
    "《七修续稿》": "Qixiu Xugao (Sequel to the Draft Notes in Seven Categories)",
    "《枪𪿫学》": "Qiangpao Xue (Science of Firearms)",
    "《说文闽音通》": "Shuowen Minyin Tong (The Shuowen with Min Pronunciations)",
    "《嵩年奏档》": "Songnian Zoudang (Memorial Archives of Songnian)",
    "《农政全书》": "Nongzheng Quanshu (Complete Treatise on Agricultural Administration)",
    "《莫氏四种》": "Moshi Sizhong (Four Works of the Mo Family)",
    "《事物绀珠》": "Shiwu Ganzhu (A Classified Encyclopedia of Things)",
    "《发微历眼通书大全》": "Fawei Liyan Tongshu Daquan (Complete Divination Almanac)",
    "《测地绘图》": "Land Surveying and Mapping",
    "《永觉和尚禅余内集》": "Inner Collection of Chan Master Yongjue's Leisure Writings",
    "《老子通义》": "Laozi Tongyi (A General Exposition of the Laozi)",
    "《字学指南》": "Zixue Zhinan (A Guide to the Study of Characters)",
    "《经济备要三种》": "Jingji Beiyao Sanzhong (Three Works of Essential Statecraft)",
    "《泰西水法》": "Taixi Shuifa (Hydraulic Machinery of the West)",
    "《遂初堂集》": "Suichutang Ji (Anthology of the Suichu Hall)",
    "《五朝小说》": "Wuchao Xiaoshuo (Tales of Five Dynasties)",
}


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    hit = 0
    for n in data["nodes"]:
        if n.get("type") == "literature" and n["name"] in TITLES:
            n["en"] = TITLES[n["name"]]
            hit += 1
    print("updated", hit, "of", len(TITLES))
    missing = [k for k in TITLES if not any(x["name"] == k for x in data["nodes"])]
    if missing:
        print("no-match:", missing)
    DATA.write_text(text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
