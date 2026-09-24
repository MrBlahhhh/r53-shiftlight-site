#!/usr/bin/env python3
"""Build the R53 shift light page from template.html.

Two outputs from one template:

  dist/index.html        the hosted page: real files under dist/assets/, loaders fetch them
  preview.html           a single self-contained file with every asset inlined as base64,
                         for the claude.ai artifact preview (not committed, ~9 MB)

Assets come from assets.json, a {key: {uri|b64, ext}} map produced by pack.py from the
blog photos, the KiCad renders and the model files. dist/assets/ is committed, so a
re-deploy never needs kicad-cli or the blog checkout; only a new photo does.

    python build.py            # both outputs
    python build.py --preview  # preview only
"""
import base64
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.html")
ASSETS = os.path.join(HERE, "assets.json")
DIST = os.path.join(HERE, "dist")

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A CAN bus shift light for the 2002–2006 MINI Cooper S (R53): printed housing, assembled light, free companion app, and the K-line + CAN bridge that feeds the R53 Logger · Flasher.">
<meta property="og:title" content="R53 Shift Light">
<meta property="og:description" content="Eight LEDs on the column shroud, fed by the engine's own CAN bus. Housing, assembled light, free app, and the K-line + CAN bridge.">
<meta property="og:image" content="https://ryansdesigns.geekopolis.com/shiftlight/assets/installed.webp">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0B1811">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='4' fill='%230B1811'/%3E%3Crect x='5' y='11' width='4' height='10' fill='%232BF06A'/%3E%3Crect x='11' y='11' width='4' height='10' fill='%232BF06A'/%3E%3Crect x='17' y='11' width='4' height='10' fill='%23FFB000'/%3E%3Crect x='23' y='11' width='4' height='10' fill='%23FF2E2E'/%3E%3C/svg%3E">
"""


def load_assets():
    if os.path.exists(ASSETS):
        return json.load(open(ASSETS))
    # no assets.json: rebuild the map from the committed dist/assets so the hosted build
    # still works; the preview needs the packed file
    out = {}
    for f in os.listdir(os.path.join(DIST, "assets")):
        k, ext = os.path.splitext(f)
        out[k] = {"ext": ext[1:]}
    return out


def versioned(rel):
    """`assets/x.webp?v=1a2b3c4d` -- the first bytes of the file's SHA-1.

    nginx sends every asset with a 30-day max-age, and the file names never
    change, so a re-render that only swaps bytes was invisible to anyone who
    had seen the page before: the new picture sat on the server behind the
    old one in every browser cache. The query string changes with the
    content, so a redeploy is seen on the next load with no cache flush.
    """
    path = os.path.join(DIST, rel)
    if not os.path.exists(path):
        return rel
    h = hashlib.sha1(open(path, "rb").read()).hexdigest()[:8]
    return "%s?v=%s" % (rel, h)


def hosted(template, assets):
    def sub(m):
        k = m.group(1)
        if k == "manifest":
            return "{inline:false, stl:'%s', glb:'%s'}" % (
                versioned("assets/housing.stl"), versioned("assets/board.glb"))
        if k in ("stl", "glb"):
            return ""
        return versioned("assets/%s.%s" % (k, assets[k].get("ext", "webp")))
    body = re.sub(r"\{\{ASSET:(\w+)\}\}", sub, template)
    m = re.search(r"^(<title>.*?</title>\n(?:<link[^\n]*\n)+<style>.*?</style>\n)", body, re.S)
    if not m:
        sys.exit("template must start with <title>, the font <link>s and one <style> block")
    return HEAD + m.group(1) + "</head>\n<body>\n" + body[m.end():] + "\n</body>\n</html>\n"


def preview(template, assets):
    def sub(m):
        k = m.group(1)
        if k == "manifest":
            return "{inline:true}"
        a = assets[k]
        if "b64" in a:
            return a["b64"]
        if "uri" in a:
            return a["uri"]
        name = {"stl": "housing.stl", "glb": "board.glb"}.get(k, "%s.%s" % (k, a.get("ext", "webp")))
        path = os.path.join(DIST, "assets", name)
        data = open(path, "rb").read()
        if k in ("stl", "glb"):
            return base64.b64encode(data).decode()
        mime = "image/png" if a.get("ext") == "png" else "image/webp"
        return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode())
    return re.sub(r"\{\{ASSET:(\w+)\}\}", sub, template)


def main():
    template = io.open(TEMPLATE, encoding="utf-8").read()
    assets = load_assets()
    assets.setdefault("stl", {"ext": "stl"})
    assets.setdefault("glb", {"ext": "glb"})
    if "--preview" not in sys.argv:
        out = hosted(template, assets)
        io.open(os.path.join(DIST, "index.html"), "w", encoding="utf-8", newline="\n").write(out)
        print("dist/index.html  %5.0f KB" % (len(out.encode("utf-8")) / 1024))
    out = preview(template, assets)
    io.open(os.path.join(HERE, "preview.html"), "w", encoding="utf-8", newline="\n").write(out)
    print("preview.html     %5.2f MB" % (len(out.encode("utf-8")) / 1e6))


if __name__ == "__main__":
    main()
