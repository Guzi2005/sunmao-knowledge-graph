# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(ROOT, "fonts", "SmileySans-Oblique.ttf")
assert os.path.exists(FONT), FONT


def _char_size(draw, ch, font):
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), ch, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    if hasattr(draw, "textsize"):
        return draw.textsize(ch, font=font)
    return font.getsize(ch)


def bake_title(text, font_size, out_name, letter_spacing=0, glow_radius=18, glow_alpha=110):
    font = ImageFont.truetype(FONT, font_size)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    chars = list(text)
    widths = []
    heights = []
    for ch in chars:
        cw, chh = _char_size(d, ch, font)
        widths.append(cw)
        heights.append(chh)
    total_w = sum(widths) + letter_spacing * (len(chars) - 1)
    ascent, descent = font.getmetrics()
    h = ascent + descent + glow_radius * 4
    w = total_w + glow_radius * 4
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x = glow_radius * 2
    y = glow_radius * 2
    color = (233, 220, 192, 255)
    for i, ch in enumerate(chars):
        draw.text((x, y), ch, font=font, fill=color)
        x += widths[i] + letter_spacing
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    x = glow_radius * 2
    for i, ch in enumerate(chars):
        gd.text((x, y), ch, font=font, fill=(201, 162, 39, glow_alpha))
        x += widths[i] + letter_spacing
    glow = glow.filter(ImageFilter.GaussianBlur(glow_radius))
    glow2 = glow.filter(ImageFilter.GaussianBlur(max(6, glow_radius // 2)))
    out = Image.alpha_composite(Image.alpha_composite(img, glow2), glow)
    out = Image.alpha_composite(out, layer)
    bbox = out.getbbox()
    if bbox:
        pad = 8
        bbox = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(w, bbox[2] + pad),
            min(h, bbox[3] + pad),
        )
        out = out.crop(bbox)
    path = os.path.join(ROOT, out_name)
    out.save(path, "PNG")
    print(out_name, out.size, os.path.getsize(path))


def bake_title_stacked(out_name="title-zh-glow-mobile.png"):
    font_size = 112
    font = ImageFont.truetype(FONT, font_size)
    rows = ["榫卯", "·木", "构千", "年"]
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    cell_w, cell_h = _char_size(d, "榫", font)
    gap_y = int(font_size * -0.08)
    glow_r = 20
    content_w = cell_w * 2
    content_h = cell_h * 4 + gap_y * 3
    pad = glow_r * 3
    W = content_w + pad * 2
    H = content_h + pad * 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    td = ImageDraw.Draw(text)
    y = pad
    paper = (233, 220, 192, 255)
    gold = (201, 162, 39, 95)
    jin = (201, 162, 39, 255)
    for row in rows:
        for ci, ch in enumerate(list(row)):
            x = pad + ci * cell_w
            fill = jin if ch == "·" else paper
            gfill = (201, 162, 39, 120) if ch == "·" else gold
            gd.text((x, y), ch, font=font, fill=gfill)
            td.text((x, y), ch, font=font, fill=fill)
        y += cell_h + gap_y
    glow = glow.filter(ImageFilter.GaussianBlur(glow_r))
    glow2 = glow.filter(ImageFilter.GaussianBlur(10))
    out = Image.alpha_composite(Image.alpha_composite(img, glow2), glow)
    out = Image.alpha_composite(out, text)
    bbox = out.getbbox()
    if bbox:
        p = 6
        out = out.crop(
            (
                max(0, bbox[0] - p),
                max(0, bbox[1] - p),
                min(W, bbox[2] + p),
                min(H, bbox[3] + p),
            )
        )
    path = os.path.join(ROOT, out_name)
    out.save(path, "PNG")
    print(out_name, out.size, os.path.getsize(path))


def bake_qr():
    try:
        import qrcode
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]", "-q"])
        import qrcode

    url = "https://tenennium.fluorescentmice.fun/"
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    base = qr.make_image(fill_color="white", back_color="black").convert("RGBA")
    w, h = base.size
    pad = 40
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    qr_mask = base.split()[0]
    expanded = Image.new("L", canvas.size, 0)
    expanded.paste(qr_mask, (pad, pad))
    expanded = expanded.filter(ImageFilter.MaxFilter(5))
    # tighter, dimmer halo than previous bake
    alpha = expanded.point(lambda p: int(p * 0.22))
    halo_img = Image.merge(
        "RGBA",
        (
            Image.new("L", canvas.size, 201),
            Image.new("L", canvas.size, 162),
            Image.new("L", canvas.size, 39),
            alpha,
        ),
    ).filter(ImageFilter.GaussianBlur(8))
    outer_a = expanded.point(lambda p: int(p * 0.08))
    outer = Image.merge(
        "RGBA",
        (
            Image.new("L", canvas.size, 201),
            Image.new("L", canvas.size, 162),
            Image.new("L", canvas.size, 39),
            outer_a,
        ),
    ).filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(canvas, outer)
    out = Image.alpha_composite(out, halo_img)
    out.paste(base, (pad, pad), base)
    path = os.path.join(ROOT, "qr-tenennium-glow.png")
    out.save(path, "PNG")
    print("qr", out.size, os.path.getsize(path))


if __name__ == "__main__":
    bake_title(
        "榫卯 · 木构千年",
        128,
        "title-zh-glow.png",
        letter_spacing=18,
        glow_radius=22,
        glow_alpha=100,
    )
    bake_title_stacked()
    bake_qr()
