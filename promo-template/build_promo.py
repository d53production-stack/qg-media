#!/usr/bin/env python3
"""QuantGeeks proof-promo template.

Turns one proof screenshot plus a post.json into the promo set the playbook
asks for: Twitter/X 1600x900 first, then Instagram Story 1080x1920, then
Instagram landscape 1080x566, plus an overview sheet.

    python3 build_promo.py posts/2026-10-bricks-lucid            # everything
    python3 build_promo.py posts/2026-10-bricks-lucid x story    # just some formats

Formats: x (layouts mirror, split, band), story, ig. Output lands in
<post>/out/. The proof is never cropped, retouched or upscaled; only glow
outlines, tags and dimming are drawn on top (Lucid promo design rules).
"""
import io
import json
import os
import sys

import cairosvg
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_SVG = os.path.join(HERE, "assets", "Quant Geeks-Logo-v2.svg")

# ---- Brand (Brand Fundamentals + Lucid promo design rules) ----
BG = (6, 8, 7)
GREEN = (50, 205, 50)
GOLD = (255, 214, 90)
WHITE = (255, 255, 255)
MUTED = (150, 170, 155)
FONT_DIRS = ["/usr/share/fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts"), os.path.join(HERE, "fonts")]
FONT_FILES = {
    "head": "InterDisplay-ExtraBold.otf",
    "mono": "DejaVuSansMono-Bold.ttf",
}


def find_font(key):
    name = FONT_FILES[key]
    for root in FONT_DIRS:
        for dirpath, _, files in os.walk(root):
            if name in files:
                return os.path.join(dirpath, name)
    sys.exit(f"Font {name} not found. Install it or drop it in {os.path.join(HERE, 'fonts')}.")


_font_cache = {}


def font(key, size):
    if key not in _font_cache:
        _font_cache[key] = find_font(key)
    return ImageFont.truetype(_font_cache[key], size)


# ---- Drawing helpers ----

def background(w, h, grid=0.04, glows=((0.75, 0.3, 0.55),)):
    """Near-black ground, faint 54px green grid, soft green radial glows, vignette."""
    im = Image.new("RGB", (w, h), BG)
    if grid:
        layer = Image.new("RGB", (w, h), BG)
        d = ImageDraw.Draw(layer)
        for x in range(0, w, 54):
            d.line([(x, 0), (x, h)], fill=GREEN)
        for y in range(0, h, 54):
            d.line([(0, y), (w, y)], fill=GREEN)
        im = Image.blend(im, layer, grid)
    for gx, gy, gr in glows:
        r = int(max(w, h) * gr)
        glow = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glow).ellipse([gx * w - r / 2, gy * h - r / 2, gx * w + r / 2, gy * h + r / 2], fill=70)
        glow = glow.filter(ImageFilter.GaussianBlur(r / 4))
        im = Image.composite(Image.new("RGB", (w, h), GREEN), im, glow.point(lambda v: v * 0.35))
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).rectangle([0, 0, w, h], outline=255, width=int(min(w, h) * 0.08))
    vig = vig.filter(ImageFilter.GaussianBlur(min(w, h) * 0.08))
    return Image.composite(Image.new("RGB", (w, h), (0, 0, 0)), im, vig.point(lambda v: v * 0.6))


def tracked(draw, xy, text, fnt, fill, spacing=0.18):
    """Monospace label with wide letter spacing. Returns the drawn width."""
    x, y = xy
    step = fnt.getlength("M") * (1 + spacing)
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += step
    return step * len(text) - fnt.getlength("M") * spacing


def tracked_width(text, fnt, spacing=0.18):
    return fnt.getlength("M") * ((1 + spacing) * len(text) - spacing)


def glow_rect(canvas, box, color, radius=14, stroke=3, blur=20, ring=0):
    """Blurred halo + inner glow + crisp stroke (+ optional hairline ring further out)."""
    x0, y0, x1, y1 = box
    halo = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(halo).rounded_rectangle(box, radius, outline=255, width=stroke + 6)
    halo = halo.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(Image.new("RGB", canvas.size, color), (0, 0), halo.point(lambda v: min(255, v * 2)))
    inner = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(inner).rounded_rectangle(box, radius, outline=255, width=stroke + 2)
    inner = inner.filter(ImageFilter.GaussianBlur(4))
    canvas.paste(Image.new("RGB", canvas.size, color), (0, 0), inner.point(lambda v: v * 0.6))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(box, radius, outline=color, width=stroke)
    if ring:
        d.rounded_rectangle([x0 - ring, y0 - ring, x1 + ring, y1 + ring], radius + ring, outline=color, width=1)


def pill(canvas, center_x, center_y, text, bg, size=22, fg=(0, 0, 0)):
    """Black mono text on a coloured pill, centred on (center_x, center_y)."""
    f = font("mono", size)
    tw = tracked_width(text, f, 0.12)
    pw, ph = tw + size * 1.4, size * 1.75
    x0, y0 = center_x - pw / 2, center_y - ph / 2
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], 8, fill=bg)
    asc, desc = f.getmetrics()
    tracked(d, (x0 + size * 0.7, center_y - (asc + desc) / 2 + 1), text, f, fg, 0.12)
    return x0, y0, x0 + pw, y0 + ph


_logo_cache = {}


def logo(width):
    """Official >QuantGeeks_ wordmark, rendered from the SVG and trimmed to its ink."""
    if width not in _logo_cache:
        big = Image.open(io.BytesIO(cairosvg.svg2png(url=LOGO_SVG, output_width=4320))).convert("RGBA")
        big = big.crop(big.getbbox())
        h = round(big.height * width / big.width)
        _logo_cache[width] = big.resize((width, h), Image.LANCZOS)
    return _logo_cache[width]


def paste_logo(canvas, x, y, width, glow=True):
    lg = logo(width)
    if glow:
        pad = Image.new("L", canvas.size, 0)
        pad.paste(lg.split()[3], (int(x), int(y)))
        pad = pad.filter(ImageFilter.GaussianBlur(width * 0.035))
        canvas.paste(GREEN, (0, 0) + canvas.size, pad.point(lambda v: v * 0.45))
    canvas.paste(lg, (int(x), int(y)), lg)
    return lg.size


def fit_headline(lines, max_w, max_size, min_size=40):
    size = max_size
    while size > min_size:
        f = font("head", size)
        if max(f.getlength(l) for l in lines) <= max_w:
            return f
        size -= 2
    return font("head", min_size)


# ---- Proof card ----

def load_proof(post_dir, cfg):
    path = os.path.join(post_dir, cfg["proof"])
    if os.path.exists(path):
        return Image.open(path).convert("RGB"), False
    # Stand-in so the layout can be previewed before the real screenshot arrives.
    w, h = cfg["proof_size"]
    im = Image.new("RGB", (w, h), (14, 16, 18))
    d = ImageDraw.Draw(im)
    for key, color in (("hero", (40, 60, 40)), ("secondary", (60, 55, 30))):
        if key in cfg:
            d.rectangle(cfg[key]["box"], fill=color)
    f = font("mono", 28)
    msg = f"PLACEHOLDER - drop {cfg['proof']} in the post folder"
    d.text((w / 2, h / 2), msg, font=f, fill=WHITE, anchor="mm")
    return im, True


def proof_card(proof, cfg, scale=1.0):
    """The screenshot on its card body, dimmed outside the focus areas, with glow outlines and tags.

    Returns (layer RGB, body mask L, highlight mask L, extra) where the layer has `extra`
    px of room on every side for glows and tags that spill past the card edge."""
    shot = proof.copy()
    boxes = [cfg[k]["box"] for k in ("hero", "secondary") if k in cfg]
    if boxes and cfg.get("dim"):
        dimmed = ImageEnhance.Brightness(shot).enhance(max(0.6, cfg["dim"]))
        for b in boxes:
            dimmed.paste(shot.crop(b), b[:2])
        shot = dimmed
    if scale != 1.0:
        assert 0.8 <= scale < 1.0, "proof may only scale down, to no less than 80%"
        shot = shot.resize((round(shot.width * scale), round(shot.height * scale)), Image.LANCZOS)
    pad, extra = 10, 60
    cw, ch = shot.width + pad * 2, shot.height + pad * 2
    layer = Image.new("RGB", (cw + extra * 2, ch + extra * 2), BG)
    layer.paste(Image.new("RGB", (cw, ch), proof.getpixel((2, 2))), (extra, extra))
    layer.paste(shot, (extra + pad, extra + pad))
    body = Image.new("L", layer.size, 0)
    ImageDraw.Draw(body).rounded_rectangle([extra, extra, extra + cw - 1, extra + ch - 1], 20, fill=255)
    hl = Image.new("L", layer.size, 0)
    o = extra + pad

    def to_layer(b, grow=4):
        return [o + b[0] * scale - grow, o + b[1] * scale - grow, o + b[2] * scale + grow, o + b[3] * scale + grow]

    tags = []
    if "secondary" in cfg:
        sb = to_layer(cfg["secondary"]["box"])
        glow_rect(layer, sb, GOLD, stroke=2, blur=14)
        tags.append((o + cfg["secondary"]["tag_x"] * scale, sb[1], cfg["secondary"]["tag"], GOLD))
        ImageDraw.Draw(hl).rectangle([sb[0] - 40, sb[1] - 40, sb[2] + 40, sb[3] + 40], fill=255)
    if "hero" in cfg:
        hb = to_layer(cfg["hero"]["box"])
        glow_rect(layer, hb, GREEN, stroke=3, blur=20, ring=10 if cfg["hero"].get("ring", True) else 0)
        size = round(22 * scale)
        tw = tracked_width(cfg["hero"]["tag"], font("mono", size), 0.12) + size * 1.4
        right = cfg["hero"].get("tag_align", "right") == "right"
        tx = hb[2] - 24 - tw / 2 if right else hb[0] + 24 + tw / 2
        tags.append((tx, hb[1], cfg["hero"]["tag"], GREEN))
        ImageDraw.Draw(hl).rectangle([hb[0] - 40, hb[1] - 40, hb[2] + 40, hb[3] + 40], fill=255)
    for x, y, text, color in tags:
        pill(layer, x, y, text, color, size=round(22 * scale))
    # Highlights may spill outside the card body, but only as glow over the background.
    return layer, body, ImageChops.lighter(body, hl), extra, (cw, ch)


def draw_card(canvas, proof, cfg, x, y, scale=1.0):
    """Floating card: deep shadow, soft green ambient glow, the card, a green rim brightest
    at the top, and the neutral source label on the top edge. (x, y) is the body's top-left."""
    layer, body, show, extra, (cw, ch) = proof_card(proof, cfg, scale)
    W, H = canvas.size
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle([x, y + 24, x + cw, y + ch + 24], 20, fill=230)
    canvas.paste((0, 0, 0), (0, 0, W, H), shadow.filter(ImageFilter.GaussianBlur(36)))
    amb = Image.new("L", (W, H), 0)
    ImageDraw.Draw(amb).rounded_rectangle([x, y, x + cw, y + ch], 20, outline=255, width=10)
    canvas.paste(GREEN, (0, 0, W, H), amb.filter(ImageFilter.GaussianBlur(40)).point(lambda v: v * 0.35))
    # Outside the body, only bright glow pixels of the highlight layer show (screen-like).
    lum = layer.convert("L").point(lambda v: 0 if v < 20 else min(255, v * 2))
    outside = ImageChops.multiply(ImageChops.multiply(show, ImageChops.invert(body)), lum)
    canvas.paste(layer, (x - extra, y - extra), ImageChops.lighter(body, outside))
    rim = Image.new("L", (W, H), 0)
    ImageDraw.Draw(rim).rounded_rectangle([x - 1, y - 1, x + cw, y + ch], 21, outline=255, width=2)
    fade = Image.new("L", (W, H), 0)
    fade.paste(Image.linear_gradient("L").resize((W, ch + 4)).point(lambda v: 255 - int(v * 0.75)), (0, y - 2))
    canvas.paste(GREEN, (0, 0, W, H), ImageChops.multiply(rim, fade))
    # Re-paste tags/glow that sit on the rim so the rim doesn't cut through them.
    canvas.paste(layer, (x - extra, y - extra), ImageChops.multiply(ImageChops.subtract(show, body), lum))
    label = cfg["source_label"]
    f = font("mono", 15)
    tw = tracked_width(label, f, 0.2)
    d = ImageDraw.Draw(canvas)
    lx, ly = x + 26, y - 13
    d.rounded_rectangle([lx, ly, lx + tw + 46, ly + 26], 13, fill=BG, outline=(70, 80, 72))
    d.ellipse([lx + 13, ly + 9, lx + 21, ly + 17], fill=WHITE)
    tracked(d, (lx + 30, ly + 4), label, f, (225, 230, 226), 0.2)
    return cw, ch


# ---- Copy blocks ----

def draw_kicker_headline(canvas, cfg, x, y, max_w, max_size=72):
    d = ImageDraw.Draw(canvas)
    kf = font("mono", 24)
    tracked(d, (x, y), cfg["kicker"], kf, GREEN, 0.16)
    hf = fit_headline(cfg["headline"], max_w, max_size)
    yy = y + 52
    for line in cfg["headline"]:
        d.text((x, yy), line, font=hf, fill=WHITE)
        yy += round(hf.size * 1.06)
    return yy


def draw_stats(canvas, cfg, x, y, w, vertical=False, value_size=52):
    d = ImageDraw.Draw(canvas)
    lf, vf = font("mono", 16), font("head", value_size)
    n = len(cfg["stats"])
    if vertical:
        for i, s in enumerate(cfg["stats"]):
            yy = y + i * (value_size + 56)
            tracked(d, (x, yy), s["label"], lf, MUTED, 0.22)
            d.text((x, yy + 26), s["value"], font=vf, fill=GREEN if s.get("green") else WHITE)
        return y + n * (value_size + 56)
    d.line([(x, y), (x + w, y)], fill=(40, 52, 44), width=1)
    col = w / n
    for i, s in enumerate(cfg["stats"]):
        cx = x + i * col
        tracked(d, (cx, y + 22), s["label"], lf, MUTED, 0.22)
        d.text((cx, y + 48), s["value"], font=vf, fill=GREEN if s.get("green") else WHITE)
    end = y + 48 + value_size + 30
    d.line([(x, end), (x + w, end)], fill=(40, 52, 44), width=1)
    return end


def draw_signoff(canvas, cfg, x, bottom, logo_w):
    d = ImageDraw.Draw(canvas)
    lg_h = logo(logo_w).height
    top = bottom - lg_h
    tracked(d, (x, top - 44), cfg["signoff"], font("mono", 20), MUTED, 0.22)
    paste_logo(canvas, x, top, logo_w)


# ---- Layouts ----

def card_size(cfg, scale):
    w, h = cfg["proof_size"]
    return round(w * scale) + 20, round(h * scale) + 20


def fit_scale(cfg, max_w, max_h):
    w, h = card_size(cfg, 1.0)
    s = min(1.0, max_w / w, max_h / h)
    if s < 0.8:
        sys.exit(f"Proof needs {s:.0%} scale to fit; the rules allow no less than 80%.")
    return s


def layout_side(proof, cfg, W, H, M, card_left):
    """Mirror (card left) or split (card right): card ~55% width, copy column beside it."""
    im = background(W, H, glows=((0.3 if card_left else 0.7, 0.45, 0.6),))
    s = fit_scale(cfg, W * 0.58, H - 2 * M + 30)
    cw, ch = card_size(cfg, s)
    cy = (H - ch) // 2
    cx = M if card_left else W - M - cw
    col_x = cx + cw + 64 if card_left else M
    col_w = (W - M - col_x) if card_left else (cx - 64 - M)
    draw_card(im, proof, cfg, cx, cy, s)
    end = draw_kicker_headline(im, cfg, col_x, cy + 10, col_w, max_size=72 if H > 860 else 64)
    draw_stats(im, cfg, col_x, end + 28, col_w, vertical=True, value_size=44 if H > 860 else 38)
    draw_signoff(im, cfg, col_x, cy + ch - 6, min(col_w, 440))
    return im


def layout_band(proof, cfg, W, H, M):
    """Headline in one line across the top, card centred, stats left, logo right."""
    im = background(W, H, glows=((0.5, 0.55, 0.7),))
    d = ImageDraw.Draw(im)
    kf = font("mono", 20)
    kw = tracked_width(cfg["kicker"], kf, 0.16)
    tracked(d, ((W - kw) / 2, M), cfg["kicker"], kf, GREEN, 0.16)
    line = " ".join(cfg["headline"])
    hf = fit_headline([line], W - 2 * M, 58)
    d.text((W / 2, M + 32), line, font=hf, fill=WHITE, anchor="mt")
    top = M + 32 + hf.size + 30
    s = fit_scale(cfg, W * 0.5, H - top - M)
    cw, ch = card_size(cfg, s)
    cx = (W - cw) // 2
    draw_card(im, proof, cfg, cx, top, s)
    side = cx - 48 - M
    draw_stats(im, cfg, M, top + 20, side, vertical=True, value_size=36)
    lw = min(side, 300)
    rx = W - M - lw
    draw_signoff(im, cfg, rx, top + ch - 10, lw)
    return im


def layout_story(proof, cfg):
    """Instagram Story: kicker, headline, card, stats, logo lockup, all inside y 250-1580."""
    W, H, M = 1080, 1920, 64
    im = background(W, H, glows=((0.5, 0.45, 0.8),))
    end = draw_kicker_headline(im, cfg, M, 262, W - 2 * M, max_size=84)
    s = fit_scale(cfg, W - 2 * M, 1580 - 300 - (end + 40))
    cw, ch = card_size(cfg, s)
    cy = end + 36
    draw_card(im, proof, cfg, (W - cw) // 2, cy, s)
    stats_end = draw_stats(im, cfg, M, cy + ch + 36, W - 2 * M, value_size=52)
    draw_signoff(im, cfg, M, min(1580, stats_end + 60 + logo(430).height + 44), 430)
    return im


LANDSCAPE = {
    "mirror": lambda p, c, W, H, M: layout_side(p, c, W, H, M, card_left=True),
    "split": lambda p, c, W, H, M: layout_side(p, c, W, H, M, card_left=False),
    "band": layout_band,
}


def overview(images, path, cols=3, cell_w=520):
    cells = []
    for name, im in images:
        t = im.copy()
        t.thumbnail((cell_w, cell_w * 2))
        cells.append((name, t))
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    heights = [max(t.height for _, t in row) + 40 for row in rows]
    sheet = Image.new("RGB", (cols * (cell_w + 24) + 24, sum(heights) + 24), (20, 22, 21))
    d = ImageDraw.Draw(sheet)
    y = 24
    for row, rh in zip(rows, heights):
        for i, (name, t) in enumerate(row):
            x = 24 + i * (cell_w + 24)
            sheet.paste(t, (x, y))
            d.text((x, y + t.height + 8), name, font=font("mono", 16), fill=MUTED)
        y += rh
    sheet.save(path)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    post_dir = os.path.abspath(sys.argv[1])
    formats = sys.argv[2:] or ["x", "story", "ig"]
    with open(os.path.join(post_dir, "post.json")) as fh:
        cfg = json.load(fh)
    proof, placeholder = load_proof(post_dir, cfg)
    if not placeholder and list(proof.size) != list(cfg["proof_size"]):
        sys.exit(f"Proof is {proof.size}, post.json says {cfg['proof_size']}. Re-measure the focus boxes.")
    out = os.path.join(post_dir, "out")
    os.makedirs(out, exist_ok=True)
    tag = "-PLACEHOLDER" if placeholder else ""
    made = []
    if "x" in formats:
        for name, fn in LANDSCAPE.items():
            im = fn(proof, cfg, 1600, 900, 64)
            im.save(os.path.join(out, f"{cfg['name']}-x-{name}{tag}.png"))
            made.append((f"X {name}", im))
    if "story" in formats:
        im = layout_story(proof, cfg)
        im.save(os.path.join(out, f"{cfg['name']}-story{tag}.png"))
        made.append(("Story", im))
    if "ig" in formats:
        for name, fn in LANDSCAPE.items():
            im = fn(proof, cfg, 1600, 838, 59).resize((1080, 566), Image.LANCZOS)
            im.save(os.path.join(out, f"{cfg['name']}-ig-{name}{tag}.png"))
            made.append((f"IG {name}", im))
    overview(made, os.path.join(out, f"{cfg['name']}-overview{tag}.png"))
    print(f"{len(made)} images in {out}" + (" (placeholder proof: not for posting)" if placeholder else ""))


if __name__ == "__main__":
    main()
