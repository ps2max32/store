#!/usr/bin/env python3
"""Art for the catalogue, our own: a cover per program, in
MXSHELL2's design (Penumbra: ink, half-shadow, one warm light).

  mkart.py [--catalog DIR] [--fonts DIR] [id ...]

For each catalog/<id>/game.ini (or the ids given) without a cover.png of its own:
catalog/<id>/cover.png (512 x 722, twice the shelf's 256 x 361). The ground is the shell's colour for a tile without a cover
(apps/mxshell src/games.c, title_colour), so the two look alike; the motif
follows `kind` and `type`, its details are seeded by the id, so a run makes
the same pictures again. Art of your own: put a cover.png in
catalog/<id>/ and this leaves it alone (--force makes it anyway).
"""
import argparse
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

LAMP = (233, 201, 143)
WHITE = (239, 233, 223)
INK = (11, 11, 13)
# apps/mxshell src/games.c
TONES = (0x33271F, 0x351C19, 0x2A281C, 0x1B232E, 0x23202B, 0x1C2723, 0x29222C, 0x2C251C)


def title_colour(title):
    h = 2166136261
    for b in title.encode("latin-1"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    t = TONES[h & 7]
    return (t >> 16 & 255, t >> 8 & 255, t & 255)


def read_ini(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if "=" in line and not line.startswith(("#", ";")):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ground(w, h, tone):
    """the tone lit from above, falling to ink"""
    top = mix(tone, WHITE, 0.10)
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        c = mix(top, INK, min(1.0, (y / h) ** 0.8 * 1.05))
        for x in range(w):
            px[x, y] = c
    return im


def light(size, at, radius, strength):
    """the lamp's light: a soft pool, as an alpha mask"""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for i in range(24, 0, -1):
        r = radius * i / 24
        a = round(255 * strength * (1 - i / 24) ** 2)
        d.ellipse((at[0] - r, at[1] - r * 0.55, at[0] + r, at[1] + r * 0.55), fill=a)
    return m.filter(ImageFilter.GaussianBlur(radius / 10))


def motif(w, h, kind, genre, rnd):
    """lines in warm white (an alpha mask) and where the light sits"""
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    g = genre.lower()
    s = w / 512
    if kind == "emulator":
        # pixels: a grid of squares, some lit, falling away
        cell = round(34 * s)
        for gy in range(int(h * 0.18) // cell, int(h * 0.62) // cell):
            for gx in range(1, w // cell - 1):
                if rnd.random() < 0.5:
                    continue
                a = round(rnd.choice((30, 50, 80, 130)) * (1 - gy * cell / h))
                x, y = gx * cell, gy * cell
                d.rectangle((x + 3, y + 3, x + cell - 4, y + cell - 4), outline=a, width=max(1, round(2 * s)))
        return m, (w * rnd.uniform(0.35, 0.65), h * 0.40)
    if "rpg" in g or "role" in g:
        # rings round a point
        cx, cy = w * rnd.uniform(0.4, 0.6), h * rnd.uniform(0.32, 0.42)
        for i in range(1, 9):
            r = i * 34 * s * rnd.uniform(0.9, 1.1)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=round(150 / i + 20), width=max(1, round(2 * s)))
        return m, (cx, cy)
    if "freedom" in g or "flight" in g or "tunnel" in g or "six" in g:
        # a tunnel: frames to a far point
        cx, cy = w * 0.5, h * 0.38
        for i in range(1, 10):
            f = 1 / (1 + i * 0.55)
            rw, rh = w * 0.62 * f, h * 0.34 * f
            ang = rnd.uniform(-0.12, 0.12) * i
            pts = []
            for k in range(4):
                a = ang + math.pi / 4 + k * math.pi / 2
                pts.append((cx + math.cos(a) * rw, cy + math.sin(a) * rh))
            d.polygon(pts, outline=round(40 + 15 * i))
        return m, (cx, cy)
    if kind == "system":
        # mx OS's own start: a point of light over a horizon
        hy = h * 0.46
        d.line((w * 0.08, hy, w * 0.92, hy), fill=120, width=max(1, round(2 * s)))
        for k in range(1, 5):
            y = hy + h * 0.035 * k * k
            d.line((w * (0.08 + 0.02 * k), y, w * (0.92 - 0.02 * k), y), fill=round(60 / k))
        return m, (w * 0.5, hy - h * rnd.uniform(0.04, 0.09))
    if kind == "app":
        # a few stacked panes
        for i in range(5):
            x0 = w * (0.18 + i * 0.05)
            y0 = h * (0.16 + i * 0.06)
            d.rounded_rectangle((x0, y0, x0 + w * 0.5, y0 + h * 0.22), radius=round(10 * s),
                                outline=round(40 + i * 25), width=max(1, round(2 * s)))
        return m, (w * 0.62, h * 0.30)
    # a horizon with a light on it, and the floor's lines running to it
    hy = h * rnd.uniform(0.40, 0.48)
    lx = w * rnd.uniform(0.3, 0.7)
    d.line((0, hy, w, hy), fill=110, width=max(1, round(2 * s)))
    for i in range(-9, 10):
        d.line((lx, hy, lx + i * w * 0.22, h * 0.78), fill=round(70 - abs(i) * 5), width=1)
    for k in range(1, 7):
        y = hy + (h * 0.78 - hy) * (k / 6) ** 1.8
        d.line((0, y, w, y), fill=round(26 + k * 6), width=1)
    # the far shapes: a ridge of blocks or arches on the horizon
    x = 0
    while x < w:
        bw = w * rnd.uniform(0.04, 0.12)
        bh = h * rnd.uniform(0.01, 0.09) * (1.6 if abs(x - lx) > w * 0.15 else 0.5)
        if "shooter" in g and rnd.random() < 0.35:
            d.arc((x, hy - bh * 2, x + bw, hy), 180, 360, fill=90, width=max(1, round(2 * s)))
        else:
            d.rectangle((x, hy - bh, x + bw, hy), outline=70)
        x += bw + w * rnd.uniform(0.0, 0.05)
    return m, (lx, hy)


def fit_font(path, text, width, size, weight):
    while size > 10:
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_name(weight)
        except (OSError, ValueError):
            pass
        if f.getlength(text) <= width:
            return f
        size -= 2
    return f


def wrap(text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if font.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def compose(w, h, c, ident, fonts, text):
    tone = title_colour(c["title"])
    rnd = random.Random(ident)
    im = ground(w, h, tone)
    lines, at = motif(w, h, c.get("kind", "game"), c.get("type", ""), rnd)
    im.paste(Image.new("RGB", (w, h), WHITE), (0, 0), lines.point(lambda v: v * 0.55))
    im.paste(Image.new("RGB", (w, h), LAMP), (0, 0), light((w, h), at, w * 0.55, 0.55))
    # the lamp itself: a small bright point
    core = light((w, h), at, w * 0.05, 1.0)
    im.paste(Image.new("RGB", (w, h), mix(LAMP, WHITE, 0.6)), (0, 0), core)
    # half-shadow at the foot, for the text
    shade = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(int(h * 0.55), h):
        sd.line((0, y, w, y), fill=round(220 * max(0.0, (y - h * 0.55) / (h * 0.45)) ** 1.2))
    im.paste(Image.new("RGB", (w, h), INK), (0, 0), shade)
    if not text:
        return im
    d = ImageDraw.Draw(im)
    s = w / 512
    pad = round(36 * s)
    inter = os.path.join(fonts, "InterTight-Variable.ttf")
    mono = os.path.join(fonts, "JetBrainsMono-Variable.ttf")
    big = fit_font(inter, max(c["title"].split(), key=len), w - 2 * pad, round(84 * s), "Bold")
    tl = wrap(c["title"], big, w - 2 * pad)
    lh = round(big.size * 1.02)
    y = h - pad - round(30 * s) - lh * len(tl)
    for ln in tl:
        d.text((pad, y), ln, font=big, fill=WHITE)
        y += lh
    small = ImageFont.truetype(mono, round(17 * s))
    kind = {"game": "GAME", "emulator": "EMULATOR", "app": "APP", "system": "SYSTEM"}.get(c.get("kind", "game"), "")
    facts = " · ".join(x for x in (c.get("type", "").upper(), c.get("year", "")) if x)
    d.text((pad, h - pad - round(12 * s)), facts, font=small, fill=mix(WHITE, INK, 0.35))
    d.text((pad, pad), kind, font=small, fill=mix(WHITE, INK, 0.4))
    tag = ImageFont.truetype(mono, round(14 * s))
    d.text((w - pad - tag.getlength("ps2max"), pad + round(2 * s)), "ps2max", font=tag,
           fill=mix(LAMP, INK, 0.25))
    # the lit edge on top, as the shelf draws it
    d.rectangle((0, 0, w, max(2, round(3 * s))), fill=mix(LAMP, INK, 0.2))
    return im


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default=os.path.join(here, "catalog"))
    ap.add_argument("--fonts", default=os.path.join(here, "fonts"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("ids", nargs="*")
    a = ap.parse_args()
    ids = a.ids or sorted(n for n in os.listdir(a.catalog) if os.path.exists(os.path.join(a.catalog, n, "game.ini")))
    for ident in ids:
        c = read_ini(os.path.join(a.catalog, ident, "game.ini"))
        out = os.path.join(a.catalog, ident)
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, "cover.png")
        if os.path.exists(p) and not a.force:
            continue
        compose(512, 722, c, ident, a.fonts, True).save(p, optimize=True)
        print(f"mkart: {p}")


if __name__ == "__main__":
    main()
