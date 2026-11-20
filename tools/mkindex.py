#!/usr/bin/env python3
"""The store's site from catalog/ (docs/index-format.md).

  mkindex.py [--catalog DIR] [--out DIR] [--key PEM] [--base URL]

For each catalog/<id>.ini (in the order of its `order=`, then by id): the newest
release of its `repo=` (GitHub's API; GITHUB_TOKEN if set) and the asset that
matches `asset=`, or the package at `url=` when that is given. The package is
downloaded for its size and SHA-256. The pictures in catalog/<id>/ are cut and
converted (Pillow; a trailer with ffmpeg). Writes <out>/index.ini, index.sig
(with --key or STORE_KEY: an EC P-256 private key, PEM) and index.html.
"""
import argparse
import datetime
import fnmatch
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from PIL import Image

COVER = (256, 361)
WIDE = (640, 360)
MAX_SHOTS = 6
ID = re.compile(r"^[a-z0-9-]{1,31}$")
KINDS = ("game", "emulator", "app", "system")
SECTIONS = ("games", "emulation", "media", "apps")
# copied from catalog/<id>.ini into the index as they are
KEYS = ("title", "kind", "section", "summary", "description", "genre", "year", "developer",
        "players", "kernel", "needs", "needs_text", "license")


def fail(msg):
    sys.exit(f"mkindex: {msg}")


def read_ini(path):
    out = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line or line.startswith(("#", ";")):
            continue
        if "=" not in line:
            fail(f"{path}:{n}: not key=value")
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": "ps2max-store-mkindex"})
    if accept:
        req.add_header("Accept", accept)
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def release(repo, pattern):
    rel = json.loads(get(f"https://api.github.com/repos/{repo}/releases/latest",
                         "application/vnd.github+json"))
    for a in rel.get("assets", []):
        if fnmatch.fnmatch(a["name"], pattern):
            return {"version": rel["tag_name"].lstrip("v"), "date": rel["published_at"][:10],
                    "url": a["browser_download_url"]}
    fail(f"{repo} {rel['tag_name']}: no asset {pattern}")


def latin1(s, what):
    try:
        s.encode("latin-1")
    except UnicodeEncodeError:
        fail(f"{what}: characters the shell's font does not have: {s!r}")
    return s


def cut(im, size):
    """fill size, cutting what is over"""
    im = im.convert("RGB")
    scale = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    return im.crop((x, y, x + size[0], y + size[1]))


def jpeg(src, size, dst):
    buf = io.BytesIO()
    cut(Image.open(src), size).save(buf, "JPEG", quality=85, subsampling=2, progressive=False,
                                    optimize=True)
    data = buf.getvalue()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(data)
    return hashlib.sha256(data).hexdigest()


def trailer(src, dst):
    if not shutil.which("ffmpeg"):
        fail(f"{src}: a trailer needs ffmpeg")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-t", "30", "-an",
                    "-vf", f"scale={WIDE[0]}:{WIDE[1]}:force_original_aspect_ratio=increase,"
                           f"crop={WIDE[0]}:{WIDE[1]}",
                    "-c:v", "mpeg1video", "-b:v", "2000k", "-f", "mpeg", dst], check=True)
    data = open(dst, "rb").read()
    if len(data) > 8 << 20:
        fail(f"{src}: the trailer is over 8 MiB")
    return hashlib.sha256(data).hexdigest()


def picture(cat, ident, name):
    """catalog/<id>/<name>.* (png, jpg, jpeg, webp), or None"""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = os.path.join(cat, ident, f"{name}.{ext}")
        if os.path.exists(p):
            return p
    return None


def der_to_raw(der):
    """an ECDSA signature, DER, to r and s (32 bytes each)"""
    def integer(b, i):
        if b[i] != 2:
            fail("signature: not DER")
        n = b[i + 1]
        return int.from_bytes(b[i + 2:i + 2 + n], "big"), i + 2 + n
    if der[0] != 0x30:
        fail("signature: not DER")
    i = 3 if der[1] & 0x80 else 2
    r, i = integer(der, i)
    s, _ = integer(der, i)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def sign(data, key):
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
        f.write(key)
        path = f.name
    try:
        der = subprocess.run(["openssl", "dgst", "-sha256", "-sign", path], input=data,
                             capture_output=True, check=True).stdout
    finally:
        os.unlink(path)
    return der_to_raw(der)


def package(url):
    data = get(url)
    return len(data), hashlib.sha256(data).hexdigest()


def page(entries, base):
    rows = []
    for e in entries:
        shots = "".join(f'<img src="{html.escape(s.split()[0])}" alt="">'
                        for s in e.get("shots", "").split(",") if s)
        facts = " · ".join(html.escape(e[k]) for k in ("genre", "year", "developer") if e.get(k))
        desc = html.escape(e.get("description", "")).replace("\\n", "<br>")
        cover = (f'<img class="cover" src="{html.escape(e["cover"].split()[0])}" alt="">'
                 if e.get("cover") else '<div class="cover"></div>')
        source = (f' · <a href="{html.escape(e["source"])}">source</a>' if e.get("source") else "")
        rows.append(f"""<article>{cover}<div><h2>{html.escape(e['title'])}</h2>
<p class="facts">{facts}</p><p>{html.escape(e['summary'])}</p><p>{desc}</p>
<p class="facts">version {html.escape(e['version'])}, {html.escape(e['date'])} ·
<a href="{html.escape(e['url'])}">download</a>{source}</p>
<div class="shots">{shots}</div></div></article>""")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>ps2max store</title>
<style>
:root{{--ink:#121214;--graphite:#1d1d21;--white:#efe9df;--dim:#9a958c;--lamp:#e9c98f}}
body{{margin:0;background:var(--ink);color:var(--white);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:960px;margin:0 auto;padding:32px 16px}}h1{{font-weight:600;letter-spacing:.02em}}
article{{display:flex;gap:24px;background:var(--graphite);border-radius:6px;padding:20px;margin:20px 0}}
.cover{{width:128px;height:180px;flex:none;border-radius:3px;object-fit:cover;background:#2a2a30}}
h2{{margin:0;color:var(--lamp);font-weight:600}}.facts{{color:var(--dim);font-size:14px}}
a{{color:var(--lamp)}}.shots{{display:flex;gap:8px;overflow-x:auto}}.shots img{{height:90px;border-radius:3px}}
@media (max-width:600px){{article{{flex-direction:column}}}}
</style></head><body><main><h1>ps2max store</h1>
<p>Programs for the PlayStation 2 made with ps2max, as the store on the PS2 shows them.</p>
{''.join(rows)}</main></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--catalog", default=os.path.join(here, "catalog"))
    ap.add_argument("--out", default=os.path.join(here, "site"))
    ap.add_argument("--key", help="EC P-256 private key (PEM); else $STORE_KEY")
    ap.add_argument("--base", default="https://ps2max32.github.io/store/")
    a = ap.parse_args()

    found = []
    for name in sorted(os.listdir(a.catalog)):
        if name.endswith(".ini"):
            ident = name[:-4]
            if not ID.match(ident):
                fail(f"{name}: an id is a-z, 0-9 and -, at most 31")
            found.append((ident, read_ini(os.path.join(a.catalog, name))))
    found.sort(key=lambda x: (int(x[1].get("order", 50)), x[0]))

    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    os.makedirs(a.out)
    entries = []
    lines = ["[store]", "format=1",
             "generated=" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             f"base={a.base}", ""]
    for ident, c in found:
        e = {k: latin1(c[k], f"{ident}.{k}") for k in KEYS if c.get(k)}
        for k in ("title", "kind", "summary"):
            if k not in e:
                fail(f"{ident}: no {k}=")
        if e["kind"] not in KINDS or e.get("section", "games") not in SECTIONS:
            fail(f"{ident}: kind= or section= unknown")
        if len(e["title"]) > 40 or len(e["summary"]) > 80 or len(e.get("description", "")) > 600:
            fail(f"{ident}: title (40), summary (80) or description (600) too long")
        if c.get("url"):
            rel = {"url": c["url"], "version": c.get("version", "0"),
                   "date": c.get("date", datetime.date.today().isoformat())}
        elif c.get("repo") and c.get("asset"):
            rel = release(c["repo"], c["asset"])
        else:
            fail(f"{ident}: repo= and asset=, or url=")
        e.update(rel)
        e["size"], e["sha256"] = (str(v) for v in package(rel["url"]))
        if c.get("installed"):
            e["installed"] = c["installed"]
        if c.get("repo"):
            e["source"] = f"https://github.com/{c['repo']}"

        img = f"img/{ident}/"
        if (p := picture(a.catalog, ident, "cover")):
            e["cover"] = f"{img}cover.jpg " + jpeg(p, COVER, os.path.join(a.out, img, "cover.jpg"))
        if (p := picture(a.catalog, ident, "hero")):
            e["hero"] = f"{img}hero.jpg " + jpeg(p, WIDE, os.path.join(a.out, img, "hero.jpg"))
        shots = []
        for n in range(1, MAX_SHOTS + 1):
            if (p := picture(a.catalog, ident, f"shot{n}")):
                shots.append(f"{img}shot{n}.jpg " + jpeg(p, WIDE, os.path.join(a.out, img, f"shot{n}.jpg")))
        if shots:
            e["shots"] = ",".join(shots)
        for ext in ("mp4", "mkv", "webm", "mpg", "mov"):
            p = os.path.join(a.catalog, ident, f"trailer.{ext}")
            if os.path.exists(p):
                e["trailer"] = f"{img}trailer.mpg " + trailer(p, os.path.join(a.out, img, "trailer.mpg"))
                break

        lines.append(f"[{ident}]")
        order = ("title", "kind", "section", "summary", "description", "genre", "year", "developer",
                 "players", "version", "date", "url", "size", "sha256", "installed", "kernel", "needs",
                 "needs_text", "cover", "hero", "shots", "trailer", "source", "license")
        for k in order:
            if e.get(k):
                if "\n" in e[k] or len(f"{k}={e[k]}") > 1023:
                    fail(f"{ident}.{k}: a new line, or the line is over 1023 bytes")
                lines.append(f"{k}={e[k]}")
        lines.append("")
        entries.append(e)
        print(f"mkindex: {ident} {e['version']} {e['size']} bytes", file=sys.stderr)

    index = "\n".join(lines).encode("utf-8")
    if len(index) > 256 << 10:
        fail("index.ini is over 256 KiB")
    open(os.path.join(a.out, "index.ini"), "wb").write(index)
    key = open(a.key).read() if a.key else os.environ.get("STORE_KEY")
    if key:
        open(os.path.join(a.out, "index.sig"), "wb").write(sign(index, key))
    else:
        print("mkindex: no key: index.sig not written", file=sys.stderr)
    open(os.path.join(a.out, "index.html"), "w", encoding="utf-8").write(page(entries, a.base))


if __name__ == "__main__":
    main()
