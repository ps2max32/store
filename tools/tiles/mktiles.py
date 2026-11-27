#!/usr/bin/env python3
"""The covers of our own programs, and of Daedalus and NJEMU, in the shell's
Penumbra light (MXSHELL2: ink, one warm lamp from above, a floor with its
reflection).

  mktiles.py [id ...]

Writes catalog/<id>/cover.png (512 x 722) for files, media, mxboot, mxos,
mxshell, mxstore, daedalus and njemu (or the ids given): each tile is an SVG
drawn by this script, made into a picture by a headless Chrome or Chromium
(google-chrome, chromium or $CHROME). The fonts are Inter Tight and Saira
Extra Condensed from Google Fonts, so it needs the network.

The programs' glyphs are drawn here (G). Daedalus: its own D cube logo
(img/dcube.png, from DaedalusX64's Vita port). NJEMU: its own artwork of the
four boards it plays (img/sq_*.jpg, from NJEMU's data/artwork) and its name
(img/w_nj_mvs.png, cut from the MVS one).
"""
import base64, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "..", "catalog")
W, H = 300, 423  # the drawing's units; the picture is 512 x 722


def data(name):
    kind = "image/png" if name.endswith(".png") else "image/jpeg"
    with open(os.path.join(HERE, "img", name), "rb") as f:
        return f"data:{kind};base64," + base64.b64encode(f.read()).decode()


# a glyph in a 100 x 100 box: its lines, and its lit part (the lamp's colour)
G = {
    "files": ('<path d="M12 30Q12 25 17 25H38L45 32H83Q88 32 88 37V76Q88 81 83 81H17Q12 81 12 76Z"/>'
              '<path d="M12 45H88"/>', '<path d="M24 40V20H70L76 26V40"/>'),
    "media": ('<circle cx="50" cy="53" r="34"/>', '<path d="M43 38L66 53L43 68Z"/>'),
    "mxboot": ('<path d="M33 32A28 28 0 1 0 67 32"/>', '<path d="M50 14V50"/>'),
    "mxos": ('<rect x="26" y="29" width="48" height="48" rx="6"/><path d="M36 29V19M50 29V19M64 29V19M36 77V87'
             'M50 77V87M64 77V87M26 39H16M26 53H16M26 67H16M74 39H84M74 53H84M74 67H84"/>',
             '<rect x="40" y="43" width="20" height="20" rx="2"/>'),
    "mxshell": ('<rect x="12" y="38" width="18" height="34" rx="3"/><rect x="70" y="38" width="18" height="34" rx="3"/>'
                '<path d="M6 82H94"/>', '<rect x="37" y="24" width="26" height="48" rx="3"/>'),
    "mxstore": ('<path d="M20 38H80L75 86H25Z"/><path d="M37 38V32A13 13 0 0 1 63 32V38"/>',
                '<path d="M50 50V73M40 64L50 74L60 64"/>'),
}
TITLES = {"files": "FILES", "media": "MEDIA", "mxboot": "MXBOOT", "mxos": "MXKERNEL", "mxshell": "MXSHELL",
          "mxstore": "MXSTORE"}

DEFS = '''<defs>
<radialGradient id="cone" cx="50%" cy="0%" r="95%" fx="50%" fy="0%"><stop offset="0" stop-color="#6b5838"/>
<stop offset=".45" stop-color="#241e16"/><stop offset="1" stop-color="#080808"/></radialGradient>
<radialGradient id="pool" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#e9c98f" stop-opacity=".38"/>
<stop offset="1" stop-color="#e9c98f" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/>
<stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="refl"><rect y="268" width="300" height="120" fill="url(#fade)"/></mask></defs>'''


def room(floor):
    """the lamp on ink, the floor at y floor and the light's pool on it"""
    return (f'{DEFS}<rect width="{W}" height="{H}" fill="url(#cone)"/>'
            f'<rect y="{floor}" width="{W}" height="{H - floor}" fill="#0b0a09"/>'
            f'<ellipse cx="150" cy="{floor}" rx="135" ry="26" fill="url(#pool)"/>')


def glyph(ident):
    lines, lit = G[ident]
    s = 2.0

    def g(stroke, fill, extra=""):
        return (f'<g transform="translate({150 - 50 * s} {170 - 53 * s}) scale({s})" stroke="{stroke}" '
                f'fill="{fill}" stroke-width="3.36" stroke-linecap="round" stroke-linejoin="round" {extra}>')
    glow = 'filter="url(#glow)" opacity=".8"'
    return (f'{room(268)}'
            f'<g mask="url(#refl)"><g transform="translate(0 536) scale(1 -1)">{g("#ece6dc", "none")}{lines}</g>'
            f'{g("#e9c98f", "#e9c98f")}{lit}</g></g></g>'
            f'{g("#e9c98f", "#e9c98f", glow)}{lit}</g>'
            f'{g("#ece6dc", "none")}{lines}</g>{g("#f3dca8", "#e9c98f")}{lit}</g>'
            f'<text x="150" y="392" class="tt">{TITLES[ident]}</text>')


def daedalus():
    return (f'{room(290)}<image href="{data("dcube.png")}" x="83" y="96" width="134" height="146"/>'
            '<text x="150" y="342" class="dx">DaedalusX64</text>')


def njemu():
    quads = "".join(f'<image href="{data("sq_" + b + ".jpg")}" x="{x}" y="{y}" width="150" height="150"/>'
                    for b, x, y in (("cps1", 0, 0), ("cps2", 150, 0), ("mvs", 0, 150), ("ncdz", 150, 150)))
    return (f'<rect width="{W}" height="{H}" fill="#0a0a0b"/>{quads}'
            '<defs><linearGradient id="nf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a0a0b" '
            'stop-opacity="0"/><stop offset="1" stop-color="#0a0a0b"/></linearGradient></defs>'
            f'<rect y="270" width="{W}" height="30" fill="url(#nf)"/><rect y="300" width="{W}" height="123" fill="#0a0a0b"/>'
            f'<image href="{data("w_nj_mvs.png")}" x="10" y="318" width="280" height="68"/>')


PAGE = '''<!doctype html><meta charset=utf-8>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@600&family=Saira+Extra+Condensed:wght@500&display=block" rel="stylesheet">
<style>body{margin:0;background:#080808}svg{display:block;width:512px;height:722px}
.tt{font:600 21px "Inter Tight",sans-serif;letter-spacing:.17em;fill:#ECEAE6;text-anchor:middle}
.dx{font:500 40px "Saira Extra Condensed",sans-serif;fill:#ECEAE6;text-anchor:middle;letter-spacing:.01em}</style>
<svg viewBox="0 0 300 423">%s</svg>'''


def main():
    ids = sys.argv[1:] or list(G) + ["daedalus", "njemu"]
    chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        sys.exit("mktiles: no Chrome or Chromium (set CHROME)")
    tmp = tempfile.mkdtemp()
    try:
        for ident in ids:
            svg = daedalus() if ident == "daedalus" else njemu() if ident == "njemu" else glyph(ident)
            page = os.path.join(tmp, ident + ".html")
            with open(page, "w") as f:
                f.write(PAGE % svg)
            out = os.path.join(CATALOG, ident, "cover.png")
            subprocess.run([chrome, "--headless=new", "--hide-scrollbars", f"--user-data-dir={tmp}/profile",
                            "--window-size=512,722", f"--screenshot={out}", "--virtual-time-budget=6000",
                            "file://" + page], check=True, capture_output=True)
            print(f"mktiles: {out}")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
