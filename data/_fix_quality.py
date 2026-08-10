# -*- coding: utf-8 -*-
"""内容质量修复：
A. 榫卯节点：中文详情去英文混杂并补写真实描述；enDetail 与 enDesc 区分开
B. 古籍节点：按体裁+朝代生成有区分度的 enDesc/enDetail
C. 原文摘录：严格去重（规范化全等 + 包含关系 + 手工黑名单），补全缺失译文
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "sunmao-graph.source.js"

# ── A. 榫卯：name -> (中文详情, 英文详情) ──────────────────────
MORTISE = {
    "透榫": ("榫头贯穿卯眼、端头露于构件外侧的做法，常在露头处加木楔涨紧。多用于梁枋穿柱等受拉部位，牢固且便于检视。",
             "The tenon passes completely through the mortised member, its end grain exposed and often locked with a wedge. Used where beams or rails pierce columns, giving a strong, inspectable joint."),
    "馒头榫": ("柱头顶部凸起的短圆榫，形如馒头，与梁底的海眼相扣，用于固定柱头与梁头的相对位置，是抬梁式构架的常见做法。",
             "A short, bun-shaped stub tenon on top of a column head that seats into a socket under the beam, locating beam on column in northern post-and-lintel framing."),
    "箍头榫": ("枋出头处做成箍头，榫头穿过柱头卯口并箍住柱头，多见于清式建筑的转角与尽端开间，兼具结构与装饰作用。",
             "The rail end runs through the column-head mortise and is shaped to clasp (hoop) the column, common at corners of Qing-style buildings; both structural and decorative."),
    "管脚榫": ("柱脚底面留出的短榫，插入柱础或墩台上的卯口，防止柱脚水平移位，是木构架防侧移的基础性做法。",
             "A short tenon at the foot of a column that drops into a socket in the plinth, keeping the column foot from sliding sideways."),
    "交叉榫": ("两构件十字相交时各剔去一半断面后互卡，接合面咬合紧密，常见于枨子、格架等交叉部位。",
             "Where two members cross, each is notched to half depth so they interlock flush, as in stretchers and lattice frames."),
    "十字卡腰榫": ("圆材或带线脚的构件十字相交时，在腰部各剔去一半互相卡合的做法，常见于家具的十字枨、托泥等处。",
             "For round or moulded members crossing at right angles: each is waisted to half section so the two lock together, as in cross stretchers of furniture."),
    "穿榫": ("榫头穿过中间构件的卯眼后再与其他构件接合，起串联多个构件的作用，常见于穿斗式构架的穿枋。",
             "A tenon threads through an intermediate member before engaging the next, tying several members in a row; typical of through-rails in chuandou frames."),
    "暗榫": ("榫头藏于构件内部、表面不露端头的闷榫做法，外观整洁，多用于家具与装修的可见部位。",
             "The tenon is fully concealed within the joint so no end grain shows; favoured for the visible faces of furniture and joinery."),
    "巴掌榫": ("端头削成掌状的搭接面，两件如手掌相搭，接触面大、便于加销加固，常用于弧形或长材的接长。",
             "Ends are cut to broad palm-like lapping faces that overlap like clasped hands, giving a large glue/pin surface; used for scarfing long or curved members."),
    "半通榫": ("榫头插入卯眼但不穿透构件，深度约为卯件断面的一半，外表不露端头，强度与美观兼顾。",
             "The tenon enters the mortise but stops about halfway through the member, leaving no exposed end grain; a balance of strength and clean appearance."),
    "鼻子榫": ("端头留出鼻状的小凸榫，与对应凹口相扣定位，常用于构件对位与防错动。",
             "A small nose-like projection on the end locates into a matching recess, registering the two members against slip."),
    "叉子榫": ("端头开成叉口卡住对接构件的做法，形如叉子夹物，多用于枝条状构件的交接。",
             "The end is forked to straddle and grip the mating member, like a fork holding a stem."),
    "雌雄榫": ("一凸一凹成对咬合的榫式，凸为雄、凹为雌，配合紧密，常用于板材拼接与框料接合。",
             "A paired convex (male) and concave (female) profile that mate tightly; used for edge-joining boards and frame members."),
    "大进小出榫": ("榫头分大小两级：大头留在卯眼内，小头穿出构件外侧并可加销，兼顾强度与外观，多用于穿枋与额枋。",
             "A stepped tenon: the larger step stays inside the mortise while the smaller step passes out the far side to be pegged; strong yet tidy, common in penetrating rails."),
    "搭掌榫": ("两构件端头各削去一半厚度、如掌相搭的接长做法，接面可加销钉或胶合，常用于檩枋接续。",
             "Each end is halved so the two lap like overlapping palms, then pegged or glued; a standard splice for purlins and rails."),
    "顶空榫": ("卯眼上部留空、榫头不顶满的做法，为木材胀缩与安装留出余地，常见于需要落装的部位。",
             "The mortise is left open at the top so the tenon does not bear fully, allowing seasonal movement and drop-in assembly."),
    "鬭榫": ("构件相互斗合咬扣的榫式，取“斗”之相争相合之意，接合面互相锁定。",
             "An interlocking 'dou' joint in which the two members butt and lock into each other."),
    "对榫": ("两构件端头相对出榫、彼此插接的做法，多用于同断面构件的对接接长。",
             "Opposed tenons cut on facing ends plug into each other, splicing members of equal section end to end."),
    "二蹬榫": ("榫头做成两级台阶（蹬）的做法，逐级承压，增大受剪面，常用于较厚构件。",
             "The tenon is cut in two stepped tiers that bear in succession, enlarging the shear area for thick members."),
    "二合榫": ("由两件合成的组合榫，两半相抱合为一体，多用于需要围合或抱接的部位。",
             "A composite joint assembled from two halves that clasp together as one; used where members must wrap or embrace another."),
    "二肩蹬榫": ("带双肩并做蹬台的榫式，双肩抵压卯件表面，蹬台分级传力，接合稳定。",
             "A stepped tenon with twin shoulders: the shoulders bear on the mortised face while the step transfers load in stages."),
    "公母榫": ("公榫与母卯配对咬合的通称，公者凸、母者凹，是榫卯配合关系最直观的表达。",
             "The generic male-female pair: the protruding male tenon seats in the receiving female mortise."),
    "荷包榫": ("形如荷包的锁扣榫式，榫头入卯后被兜住难以拔出，多用于需抗拉拔的部位。",
             "A purse-shaped locking tenon that is pocketed by the mortise once seated, resisting withdrawal."),
    "鸡尾榫": ("尾部张开如鸡尾的榫式，与燕尾同理而形稍异，靠尾部放大抗拉。",
             "A splayed tail tenon akin to a dovetail: the widened tail resists pull-out."),
    "交口榫": ("构件在开口处相交咬合的做法，两口相咬、互为约束，常见于框料十字或丁字相交。",
             "Members meet at mouthed notches that bite into each other, restraining both; seen at cross and T intersections of frames."),
    "扣金式箍头榫": ("箍头榫的讲究做法，箍头雕作霸王拳等线脚并包掩交接，常用于官式建筑角部的额枋出头。",
             "An ornate variant of the hooped-head joint: the projecting head is carved (e.g. 'bawangquan' fist profile) to cap the corner junction in official-style architecture."),
    "龙舌榫": ("榫头做成长舌状，如龙舌探出，插入深卯，接触面长、导向性好。",
             "A long tongue-like tenon that reaches deep into its mortise, giving long bearing and good alignment."),
    "平接榫": ("构件端对端平齐接合的做法，接缝平整，常辅以暗榫或销钉加固。",
             "A flush end-to-end butt splice, usually reinforced with hidden tenons or pegs."),
    "骑马榫": ("构件如骑马般跨骑于另一构件之上的接合，骑口卡住下件，防止滚动与滑移。",
             "One member saddles astride another like a rider, the notch gripping the lower member against rolling and sliding."),
    "全通榫": ("榫头完全贯通卯件、两端均可见的做法，可两面加楔，接合最为牢固。",
             "The tenon runs fully through so both ends are visible and can be wedged from either face; the strongest through joint."),
    "三合榫": ("三个构件于一点相合的组合榫，常用于三向交汇的角部，如框架转角三碰肩。",
             "Three members meet and lock at one point, as at three-way frame corners."),
    "上下榫": ("构件上下两端均出榫的做法，上入梁底、下入础卯，柱类构件常用。",
             "Tenons are cut at both top and bottom of a member—into the beam above and the plinth below—typical of columns and posts."),
    "双肩直榫": ("直榫两侧留肩，双肩抵住卯件表面，抗扭且遮掩卯口，是最常用的直榫形式。",
             "A straight tenon with shoulders on both sides that bear against the mortised face, resisting racking and concealing the mortise; the standard form."),
    "双榫": ("并列出两个榫头的做法，双榫分担受力并防转动，多用于宽厚构件。",
             "Two parallel tenons share the load and stop rotation, used on wide or thick members."),
    "螳螂头榫": ("榫头头大颈细，形如螳螂头，入卯后头部卡住难以拔出，抗拉性能好，多用于拼板与接长。",
             "The tenon has a wide head on a narrow neck, like a mantis head; once seated the head locks against withdrawal, good for panels and splices."),
    "无肩直榫": ("不留肩的直榫，榫头与构件同宽径直入卯，制作简便，多用于隐蔽或次要部位。",
             "A shoulderless straight tenon the full width of the member; simple to cut, used in concealed or secondary positions."),
    "袖肩燕尾榫": ("燕尾榫带斜袖状肩部的做法，袖肩包掩卯口并增大承压面，常见于讲究的家具接合。",
             "A dovetail with sloped sleeve-like shoulders that cover the mortise mouth and add bearing; found in fine furniture."),
    "燕尾箍头复合榫": ("燕尾榫与箍头榫复合使用的做法，既抗拉拔又箍锁柱头，用于关键的角部节点。",
             "A compound of dovetail and hooped-head joints: it resists pull-out while clasping the column head, reserved for key corner nodes."),
    "阳榫": ("凸出的榫头一方，与阴卯相对而言，泛指外凸的接合构造。",
             "The protruding (yang) half of a joint, as opposed to the receiving yin mortise."),
    "阴榫": ("凹入的卯眼一方，与阳榫相对而言，泛指内凹的接合构造。",
             "The receiving (yin) half of a joint—the mortise—as opposed to the protruding yang tenon."),
    "阴阳榫": ("阳榫与阴卯成对配合的总称，一凸一凹、相入相合，是榫卯构造的基本原理。",
             "The complementary pairing of yang tenon and yin mortise—one convex, one concave—the elemental principle of all sunmao joinery."),
    "油桶榫": ("榫头做成圆柱桶状的做法，插入圆卯，可微量转动调节，常用于圆材接合。",
             "A cylindrical barrel-like tenon in a round mortise, allowing slight rotational adjustment; used with round members."),
    "元宝榫": ("形如元宝、两端大中间小的锁榫，嵌入对应卯槽后抗拉不脱，多用于拼板与案面。",
             "An ingot-shaped key, wide at both ends and waisted in the middle, let into matching sockets to draw boards together; common in tabletop panels."),
    "鸳鸯榫": ("成对咬合、左右对称的榫式，如鸳鸯成双，多用于对称构件的连接。",
             "A symmetrical pair of interlocking tenons, like mandarin ducks in a couple; joins mirrored members."),
    "中半通榫": ("深度居于半通与全通之间、榫头至构件中部的做法，用于较厚构件的稳固接合。",
             "A half-through tenon stopping near mid-depth of the member, for stout members needing extra bearing."),
    "周肩直榫": ("四周均留肩的直榫，榫头缩于断面中部，四面肩口抵压卯件，接合方正稳固。",
             "A straight tenon shouldered on all four sides, centred in the section so every face bears on the mortised member; square and stable."),
    "柱脚榫": ("柱脚部位的榫，插入地栿或柱础卯口，固定柱脚，与管脚榫同类而径稍大。",
             "The tenon at a column foot, entering the sill or plinth socket to fix the base; kin to the pipe-foot tenon but larger."),
    "柱内键榫": ("藏于柱身内部的键榫，用木键串联拼合柱料或加固接缝，外表不露痕迹。",
             "A key tenon hidden inside the column body, splining built-up column staves or reinforcing a splice with nothing showing outside."),
}

# ── B. 古籍体裁 ──────────────────────
GENRES = [
    (r"县志|乡土志|续志", "County gazetteer"),
    (r"河志|安澜|水利", "River-conservancy gazetteer"),
    (r"水法", "Treatise on hydraulics"),
    (r"会典", "Collection of dynastic statutes"),
    (r"实录", "Court annals"),
    (r"图书集成", "Section of the imperial encyclopedia Gujin Tushu Jicheng"),
    (r"大典", "Imperial encyclopedia"),
    (r"武备|兵录|城守|蹶张|神器|枪|砲|水火攻", "Military treatise"),
    (r"算|数学|测地", "Mathematical and surveying work"),
    (r"蚕|农学|农政", "Agronomy treatise"),
    (r"营造|做法|工程|清册|则例", "Building manual"),
    (r"墨苑|墨谱", "Illustrated ink catalogue"),
    (r"园冶", "Treatise on garden design"),
    (r"遵生", "Treatise on regimen and elegant living"),
    (r"新旧约|旧新约|福音", "Chinese edition of Christian scripture"),
    (r"游记|初使", "Travelogue"),
    (r"制造局", "Record of an industrial arsenal"),
    (r"通书|历眼", "Divination almanac"),
    (r"通义|语录|老子|庄子|道宗", "Philosophical commentary"),
    (r"说文|字|骈雅|通俗编|韵|雅俗|名义考|异名|绀珠|谐声", "Philological and lexicographical work"),
    (r"小说", "Collection of tales"),
    (r"集|词|稿|纂|遗书|奏档", "Literary collection"),
    (r"谱", "Practical manual"),
    (r"志", "Gazetteer"),
    (r"录", "Miscellaneous records"),
]
DYN_EN = {"明": "Ming", "清": "Qing", "宋": "Song", "元": "Yuan", "唐": "Tang",
          "金": "Jin", "辽": "Liao", "汉": "Han", "先秦": "pre-Qin", "民国": "Republican-era"}

# ── C. 缺失译文（按 节点名 + 原文前8字 匹配）──────────────────────
TRS = {
    ("《频罗庵遗集》", "俗有笋头卯眼之语"): "民间常说“笋头卯眼”，古代则有“露卯”“阴卯”的说法；“卯”俗音同“谋”。",
    ("《频罗庵遗集》", "程子语录榫卯圆则"): "《程子语录》说“榫卯圆则圆、榫卯方则方”云云——“榫”字本非古字。",
    ("《事物异名录》", "柄凿丹铅录伊川语"): "《丹铅总录》引伊川语录：所谓“枘凿”，就是榫卯；卯做成圆的（榫也随之为圆）。",
    ("《事物异名录》", "圆榫卯方则方，榫"): "榫卯圆便随之圆、方便随之方；“榫卯”二字应当写作“簨牡”。",
    ("《博山县乡土志》", "博山木工出手高强"): "博山的木工手艺高超，凡木器的卯榫工艺都很精良。",
    ("《博山县乡土志》", "博山油漆既有此特"): "博山的油漆既有这样的特色，加之木工手艺高超，凡木器的卯榫（都做得十分精良）。",
    ("《名义考》", "伊川语录云枘凿者"): "伊川语录说：“枘凿”就是榫卯。杨慎（字用修）认为“榫卯”应当写作“簨牡”。",
    ("《治政集要》", "做工程遇需用榫眼"): "凡施工中需要用到榫眼的地方，必须写明榫眼的数量与做法。",
    ("《增定雅俗稽言》", "善古称禅卯伊川语"): "古时称“榫卯”，伊川语录说“枘凿”就是榫卯；《金史》记张中孚制作（器物）云云（原文有讹字）。",
    ("《庄子通义》", "矩方规圆，枘凿之"): "矩画方、规画圆，所谓“枘凿”之论，都是说其情状并不固定于形体。",
    ("《洹词》", "铭曰：洁行而刚，"): "铭文说：品行高洁而刚正，文辞精工而有华彩；纵然如方枘圆凿般与世不合，以义度之又有何妨；精者粗者一并衡量；归隐水南，乐在其中。",
    ("《道宗六书》", "矩方规圆，枘凿之"): "矩画方、规画圆，所谓“枘凿”之论，都是说其情状并不固定于形体。",
    ("《国朝文纂》", "枘凿戾只，揆义奚"): "纵然像方枘圆凿般与世相违，只要以道义来衡量，又有什么妨碍。",
    ("《骈雅》", "榫卯、簨牡，枘凿"): "“榫卯”“簨牡”，就是枘凿；“铫鋧”是小凿；“剞劂”是曲刀。",
    ("《字触补》", "斫工问榫卯字，刘"): "木工请教“榫卯”二字的写法，刘大参以“木”旁加“卯”作答，座上客人指着“柳”字哄堂大笑。",
    ("《康济谱》", "发药盖好，将砲凑"): "装好火药并盖好，把炮口对准槽眼，将药线引入槽内。",
    ("《七修续稿》", "斫工问榫撞夘字，"): "木工请教“榫”“卯”二字，《海篇直音》注释说：削木插入孔窍叫做“准”。",
    ("《国宪家猷》", "尝闻吴人刘大参素"): "曾听说吴地的刘大参一向号称博学，有木工向他请教“榫”“卯”二字（如何书写）。",
    ("《说文闽音通》", "按闽语亦有榫头卯"): "按：闽语中也有“榫头”“卯眼”的说法，又有“接笋”“深卯”之语。",
    ("《说文闽音通》", "有笋头卯眼之语，"): "有“笋头卯眼”的说法；引程子语录“榫卯圆则圆、榫卯方则方”——“榫”“卯”都不是古字。",
    ("《嵩年奏档》", "致卯榫脱落情形较"): "（建筑构件）以致卯榫脱落、情况较重，拟奏请揭瓦查修。",
    ("《莫氏四种》", "古书恒有耜相、榫"): "古书中常有“耜相”“榫椎”这类词，本是截然不同的两物，音义各自完足，只是相互间有所脱漏。",
    ("《事物绀珠》", "(音宵以钉著物)翣"): "（字书注音释义：）“榫卯”，音同“笋”，是木匠接合构件所用之名。",
    ("《发微历眼通书大全》", "乙亥、丙子、戊子"): "择乙亥、丙子、戊子、庚子、己亥、辛亥、己卯等吉日开工，凿开柱眼。",
    ("《永觉和尚禅余内集》", "若本分举扬，必与"): "如果按本分直截宣说，必定与诸位方枘圆凿、格格不入。",
    ("《老子通义》", "矩方规圆，枘凿之"): "矩画方、规画圆，所谓“枘凿”之论，都是说其情状并不固定于形体。",
    ("《字学指南》", "榫卯(音笋茂程易"): "（字书注：）“榫卯”音“笋卯”（见程氏《易传》）；“簨”字从竹，取榫入凿窍、象“卯”之形。",
    ("《遂初堂集》", "石之方，行不渝，"): "石是方的，品行坚定不移；眼是圆的，智慧绰绰有余。可以使用，可以收藏；剖出灵巧的卯眼，雕琢出蟾蜍之形。",
    ("《五朝小说》", "隐客穿凿之志不辍"): "隐客开凿的志向始终不减。过了两年零一个多月，工人忽然听到地下传来鸡犬鸟雀之声，再凿数尺，旁边通到一处石穴。",
}
# 直接删除的垃圾摘录（节点名, 原文前缀）
DROP = {("《名义考》", "榫卯(历)")}


def norm(s: str) -> str:
    return re.sub(r"[\s，。、；：“”‘’\"'()（）\[\]【】·…—-]", "", s or "")


def main():
    text = DATA.read_text(encoding="utf-8")
    m = re.search(r"(window\.GRAPH_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.S)
    data = json.loads(m.group(2))
    nodes = data["nodes"]

    # 朝代邻接（书 -> 朝代名）
    by_id = {n["id"]: n for n in nodes}
    dyn_of = {}
    for l in data["links"]:
        s, t = l["source"], l["target"]
        for a, b in ((s, t), (t, s)):
            na, nb = by_id.get(a), by_id.get(b)
            if na and nb and na.get("type") == "literature" and nb.get("type") == "dynasty":
                dyn_of.setdefault(a, nb["name"])

    fixed_m = fixed_b = fixed_q = dropped = 0
    for n in nodes:
        # A. 榫卯
        if n.get("type") == "mortise" and n["name"] in MORTISE:
            cn, en = MORTISE[n["name"]]
            gloss = (n.get("enDesc") or "").strip()
            n["desc"] = cn.split("，")[0] + "。" if len(cn) > 40 else cn
            n["detail"] = cn
            n["enDetail"] = en
            if gloss:
                n["enDesc"] = gloss  # 保留原短释义作为简介
            fixed_m += 1
        # B. 古籍英文简介
        if n.get("type") == "literature":
            ed = (n.get("enDesc") or "").strip()
            eD = (n.get("enDetail") or "").strip()
            if ed == eD and "Historical text on timber joinery" in ed:
                genre = "Historical text"
                for pat, g in GENRES:
                    if re.search(pat, n["name"]):
                        genre = g
                        break
                dyn = DYN_EN.get(dyn_of.get(n["id"], ""), "")
                period = (" of the %s period" % dyn) if dyn else ""
                qn = len(n.get("quotes") or [])
                n["enDesc"] = genre + period + "."
                if qn:
                    n["enDetail"] = ("%s%s. Its text preserves period usage of mortise-and-tenon (sunmao) "
                                     "terminology; see the excerpt%s below.") % (genre, period, "s" if qn > 1 else "")
                else:
                    n["enDetail"] = ("%s%s, cited in historical sources for its mention of "
                                     "mortise-and-tenon (sunmao) joinery.") % (genre, period)
                fixed_b += 1
        # C. 摘录：黑名单 → 去重 → 补译文
        qs = n.get("quotes") or []
        if qs:
            out, seen = [], []
            for q in qs:
                cn = (q.get("cn") or "").strip()
                if not cn or len(norm(cn)) < 6:
                    dropped += 1
                    continue
                if any(n["name"] == d[0] and cn.startswith(d[1]) for d in DROP):
                    dropped += 1
                    continue
                nc = norm(cn)
                if any(nc == s or nc in s or s in nc for s in seen):
                    dropped += 1
                    continue
                seen.append(nc)
                if not (q.get("tr") or "").strip():
                    for (bn, pref), tr in TRS.items():
                        if bn == n["name"] and cn.startswith(pref):
                            q["tr"] = tr
                            fixed_q += 1
                            break
                out.append(q)
            n["quotes"] = out

    print("mortise fixed:", fixed_m, "| books fixed:", fixed_b,
          "| translations added:", fixed_q, "| quotes dropped:", dropped)
    # 校验：不再有缺译文
    miss = [(n["name"], q["cn"][:20]) for n in nodes for q in (n.get("quotes") or []) if not (q.get("tr") or "").strip()]
    print("still missing tr:", len(miss))
    for x in miss:
        print("  ", x)
    DATA.write_text(text[: m.start()] + m.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
