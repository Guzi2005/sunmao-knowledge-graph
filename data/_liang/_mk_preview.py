# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
import json, re
src = open("../liang-constellations.js", encoding="utf-8").read()
data = json.loads(re.search(r"= (\[.*\]);", src, re.S).group(1))
names = [
    "dule-pavilion-elev", "foguang-daxiong", "dule-guanyin-sec",
    "guangji-sansheng", "shanhua-main", "longxing-zang", "shanhua-shanmen",
]
figs = [f for f in data if f["name"] in names]
cols, CW, CH = 4, 360, 280
rows = (len(figs) + cols - 1) // cols
img = Image.new("RGB", (CW * cols, CH * rows), (8, 6, 4))
dr = ImageDraw.Draw(img)
for k, f in enumerate(figs):
    ox, oy = (k % cols) * CW + 16, (k // cols) * CH + 20
    w, h = CW - 32, CH - 40
    ar = f["ar"]
    if w / h > ar:
        w = int(h * ar)
    else:
        h = int(w / ar)
    pts = [(ox + s[0] * w, oy + s[1] * h) for s in f["stars"]]
    for a, b in f["links"]:
        dr.line([pts[a], pts[b]], fill=(140, 110, 50), width=1)
    for p in pts:
        dr.ellipse([p[0] - 1.2, p[1] - 1.2, p[0] + 1.2, p[1] + 1.2], fill=(240, 225, 180))
    dr.text((ox, oy - 14), "%s %d/%d" % (f["name"], len(f["stars"]), len(f["links"])), fill=(180, 160, 120))
img.save("_preview_new.png")
print("saved", [(f["name"], len(f["stars"]), len(f["links"])) for f in figs])
