# -*- coding: utf-8 -*-
"""Patch knowledge-graph visuals + merge curated nodes with careful English."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"d:\xwechat_files\wxid_mrim2zak1zta12_50f6\msg\file\2026-08\知识图谱")
HTML = ROOT / "index.html"
DATA = ROOT / "data" / "sunmao-graph.source.js"
KG = Path(r"D:\D盘桌面\榫卯\code\extracted\knowledge_graph.json")

html = HTML.read_text(encoding="utf-8")

# ─── 1) Replace buildBackgroundStars + buildBackgroundNets ───
new_bg = r'''
    function buildBackgroundStars() {
      if (!scene) return;
      var count = 520, R = 360;
      var pos = new Float32Array(count * 3);
      var sizes = new Float32Array(count);
      var twinkleData = [];
      for (var i = 0; i < count; i++) {
        var rr = R * (0.15 + Math.random() * 0.85);
        var u = Math.random() * 2 - 1, a = Math.random() * Math.PI * 2;
        var s = Math.sqrt(1 - u * u);
        pos[i*3]   = rr * s * Math.cos(a);
        pos[i*3+1] = rr * u;
        pos[i*3+2] = rr * s * Math.sin(a);
        var sz = 0.9 + Math.random() * 2.4;
        sizes[i] = sz;
        twinkleData.push({
          group: Math.floor(Math.random() * 6),
          speed: 0.2 + Math.random() * 1.0,
          phase: Math.random() * Math.PI * 2,
          size: sz
        });
      }
      var geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      geo.setAttribute("size", new THREE.BufferAttribute(sizes, 1));
      var glowTex = (function(){
        var c = document.createElement("canvas"); c.width = c.height = 64;
        var ctx = c.getContext("2d");
        var g = ctx.createRadialGradient(32,32,0,32,32,32);
        g.addColorStop(0,"rgba(255,255,255,1)");
        g.addColorStop(0.15,"rgba(255,255,255,0.85)");
        g.addColorStop(0.4,"rgba(255,255,255,0.35)");
        g.addColorStop(1,"rgba(255,255,255,0)");
        ctx.fillStyle = g; ctx.fillRect(0,0,64,64);
        return new THREE.CanvasTexture(c);
      })();
      var mat = new THREE.PointsMaterial({
        map: glowTex, size: 2.2, sizeAttenuation: true,
        color: 0xffffff, transparent: true, opacity: 0.8,
        blending: THREE.AdditiveBlending, depthWrite: false
      });
      var pts = new THREE.Points(geo, mat);
      pts.renderOrder = -20; pts.raycast = function(){};
      bgStarData = twinkleData; bgStars = pts;
      scene.add(pts);
    }

    function buildBackgroundNets() {
      if (!scene) return;
      /* tech-blog live constellation: denser points, short links, connect/disconnect */
      var particleCount = 110, R = 240;
      var maxLinkDist = 72;
      var maxLinksPerFrame = 160;
      var particles = [];
      for (var i = 0; i < particleCount; i++) {
        var rr = R * (0.1 + Math.random() * 0.9);
        var u = Math.random() * 2 - 1, a = Math.random() * Math.PI * 2;
        var s = Math.sqrt(1 - u * u);
        particles.push({
          x: rr * s * Math.cos(a), y: rr * u, z: rr * s * Math.sin(a),
          vx: (Math.random()-0.5)*0.28, vy: (Math.random()-0.5)*0.28, vz: (Math.random()-0.5)*0.28,
          phase: Math.random()*Math.PI*2
        });
      }
      var posArr = new Float32Array(particleCount * 3);
      for (var pi = 0; pi < particleCount; pi++) {
        posArr[pi*3]=particles[pi].x; posArr[pi*3+1]=particles[pi].y; posArr[pi*3+2]=particles[pi].z;
      }
      var ptsGeo = new THREE.BufferGeometry();
      ptsGeo.setAttribute("position", new THREE.BufferAttribute(posArr, 3));
      var ptsMat = new THREE.PointsMaterial({
        color: 0x8FD8E2, size: 2.1, sizeAttenuation: true,
        transparent: true, opacity: 0.62,
        blending: THREE.AdditiveBlending, depthWrite: false
      });
      var ptsObj = new THREE.Points(ptsGeo, ptsMat);
      ptsObj.renderOrder = -18; ptsObj.raycast = function(){};

      var linkPos = new Float32Array(maxLinksPerFrame * 6);
      var linkCol = new Float32Array(maxLinksPerFrame * 6);
      var linkGeo = new THREE.BufferGeometry();
      linkGeo.setAttribute("position", new THREE.BufferAttribute(linkPos, 3));
      linkGeo.setAttribute("color", new THREE.BufferAttribute(linkCol, 3));
      linkGeo.setDrawRange(0, 0);
      var linkMat = new THREE.LineBasicMaterial({
        vertexColors: true, transparent: true, opacity: 0.65,
        blending: THREE.AdditiveBlending, depthWrite: false
      });
      var lineObj = new THREE.LineSegments(linkGeo, linkMat);
      lineObj.renderOrder = -19; lineObj.raycast = function(){};

      bgNetData = {
        mode: "live", particles: particles, maxLinkDist: maxLinkDist, maxLinks: maxLinksPerFrame,
        pts: ptsObj, links: lineObj, linkPos: linkPos, linkCol: linkCol, active: {}, R: R
      };
      bgNets = lineObj;
      scene.add(ptsObj);
      scene.add(lineObj);
    }
'''

html = re.sub(
    r"    function buildBackgroundStars\(\) \{.*?\n    function getDepthAttenuation",
    new_bg + "\n    function getDepthAttenuation",
    html,
    count=1,
    flags=re.S,
)

# Remove leftover fog + min constants that got duplicated - check
# Actually my regex replaced from buildBackgroundStars through just before getDepthAttenuation,
# which may have removed updateSceneFog and NODE_MIN_* constants. Need to restore them.

if "function updateSceneFog" not in html:
    insert = '''
    function updateSceneFog() {
      if (!scene) return;
      var near = 400 - forceDepth * 330;
      var far  = 800 - forceDepth * 480;
      if (!scene.fog) {
        scene.fog = new THREE.Fog(new THREE.Color(0x0a0806), near, far);
      } else {
        scene.fog.near = near;
        scene.fog.far = far;
      }
    }

    var NODE_MIN_ATTEN = 0.42;
    var NODE_MIN_OPACITY = 0.40;
    var NODE_MIN_EMISSIVE = 0.30;
    var NODE_MIN_HALO = 0.18;
    var LINK_MIN_OPACITY = 0.16;
    var LABEL_MIN_OPACITY = 0.22;

'''
    html = html.replace(
        "    function getDepthAttenuation",
        insert + "    function getDepthAttenuation",
        1,
    )

# ─── 2) projectLabels: follow node opacity + stronger near-far with depth ───
old_label = """        /* v8 节点标签透明度跟随节点几何体透明度（距离衰减） */
        var atten = getDepthAttenuation(n.x||0, n.y||0, n.z||0, _camPos);
        var hlOp = (!any || highlightNodes[n.id]) ? 1 : 0.35;
        el.style.opacity = Math.max(LABEL_MIN_OPACITY, hlOp * atten);
        /* v9 近大远小：深度影响字号 + 焦点节点 1.3× 放大 */
        var depthScale = 0.6 + 0.4 * atten;
        var isFocused = (n.id === _focusedNodeId);
        var sizeBoost = isFocused ? 1.3 : 1.0;
        var zhSize = Math.round(forceLabelSize * depthScale * sizeBoost);
        var enSize = Math.round(forceLabelSize * 0.7 * depthScale * sizeBoost);
        var zhEl = el.querySelector(".nl-zh");
        var enEl = el.querySelector(".nl-en");
        if (zhEl) zhEl.style.fontSize = zhSize + "px";
        if (enEl) enEl.style.fontSize = enSize + "px";
        /* v10 着色明度：标签颜色向白色混合 */
        if (forceColorLight > 0.001 && n.__baseColor) {
          var bc = n.__baseColor;
          var r = Math.round(bc.r * 255), g = Math.round(bc.g * 255), b = Math.round(bc.b * 255);
          var lr = Math.round(r + (255 - r) * forceColorLight);
          var lg = Math.round(g + (255 - g) * forceColorLight);
          var lb = Math.round(b + (255 - b) * forceColorLight);
          el.style.color = "rgb(" + lr + "," + lg + "," + lb + ")";
        }"""

new_label = """        /* 标签跟随节点明度/透明度；近大远小随立体度增强 */
        var atten = getDepthAttenuation(n.x||0, n.y||0, n.z||0, _camPos);
        var matOp = (n.__mat && typeof n.__mat.opacity === "number") ? n.__mat.opacity : atten;
        var hlOp = (!any || highlightNodes[n.id]) ? 1 : 0.38;
        var nearFar = (forceDepth < 0.01) ? 1 : Math.pow(atten, 0.55 + forceDepth * 0.9);
        el.style.opacity = Math.max(LABEL_MIN_OPACITY, matOp * hlOp * (0.55 + 0.45 * nearFar));
        var depthScale = (1 - forceDepth) * 1.0 + forceDepth * (0.38 + 0.62 * nearFar);
        var isFocused = (n.id === _focusedNodeId);
        var sizeBoost = isFocused ? 1.28 : 1.0;
        var zhSize = Math.max(8, Math.round(forceLabelSize * depthScale * sizeBoost));
        var enSize = Math.max(7, Math.round(forceLabelSize * 0.7 * depthScale * sizeBoost));
        var zhEl = el.querySelector(".nl-zh");
        var enEl = el.querySelector(".nl-en");
        if (zhEl) zhEl.style.fontSize = zhSize + "px";
        if (enEl) enEl.style.fontSize = enSize + "px";
        if (n.__baseColor) {
          var bc = n.__baseColor;
          var lift = Math.max(0, forceColorLight || 0);
          var r = Math.round((bc.r + (1-bc.r)*lift) * 255);
          var g = Math.round((bc.g + (1-bc.g)*lift) * 255);
          var b = Math.round((bc.b + (1-bc.b)*lift) * 255);
          el.style.color = "rgb(" + r + "," + g + "," + b + ")";
          el.style.opacity = Math.max(LABEL_MIN_OPACITY, parseFloat(el.style.opacity) * (0.75 + 0.25 * matOp));
        }"""

if old_label in html:
    html = html.replace(old_label, new_label)
else:
    print("WARN: label block not found exact")

# ─── 3) Replace animate bg net + float section ───
old_anim_net = """      // ─── v9 背景粒子网：低调漂移，不喧宾夺主 ───
      if (bgNets && bgNetData) {
        var nd = bgNetData;
        // 锚点漂移：以 base 坐标为中心做小幅度摆动
        for (var ai = 0; ai < nd.anchors.length; ai++) {
          var anch = nd.anchors[ai];
          anch.x = anch.bx + anch.drift[0] * Math.sin(t * 0.25 + ai);
          anch.y = anch.by + anch.drift[1] * Math.cos(t * 0.22 + ai + 1);
          anch.z = anch.bz + anch.drift[2] * Math.sin(t * 0.28 + ai + 2);
        }
        // 更新 sprite 位置
        for (var si = 0; si < nd.sprites.length; si++) {
          var a = nd.anchors[si];
          nd.sprites[si].position.set(a.x, a.y, a.z);
        }
        // 更新连线顶点
        var netPos = bgNets.geometry.attributes.position.array;
        for (var ni = 0; ni < nd.netData.length; ni++) {
          var nni = nd.netData[ni];
          var pa = nd.anchors[nni.i1], pb = nd.anchors[nni.i2];
          netPos[ni*6]   = pa.x; netPos[ni*6+1] = pa.y; netPos[ni*6+2] = pa.z;
          netPos[ni*6+3] = pb.x; netPos[ni*6+4] = pb.y; netPos[ni*6+5] = pb.z;
        }
        bgNets.geometry.attributes.position.needsUpdate = true;
        var netPulse = 0.16 + 0.08 * Math.sin(t * 0.35) + 0.05 * Math.sin(t * 0.65 + 2);
        bgNets.material.opacity = netPulse * (1 - forceDepth * 0.30);
        // 光晕 sprite 脉冲（低调）
        for (var si2 = 0; si2 < nd.sprites.length; si2++) {
          var spOp = 0.32 + 0.12 * Math.sin(t * 0.4 + si2 * 0.7);
          nd.sprites[si2].material.opacity = spOp * (1 - forceDepth * 0.20);
        }
      }"""

new_anim_net = """      // ─── 实时星座网：短距连断 + 粒子漂移 ───
      if (bgNetData && bgNetData.mode === "live") {
        var nd = bgNetData;
        var Rbound = nd.R || 240;
        var pArr = nd.pts.geometry.attributes.position.array;
        for (var ai = 0; ai < nd.particles.length; ai++) {
          var p = nd.particles[ai];
          p.vx += Math.sin(t * 0.35 + p.phase) * 0.002;
          p.vy += Math.cos(t * 0.31 + p.phase * 1.3) * 0.002;
          p.vz += Math.sin(t * 0.27 + p.phase * 0.7) * 0.002;
          p.vx *= 0.986; p.vy *= 0.986; p.vz *= 0.986;
          p.x += p.vx; p.y += p.vy; p.z += p.vz;
          var dd = Math.sqrt(p.x*p.x + p.y*p.y + p.z*p.z) || 1;
          if (dd > Rbound) {
            p.x *= Rbound / dd; p.y *= Rbound / dd; p.z *= Rbound / dd;
            p.vx *= -0.4; p.vy *= -0.4; p.vz *= -0.4;
          }
          pArr[ai*3] = p.x; pArr[ai*3+1] = p.y; pArr[ai*3+2] = p.z;
        }
        nd.pts.geometry.attributes.position.needsUpdate = true;
        nd.pts.material.opacity = (0.45 + 0.12 * Math.sin(t * 0.5)) * (1 - forceDepth * 0.15);

        var candidates = [];
        var maxD = nd.maxLinkDist;
        var maxD2 = maxD * maxD;
        for (var i1 = 0; i1 < nd.particles.length; i1++) {
          for (var i2 = i1 + 1; i2 < nd.particles.length; i2++) {
            var a = nd.particles[i1], b = nd.particles[i2];
            var dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
            var d2 = dx*dx + dy*dy + dz*dz;
            if (d2 < maxD2) candidates.push({i1:i1, i2:i2, d2:d2});
          }
        }
        candidates.sort(function(u,v){ return u.d2 - v.d2; });
        var keep = Math.min(nd.maxLinks, candidates.length);
        var nextActive = {};
        var lp = nd.linkPos, lc = nd.linkCol;
        var drawn = 0;
        for (var ci = 0; ci < keep; ci++) {
          var cnd = candidates[ci];
          var key = cnd.i1 + "_" + cnd.i2;
          var life = nd.active[key] != null ? Math.min(1, nd.active[key] + dt * 2.2) : 0.15;
          nextActive[key] = life;
          var pa = nd.particles[cnd.i1], pb = nd.particles[cnd.i2];
          var distN = 1 - Math.sqrt(cnd.d2) / maxD;
          var alpha = life * (0.18 + 0.72 * distN);
          var o = drawn * 6;
          lp[o]=pa.x; lp[o+1]=pa.y; lp[o+2]=pa.z;
          lp[o+3]=pb.x; lp[o+4]=pb.y; lp[o+5]=pb.z;
          var cr = 0.45 + 0.35 * distN, cg = 0.75 + 0.15 * distN, cb = 0.82;
          lc[o]=cr; lc[o+1]=cg; lc[o+2]=cb;
          lc[o+3]=cr; lc[o+4]=cg; lc[o+5]=cb;
          // bake alpha into color brightness
          lc[o]*=alpha; lc[o+1]*=alpha; lc[o+2]*=alpha;
          lc[o+3]*=alpha; lc[o+4]*=alpha; lc[o+5]*=alpha;
          drawn++;
        }
        // fade out recently lost links briefly by not keeping them
        nd.active = nextActive;
        nd.links.geometry.setDrawRange(0, drawn * 2);
        nd.links.geometry.attributes.position.needsUpdate = true;
        nd.links.geometry.attributes.color.needsUpdate = true;
        nd.links.material.opacity = 0.85 * (1 - forceDepth * 0.2);
      }"""

if old_anim_net in html:
    html = html.replace(old_anim_net, new_anim_net)
else:
    print("WARN: anim net block not found")

old_float = """      // ─── 节点呼吸/悬浮 + 立体度衰减 ───
      var gNodes = Graph.graphData().nodes || [];
      var floatAmp = 0.7;
      for (var ni=0; ni<gNodes.length; ni++){
        var n = gNodes[ni]; var m = n.__mesh; if(!m) continue;
        var ph = n.__phase || 0;
        var hl = !!highlightNodes[n.id];
        var breath = 1 + 0.07*Math.sin(t*1.2 + ph);
        m.scale.setScalar(n.__baseScale * breath * (hl ? 1.12 : 1));
        m.position.y = Math.sin(t*0.9 + ph) * floatAmp;
        m.rotation.y = t*0.15 + ph;"""

new_float = """      // ─── Obsidian 风格自然浮动 + 立体度衰减 ───
      var gNodes = Graph.graphData().nodes || [];
      for (var ni=0; ni<gNodes.length; ni++){
        var n = gNodes[ni]; var m = n.__mesh; if(!m) continue;
        var ph = n.__phase || 0;
        var hl = !!highlightNodes[n.id];
        var breath = 1 + 0.045*Math.sin(t*0.85 + ph) + 0.025*Math.sin(t*1.35 + ph*1.7);
        m.scale.setScalar(n.__baseScale * breath * (hl ? 1.1 : 1));
        /* 三轴有机漂移（局部坐标，不打乱力导向） */
        var fx = Math.sin(t*0.42 + ph) * 1.35 + Math.sin(t*0.91 + ph*1.4) * 0.55;
        var fy = Math.sin(t*0.55 + ph*1.1) * 1.6 + Math.cos(t*0.73 + ph) * 0.45;
        var fz = Math.cos(t*0.38 + ph*0.8) * 1.2 + Math.sin(t*0.67 + ph*1.6) * 0.5;
        m.position.set(fx, fy, fz);
        m.rotation.y = t*0.08 + ph;
        m.rotation.x = Math.sin(t*0.2 + ph) * 0.08;
        /* 轻微布朗力：让整图像 Obsidian 一样持续微动 */
        n.vx = (n.vx || 0) + Math.sin(t*0.3 + ph) * 0.004;
        n.vy = (n.vy || 0) + Math.cos(t*0.27 + ph*1.2) * 0.004;
        n.vz = (n.vz || 0) + Math.sin(t*0.23 + ph*0.6) * 0.004;"""

if old_float in html:
    html = html.replace(old_float, new_float)
else:
    print("WARN: float block not found")

HTML.write_text(html, encoding="utf-8")
print("HTML patched. has live net:", 'mode: "live"' in html or "mode: \"live\"" in html)
print("has updateSceneFog", "function updateSceneFog" in html)
print("has NODE_MIN", "NODE_MIN_ATTEN" in html)

# ─── 4) Merge graph data + English ───
src = DATA.read_text(encoding="utf-8")
m = re.search(r"window\.GRAPH_DATA\s*=\s*(\{.*\})\s*;?\s*$", src, re.S)
data = json.loads(m.group(1))
by_id = {n["id"]: n for n in data["nodes"]}
existing_names = {n["name"] for n in data["nodes"]}

# Careful English refresh for existing cards
EN = {
    "hemudu": {
        "en": "Hemudu Culture",
        "enDesc": "About 7,000 years ago, early mortise-and-tenon forms appear in stilt-house timber remains.",
        "enDetail": "At the Hemudu site in Zhejiang (c. 7,000 BP), stilt-house timbers preserve ridges, grooves, dovetail-like ends and tongue-and-groove boards—the earliest known prototypes of Chinese joinery, showing that 'tenon over nail' reaches back to the late Neolithic.",
    },
    "chunqiu": {
        "en": "Spring and Autumn – Warring States",
        "enDesc": "Joinery types diversify; the Kaogongji records woodworking craft.",
        "enDetail": "In the Eastern Zhou period, mortise-tenon variety expands markedly. The Kaogongji documents carpentry practice, and finds such as framed chests from the Marquis Yi of Zeng tomb already use interlocking joinery without metal fasteners.",
    },
    "han": {
        "en": "Han Dynasty",
        "enDesc": "Post-and-lintel and column-and-tie systems take shape; dougong begins to mature.",
        "enDetail": "Han builders establish the two enduring timber frames—tailiang (post-and-lintel) and chuandou (column-and-tie). Bracket sets (dougong) gradually formalize, setting the grammar of later Chinese monumental wood architecture.",
    },
    "tang": {
        "en": "Tang Dynasty",
        "enDesc": "Dougong reaches a classical peak; Tang carpentry spreads to Japan via envoys.",
        "enDetail": "Tang timber architecture culminates in works such as Foguang Temple’s seven-puzuo brackets with deep eaves. Through kentōshi missions, this craft system enters Japan (e.g. Tōshōdai-ji), becoming a shared East Asian timber source.",
    },
    "song": {
        "en": "Song Dynasty",
        "enDesc": "Yingzao Fashi standardizes joinery; Yingxian Wooden Pagoda is completed.",
        "enDetail": "Li Jie’s Yingzao Fashi (1103) introduces the caifen modular system for prefabrication and regulation. The Yingxian Wooden Pagoda stands as a pure-timber landmark, while taller furniture extends joinery from buildings into daily objects.",
    },
    "yuan": {
        "en": "Yuan Dynasty",
        "enDesc": "Song systems continue with smaller, simplified dougong.",
        "enDetail": "Yuan practice largely continues Song framing while reducing dougong scale. Joinery tends toward clearer, more economical assemblies without abandoning the modular logic of earlier treatises.",
    },
    "ming": {
        "en": "Ming Dynasty",
        "enDesc": "Ming furniture’s golden age; Forbidden City and Temple of Heaven rise.",
        "enDetail": "Ming hard-wood furniture develops more than a hundred joinery patterns centered on interlocking tenons. Monumental works such as the Forbidden City and the Hall of Prayer for Good Harvests push architectural joinery to an apex.",
    },
    "qing": {
        "en": "Qing Dynasty",
        "enDesc": "Gongcheng Zuofa Zeli sets the doukou module; furniture joinery grows ornate.",
        "enDetail": "The Qing Engineering Manual shifts the module to doukou while extending Song logic. Furniture joinery becomes more elaborate—bao-jian, zong-jiao, running pins—balancing structure with carved ornament.",
    },
    "modern": {
        "en": "Contemporary",
        "enDesc": "Expo ‘Oriental Crown’, lunar tenon bricks, space nodes, and BIM revive joinery.",
        "enDetail": "Contemporary practice remaps tradition: the 2010 Shanghai Expo China Pavilion riffs on dougong; labs explore lunar-regolith tenon bricks and deployable space-habitat joints; BIM and parametric tools return classical nodes to design workflows.",
    },
    "yanwei": {
        "en": "Dovetail Joint",
        "enDesc": "Trapezoidal tenon that tightens under tension—classic for right-angle panel joins.",
        "enDetail": "Named for its swallow-tail profile, the dovetail locks two boards at a right angle. Under tension it self-wedges, resisting pull-out—hence its use in drawers, chests and panel assemblies. Ming–Qing furniture often pairs it with dragon-phoenix edge joins for large thin tops.",
    },
    "xieding": {
        "en": "Wedged Key Tenon",
        "enDesc": "Curved-member joint locked by a transverse wedge pin—common on round-back chairs.",
        "enDetail": "Used to join curved rails (chair arms, round table rims): two scarfed tenons interlock, then a wedge pin drives through to stop vertical slip. The pin replaces glue, allowing both longevity and controlled disassembly.",
    },
    "gejian": {
        "en": "Shouldered Miter Tenon",
        "enDesc": "45° shouldered joint for T- and corner frame meetings.",
        "enDetail": "A fundamental framing joint: shoulders are cut to 45° so members meet cleanly at corners or T-junctions, hiding end grain and enlarging the glue/contact face. Variants include large and small gejian, typical of chair and table frames.",
    },
    "jiatou": {
        "en": "Clamp-Head Joint",
        "enDesc": "Table-leg joint that forks to clamp the apron and carry the top load.",
        "enDetail": "Signature of recessed-leg tables: the upper leg is kerfed to clamp the apron (and often apron heads), spreading the top’s weight into four legs. Open, readable structure and efficient load path define the case-form typology.",
    },
    "baojian": {
        "en": "Embracing-Shoulder Joint",
        "enDesc": "Three-way joint of leg, waist molding and apron in waisted furniture.",
        "enDetail": "In waisted Ming furniture the leg, waist and apron meet with a 45° shoulder and triangular tongue. The assembly hides fasteners and stabilizes the corner—one of the craft’s most intricate signatures.",
    },
    "zongjiao": {
        "en": "Zongjiao Three-Way Miter",
        "enDesc": "Three-member corner forming six 45° miters like a zong dumpling tip.",
        "enDetail": "Used on flush three-sided pieces (stools, stands): three members meet with six 45° miters, reading as a crisp ‘zong’ tip. Dimensional accuracy is unforgiving because three axes converge at one point.",
    },
    "changduan": {
        "en": "Stepped Twin Tenon",
        "enDesc": "Two tenons of unequal height for a staggered, stronger leg-to-top join.",
        "enDetail": "Two tenons of different heights enter separate mortises so cuts do not weaken one section twice. Often a sub-component inside clamp-head or embracing-shoulder assemblies.",
    },
    "chajian": {
        "en": "Inserted-Shoulder Joint",
        "enDesc": "Sloped shoulder of the leg slides into a front groove of the apron.",
        "enDetail": "Related to the clamp-head joint but emphasizing insertion: a beveled shoulder on the leg face enters an apron slot, yielding a leaner look. Where clamp-head ‘grips,’ inserted-shoulder ‘slides in.’",
    },
    "bawang": {
        "en": "Overlord Stretcher",
        "enDesc": "S-curve floating stretcher that braces legs without side rails.",
        "enDetail": "An S-shaped brace meets a top batten above and hooks the inner leg below, stiffening the frame without low stretchers—freeing knee space. Its vigorous curve inspired the ‘overlord’ name.",
    },
    "longfeng": {
        "en": "Dragon-Phoenix Edge Joint",
        "enDesc": "Tongue-and-groove board join that stops lateral shift.",
        "enDetail": "Edge joining for large panels: one board forms a tongue (‘dragon’), the other a groove (‘phoenix’). Once seated, boards cannot slide sideways—standard for tabletops and cabinet doors.",
    },
    "zouma": {
        "en": "Running Latch Pin",
        "enDesc": "Sliding wooden pin that locks a joint yet allows controlled release.",
        "enDetail": "A tapered wooden latch slides into matching seats to lock members, then can be withdrawn for knockdown packing—valued in Qing furniture for travel and maintenance.",
    },
    "tao": {
        "en": "Through-Shoulder Frame Joint",
        "enDesc": "Frame joinery family for rails and stiles in furniture carcasses.",
        "enDetail": "A family of frame joints that seat rails into stiles with shoulders, forming the rectangular skeleton of cabinets and screens. Often combined with through or blind tenons for strength and finish.",
    },
    "chuandai": {
        "en": "Cleat / Transverse Batten Tenon",
        "enDesc": "Cross batten tenoned into a panel to resist cupping.",
        "enDetail": "A transverse cleat enters the underside of a wide board with sliding or fixed tenons, restraining warp while allowing seasonal movement—essential under tabletops and doors.",
    },
    "qikou": {
        "en": "Tongue-and-Groove (Qikou)",
        "enDesc": "Matched tongue and groove for flush panel seams.",
        "enDetail": "One edge carries a tongue, the mating edge a groove. The seam stays flush and weather-tight, widely used for flooring and paneling as well as furniture skins.",
    },
    "zhi": {
        "en": "Straight Tenon",
        "enDesc": "Rectangular tenon—the basic prismatic mortise-and-tenon.",
        "enDetail": "The elemental rectangular tenon. Most specialized Chinese joints derive from adjusting its length, shoulders, wedges or penetrations.",
    },
    "ban": {
        "en": "Blind Tenon",
        "enDesc": "Tenon that stops short of the far face—no through reveal.",
        "enDetail": "The tenon is shorter than the member thickness, so it does not emerge opposite. Cleaner faces, slightly less strength than a through tenon—common where appearance matters.",
    },
    "tong": {
        "en": "Through Tenon",
        "enDesc": "Tenon that passes fully through the mortised member.",
        "enDetail": "The tenon exits the far face and may be wedged or pegged. Stronger and more honest structurally; often paired with blind tenons in the same frame for hierarchy of faces.",
    },
    "dougong": {
        "en": "Dougong Bracket Set",
        "enDesc": "Layered interlocking blocks and arms transferring roof loads to columns.",
        "enDetail": "China’s iconic bracket clusters: stacked dou blocks and gong arms cantilever eaves and dissipate loads. Rank, module and seismic resilience intertwine; palace and temple carpentry depend on it.",
    },
    "north": {
        "en": "Northern Official Style",
        "enDesc": "Official timber idiom of the north—palace, temple and state craft.",
        "enDetail": "Centered on Beijing–Shanxi–Hebei official carpentry: raised-beam frames, regulated dougong, and court manuals. Joinery favors clarity of hierarchy and modular control.",
    },
    "jiangnan": {
        "en": "Jiangnan Region",
        "enDesc": "Southern water-town and garden timber culture of Jiangsu–Zhejiang–Anhui.",
        "enDetail": "Gardens, academies and merchant houses refine lighter frames, intricate interiors and humid-climate detailing. Chuandou logic and fine furniture joinery thrive here.",
    },
    "lingnan": {
        "en": "Lingnan Region",
        "enDesc": "Lingnan timber and mixed masonry-wood traditions of the far south.",
        "enDetail": "Guangdong–Guangxi–Fujian practices adapt to heat, rain and typhoon risk—deep eaves, ventilated frames and hybrid brick-timber compounds with distinctive local tenon vocabularies.",
    },
    "xinan": {
        "en": "Southwest Region",
        "enDesc": "Southwest mountain timber cultures of Sichuan–Yunnan–Guizhou.",
        "enDetail": "Stilt houses, covered bridges and ethnic minority frames emphasize chuandou flexibility and local hardwoods. Joinery answers steep terrain and seismic zones.",
    },
    "moju": {
        "en": "Modular Mensuration",
        "enDesc": "Caifen / doukou modules that scale every member and joint.",
        "enDetail": "Song caifen and Qing doukou systems size timber, brackets and tenons from a shared module—enabling prefabrication, rank control and repair interchangeability.",
    },
    "bangang": {
        "en": "Semi-Rigid Joint Behavior",
        "enDesc": "Timber joints dissipate energy through controlled slip and friction.",
        "enDetail": "Unlike rigid steel nodes, Chinese tenon joints allow micro-rotation and friction damping—key to seismic resilience celebrated as ‘softness overcoming hardness.’",
    },
    "shouli": {
        "en": "Load Path Logic",
        "enDesc": "How roofs, brackets and frames channel forces into the ground.",
        "enDetail": "Design intent is a continuous load path: tile → purlin → beam/bracket → column → foundation. Each tenon is sized for its place in that chain.",
    },
    "jingdu": {
        "en": "Precision Craft",
        "enDesc": "Ink-line layout, hand tooling and millimeter fit without metal fasteners.",
        "enDetail": "Craftsmen mark with ink lines, cut by chisel and saw, and chase fit until joints seat by friction alone. Precision is cultural as much as technical.",
    },
    "tailiangchuandou": {
        "en": "Tailiang & Chuandou Systems",
        "enDesc": "The twin structural grammars of Chinese timber architecture.",
        "enDetail": "Tailiang spans with beams on columns; chuandou ties columns with penetrating purlins. Most historic buildings hybridize the two according to span, region and rank.",
    },
    "japan": {
        "en": "Japan",
        "enDesc": "Tang-derived wooden architecture and refined kiwari proportioning.",
        "enDetail": "Japanese temple carpentry absorbed Tang dougong and later developed kiwari mensuration and intricate kumiki joinery—parallel yet distinct from Chinese lineages.",
    },
    "iseshrine": {
        "en": "Ise Shrine",
        "enDesc": "Cyclically rebuilt sanctuary embodying pure timber joinery ethos.",
        "enDetail": "Ise’s regular rebuilding (shikinen sengū) transmits tool skills and joint lore without nails—an extreme statement of timber renewal culture.",
    },
    "korea": {
        "en": "Korean Peninsula",
        "enDesc": "Palace and temple woodwork in dialogue with Chinese official styles.",
        "enDetail": "Korean court architecture adapts Chinese bracket language to local proportions and painting systems, visible in complexes such as Gyeongbokgung.",
    },
    "oumei": {
        "en": "Euro-American Log Construction",
        "enDesc": "Log / well-frame timber houses with corner notches—Western parallels to interlocking dry joins.",
        "enDetail": "Across Europe and North America, horizontally stacked log houses use corner notches akin to a well-curb (jinggan). Though distinct from Chinese tenon systems, the dry interlock at corners is a cognate solution for all-timber envelopes.",
    },
    "banmao": {
        "en": "Shigeru Ban",
        "enDesc": "Japanese architect Shigeru Ban, known for paper-tube and timber structures; Zurich Tamedia building uses large-scale interlocking wood joins.",
        "enDetail": "Shigeru Ban is known for sustainable paper-tube and timber architecture. At Zurich’s Tamedia office building, large timber members interlock with joinery-like connections—carrying load with lightness and echoing traditional tenon logic in contemporary green building.",
    },
    "kengoyama": {
        "en": "Kengo Kuma",
        "enDesc": "Japanese architect Kengo Kuma; CNC-precise joinery in works such as the Bamboo House at the Great Wall.",
        "enDetail": "Kengo Kuma advocates “anti-object” architecture of material humility. In works like the Bamboo House at the foot of the Great Wall, CNC-precise joints let steel and timber interlock with the grace of wood joinery, carrying East Asian node wisdom into contemporary materials.",
    },
    "yuerang": {
        "en": "Lunar-Regolith Tenon Brick",
        "enDesc": "Research into sinterable lunar soil units joined like tenons.",
        "enDetail": "Labs explore casting or sintering lunar regolith into interlocking ‘tenon bricks,’ translating ancient dry-join logic into extraterrestrial construction hypotheses.",
    },
    "taikong": {
        "en": "Space Habitat Joints",
        "enDesc": "Deployable cabin nodes inspired by interlocking timber logic.",
        "enDetail": "Aerospace concepts borrow foldable, interlocking nodes reminiscent of tenon geometry for compact launch and on-orbit expansion.",
    },
    "tailiang": {
        "en": "Post-and-Lintel (Tailiang)",
        "enDesc": "Beams stack on columns to span halls—core of northern official buildings.",
        "enDetail": "Columns carry transverse beams; layers rise to the roof. Suited to wide ceremonial bays and regulated dougong crowns in palaces and temples.",
    },
    "chuandou": {
        "en": "Column-and-Tie (Chuandou)",
        "enDesc": "Purlins penetrate columns forming a flexible tied frame.",
        "enDetail": "Common in the south and southwest: columns are tied by penetrating members, yielding lighter, more deformable frames for houses, bridges and hillsides.",
    },
    "jinggan": {
        "en": "Well-Frame / Log-Cabin Stack",
        "enDesc": "Horizontally stacked members notched at corners.",
        "enDetail": "Timbers stack like a well curb or log cabin, corner-notched. Compact and sturdy for granaries, frontier buildings and some towers.",
    },
    "gongdian": {
        "en": "Palace Architecture",
        "enDesc": "Highest-rank official timber compounds centered on axis and ritual.",
        "enDetail": "Palace carpentry concentrates the full official toolkit—modules, dougong ranks, painted beams—and the most exacting tenon discipline.",
    },
    "yuanlin": {
        "en": "Garden Architecture",
        "enDesc": "Pavilions, covered walks and scholar’s studios in landscaped settings.",
        "enDetail": "Garden structures favor lighter sections, scenic frames and refined furniture-scale joinery—especially in Jiangnan scholar gardens.",
    },
    "ta": {
        "en": "Pagoda / Tower Timberwork",
        "enDesc": "Multi-story wooden towers demanding stacked joinery precision.",
        "enDetail": "Pagodas accumulate floors of beams, brackets and stair joinery. Yingxian’s pure-wood tower remains an emblem of stacked tenon ambition.",
    },
    "yingzaofashi": {
        "en": "Yingzao Fashi",
        "enDesc": "1103 Song building code that modularized Chinese carpentry.",
        "enDetail": "Li Jie’s treatise defines the caifen module, member grades and joint practice—turning workshop lore into a state-readable standard still cited for Song–Yuan reconstruction.",
    },
    "gongcheng": {
        "en": "Qing Engineering Manual",
        "enDesc": "Qing official methods using the doukou module.",
        "enDetail": "Gongcheng Zuofa Zeli recalibrates official carpentry around doukou, documenting palace and temple practice for Qing courts and workshops.",
    },
    "tiangong": {
        "en": "Tiangong Kaiwu",
        "enDesc": "Ming encyclopedia of crafts including woodworking tools and methods.",
        "enDetail": "Song Yingxing’s mid-Ming compendium surveys technology; its woodworking passages illuminate tools, materials and popular craft beyond court manuals.",
    },
    "kaogong": {
        "en": "Kaogongji",
        "enDesc": "Early classic on state crafts, including woodworking norms.",
        "enDetail": "Part of the Zhou rites corpus, Kaogongji records artisan organization and technical ideals—an early textual horizon for Chinese making, including timber work.",
    },
    "mingshi": {
        "en": "Studies in Ming Furniture",
        "enDesc": "Modern scholarship decoding Ming furniture joinery.",
        "enDetail": "Foundational modern research (e.g. Wang Shixiang’s line) classifies Ming furniture joints, aesthetics and workshop logic for today’s historians and makers.",
    },
    "chuci": {
        "en": "Chu Ci — Square Peg, Round Hole",
        "enDesc": "Literary metaphor of mismatched tenon and mortise from Songs of Chu.",
        "enDetail": "The famous line on a square tenon and round mortise turns joinery into a figure of misfit politics—proof that tenon vocabulary entered classical literature early.",
    },
    "feiyi2006": {
        "en": "National ICH (2006)",
        "enDesc": "Traditional timber construction listed as national intangible heritage.",
        "enDetail": "In 2006, traditional Chinese timber construction techniques entered the national ICH list, framing joinery as living cultural practice, not only historic fabric.",
    },
    "feiyi2009": {
        "en": "UNESCO ICH (2009)",
        "enDesc": "UNESCO inscription of Chinese traditional timber craftsmanship.",
        "enDetail": "UNESCO’s 2009 listing recognizes Chinese traditional architectural timber craftsmanship globally, reinforcing transmission, education and conservation agendas.",
    },
}

for n in data["nodes"]:
    e = EN.get(n["id"])
    if not e:
        continue
    n["en"] = e["en"]
    n["enDesc"] = e["enDesc"]
    n["enDetail"] = e["enDetail"]

# Dynasty id map for edges
DYN_MAP = {
    "明": "ming",
    "清": "qing",
    "元": "yuan",
    "宋": "song",
    "金": "chunqiu",  # no Jin node — skip later
    "辽": "song",
    "唐": "tang",
    "汉": "han",
    "民国": "modern",
    "近现代": "modern",
    "北宋": "song",
    "南宋": "song",
}
# Better: don't map 金 to chunqiu. Skip unknown.
DYN_MAP.pop("金", None)

REGION_MAP = {
    "北方地区": "north",
    "南方地区": "jiangnan",
    "西北地区": "xinan",
    "青藏地区": "xinan",
}

# Load curated batch
kg = json.loads(KG.read_text(encoding="utf-8"))
batch_sites = kg["batch"]["site"]
batch_books = kg["batch"]["book"]
batch_types = kg["batch"]["joinery_type"]

SITE_PICK = [
    "朗色林庄园",
    "乔家大院",
    "西递村古建筑群",
    "宏村古建筑群",
    "平遥文庙",
    "潭柘寺",
    "临济寺澄灵塔",
    "三原城隍庙",
    "徐霞客故居及晴山堂石刻",
    "可园",
    "定州贡院",
    "法源寺",
    "白云观",
    "庆化寺花塔",
]
BOOK_PICK = [
    "《热河工程则例》",
    "《内庭工程做法》",
    "《园冶》",
    "《扬州画舫录》",
    "《直隶五道成规》",
    "《工程做法》",
]
# types to add if missing
TYPE_PICK = ["半榫", "透榫", "馒头榫", "箍头榫", "管脚榫", "交叉榫", "十字卡腰榫", "穿榫", "楔钉榫"]

SITE_EN = {
    "朗色林庄园": ("Langselin Manor", "Ming manor in Tibet with surviving timber eaves and ladder; documented local joinery."),
    "乔家大院": ("Qiao Family Compound", "Qing merchant courtyard in Qi County, Shanxi—brick-timber frames and fine northern joinery."),
    "西递村古建筑群": ("Xidi Village Ensemble", "Ming–Qing Huizhou village of timber-brick houses; UNESCO-related vernacular carpentry."),
    "宏村古建筑群": ("Hongcun Village Ensemble", "Ming–Qing Huizhou waterside settlement; representative southern residential joinery."),
    "平遥文庙": ("Pingyao Confucian Temple", "Temple complex in Pingyao spanning Jin to Qing layers of official timberwork."),
    "潭柘寺": ("Tanzhe Temple", "Historic Beijing temple; Qing-period fabric within a long northern Buddhist timber lineage."),
    "临济寺澄灵塔": ("Chengling Pagoda, Linji Temple", "Jin-period brick-timber pagoda at Zhengding—hybrid structure with timber detailing."),
    "三原城隍庙": ("Sanyuan City God Temple", "Ming City God temple in Shaanxi; northwest official-style timber halls."),
    "徐霞客故居及晴山堂石刻": ("Xu Xiake Residence & Qingshan Hall", "Ming residence of the travel writer Xu Xiake in Jiangyin, Jiangsu."),
    "可园": ("Keyuan Garden", "Qing garden architecture in Beijing’s Dongcheng—brick-timber pavilions."),
    "定州贡院": ("Dingzhou Examination Hall", "Qing civil-exam compound in Hebei with official timber framing."),
    "法源寺": ("Fayuan Temple", "Historic Beijing monastery with layered repairs in northern timber tradition."),
    "白云观": ("White Cloud Temple", "Major Quanzhen Daoist temple in Beijing; Ming–Qing hall carpentry."),
    "庆化寺花塔": ("Flower Pagoda of Qinghua Temple", "Liao-period flower pagoda in Laishui, Hebei—brick body with timber-era lineage."),
}

TYPE_EN = {
    "半榫": ("Blind / Half Tenon", "Tenon that does not pass through the far face—clean exterior, slightly less leverage than a through tenon."),
    "透榫": ("Through Tenon", "Tenon driven fully through the mortised member; often wedged or pegged for lock."),
    "馒头榫": ("Mantou Tenon", "Rounded ‘bun-shaped’ tenon head used in northern framing and furniture transitions."),
    "箍头榫": ("Coped / Hoop-Head Tenon", "Rail end shaped to wrap or cope onto a post—common in fence-like and furniture rails."),
    "管脚榫": ("Foot / Stub Tenon", "Short tenon seating a leg or post into a base member to locate the foot."),
    "交叉榫": ("Cross / Halving Joint", "Members notch past each other in a cross; used where two axes share a plane."),
    "十字卡腰榫": ("Cross Waist Lock", "Cross joint with a waist catch locking the intersection against slip."),
    "穿榫": ("Piercing Tenon", "Tenon that threads through an intermediate member before seating—related to chuandou logic."),
    "楔钉榫": ("Wedged Key Tenon", "Already in graph as xieding—alias retained only if missing."),
}

BOOK_EN = {
    "《热河工程则例》": ("Rehe Engineering Regulations", "Qing workshop rules for Chengde / Rehe works—tenon sockets, silver-ingot slots and labor norms."),
    "《内庭工程做法》": ("Inner Court Engineering Methods", "Qing inner-court carpentry quotas distinguishing blind, through and foot tenons."),
    "《园冶》": ("Yuan Ye / The Craft of Gardens", "Ming treatise on garden design; frames how timber pavilions meet landscape."),
    "《扬州画舫录》": ("Record of the Painted Barges of Yangzhou", "Qing miscellany of Yangzhou gardens and craft life, with joinery glimpses."),
    "《直隶五道成规》": ("Zhili Five-Circuit Precedents", "Qing regional engineering precedents touching hydraulic and timber works."),
    "《工程做法》": ("Engineering Methods", "Qing official construction methods allied to the doukou modular system."),
}

def slug(s: str) -> str:
    # simple ascii id from existing style
    mapping = {
        "朗色林庄园": "langselin",
        "乔家大院": "qiaojia",
        "西递村古建筑群": "xidi",
        "宏村古建筑群": "hongcun",
        "平遥文庙": "pingyao_wenmiao",
        "潭柘寺": "tanzhe",
        "临济寺澄灵塔": "linji_pagoda",
        "三原城隍庙": "sanyuan_chenghuang",
        "徐霞客故居及晴山堂石刻": "xuxiake",
        "可园": "keyuan",
        "定州贡院": "dingzhou_gongyuan",
        "法源寺": "fayuan",
        "白云观": "baiyun",
        "庆化寺花塔": "qinghua_pagoda",
        "半榫": "bansun",
        "透榫": "tousun",
        "馒头榫": "mantou",
        "箍头榫": "goutou",
        "管脚榫": "guanjiao",
        "交叉榫": "jiaocha",
        "十字卡腰榫": "shizi_kaya",
        "穿榫": "chuansun",
        "《热河工程则例》": "rehe_zeli",
        "《内庭工程做法》": "neiting_zuofa",
        "《园冶》": "yuanye",
        "《扬州画舫录》": "yangzhou_huafang",
        "《直隶五道成规》": "zhili_chenggui",
        "《工程做法》": "gongcheng_zuofa_lit",
    }
    return mapping.get(s, re.sub(r"\W+", "_", s)[:24])


def add_link(src, tgt, rel, rel_en):
    for l in data["links"]:
        s = l["source"]
        t = l["target"]
        if (s == src and t == tgt) or (s == tgt and t == src):
            return
    data["links"].append(
        {"source": src, "target": tgt, "relation": rel, "relationEn": rel_en}
    )


new_nodes = []
# types
for tname in TYPE_PICK:
    if tname in existing_names or tname == "楔钉榫":
        continue
    if any(n["name"] == tname for n in data["nodes"]):
        continue
    en, detail = TYPE_EN[tname]
    nid = slug(tname)
    if nid in by_id:
        continue
    node = {
        "id": nid,
        "name": tname,
        "en": en,
        "type": "mortise",
        "desc": f"{tname}，传统木构榫卯类型。",
        "enDesc": detail.split(".")[0] + ".",
        "detail": f"{tname}是传统木结构中的接合做法。{detail}",
        "enDetail": detail,
        "traits": [f"类型：{tname}", "属木构榫卯体系"],
        "refs": [],
    }
    data["nodes"].append(node)
    by_id[nid] = node
    existing_names.add(tname)
    new_nodes.append(nid)

# sites
site_by_name = {s["name"]: s for s in batch_sites}
for sname in SITE_PICK:
    s = site_by_name.get(sname)
    if not s or sname in existing_names:
        continue
    nid = slug(sname)
    if nid in by_id:
        continue
    en_name, en_detail = SITE_EN.get(sname, (sname, s.get("enDesc") or s["desc"]))
    # pure name already
    node = {
        "id": nid,
        "name": sname,
        "en": en_name,
        "type": "buildingType",
        "desc": s["desc"],
        "enDesc": en_detail if len(en_detail) < 160 else en_detail[:157] + "...",
        "detail": s["desc"]
        + ("；砖木或木构遗存见备注。" if s.get("province") else ""),
        "enDetail": en_detail
        + f" Period noted in sources: {s.get('dynasties') or s.get('era')}. Location: {s.get('province','')}/{s.get('address','')}.",
        "traits": [
            f"位置：{s.get('province','')} {s.get('address','')}".strip(),
            f"分区：{s.get('region')}" if s.get("region") else "国保单位",
        ],
        "refs": ["全国重点文物保护单位名录"],
    }
    # strip empty traits
    node["traits"] = [t for t in node["traits"] if t and not t.endswith("：")]
    data["nodes"].append(node)
    by_id[nid] = node
    existing_names.add(sname)
    new_nodes.append(nid)
    # edges to dynasties
    for d in s.get("dynasties") or []:
        did = DYN_MAP.get(d)
        if did and did in by_id:
            add_link(nid, did, "建于/沿用", "dated to")
    # region
    rid = REGION_MAP.get(s.get("region") or "")
    if rid and rid in by_id:
        add_link(nid, rid, "地域", "in region")
    # only langselin type edges
    if sname == "朗色林庄园":
        for tname, tid in [
            ("半榫", "bansun"),
            ("穿带榫", "chuandai"),
            ("龙凤榫", "longfeng"),
            ("馒头榫", "mantou"),
            ("透榫", "tousun"),
        ]:
            if tid in by_id:
                add_link(nid, tid, "采用", "uses")

# books
book_by_name = {b["name"]: b for b in batch_books}
for bname in BOOK_PICK:
    # normalize
    b = None
    for k, v in book_by_name.items():
        if bname in k or k in bname:
            b = v
            bname = k
            break
    if not b:
        continue
    pure = b["name"]
    if pure in existing_names or pure.replace("《", "").replace("》", "") in {
        n["name"].replace("《", "").replace("》", "") for n in data["nodes"]
    }:
        # skip duplicate of 营造法式 etc.
        continue
    nid = slug(pure)
    if nid in by_id or nid == "gongcheng":
        continue
    en_name, en_detail = BOOK_EN.get(pure, (pure, b.get("desc") or ""))
    excerpt = ""
    if b.get("passages"):
        excerpt = b["passages"][0].get("excerpt") or ""
    node = {
        "id": nid,
        "name": pure if pure.startswith("《") else f"《{pure}》",
        "en": en_name,
        "type": "literature",
        "desc": b.get("desc") or pure,
        "enDesc": en_detail.split(".")[0] + ".",
        "detail": (b.get("desc") or "")
        + (f" 原文摘句：{excerpt}" if excerpt else ""),
        "enDetail": en_detail
        + (f" Sample passage: {excerpt}" if excerpt else ""),
        "traits": [f"作者：{b['author']}" if b.get("author") else "文献", "榫卯相关记述"],
        "refs": [pure],
    }
    data["nodes"].append(node)
    by_id[nid] = node
    existing_names.add(node["name"])
    new_nodes.append(nid)
    for d in b.get("dynasties") or []:
        did = DYN_MAP.get(d)
        if did and did in by_id:
            add_link(nid, did, "成书年代", "compiled in")
    # light links to mortise terms mentioned in excerpt
    for term, tid in [("燕尾", "yanwei"), ("半榫", "bansun"), ("透榫", "tousun"), ("管脚", "guanjiao"), ("斗拱", "dougong"), ("榫窝", "zhi")]:
        if excerpt and term in excerpt and tid in by_id:
            add_link(nid, tid, "记述", "describes")

# relationEn cleanup for older links that are thin
REL_EN_FIX = {
    "认定": "designates",
    "构成": "constitutes",
    "依赖": "depends on",
    "应用": "applies",
    "形成体系": "forms a system",
    "斗拱成型": "dougong matures",
    "延续": "continues into",
    "过渡": "transitions to",
    "组成": "component of",
    "相近": "akin to",
    "接穿带": "meets cleat",
    "框架结合": "frame joint",
    "相对": "complements",
    "衍生": "derives from",
    "框架主体": "main frame joint",
    "基础": "foundation for",
    "同源/同类": "same family",
}
for l in data["links"]:
    if l.get("relation") in REL_EN_FIX:
        l["relationEn"] = REL_EN_FIX[l["relation"]]

header = """/*
 * 中国古代榫卯结构知识图谱 · 数据源码（可审阅镜像）
 * 节点字段：id, name(中), en, type, desc(中), enDesc(英), detail(中详述), traits[], refs[], enDetail(英详述)
 * 边字段：source, target, relation(中), relationEn(英)
 * nodeType：mortise / dynasty / region / craft / culture / buildingType / literature / heritage
 * 扩展规则：节点名纯净；年代写入 desc/detail；国保→朝代 n:1；类型边仅站点级实证
 */
window.GRAPH_DATA = """

out = header + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
DATA.write_text(out, encoding="utf-8")
print("nodes", len(data["nodes"]), "links", len(data["links"]), "new", new_nodes)
