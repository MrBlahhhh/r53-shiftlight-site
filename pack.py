#!/usr/bin/env python3
"""Regenerate dist/assets/ and assets.json from the source material.

Only needed when a photo, screenshot, render or model changes. A plain page edit is
`python build.py` alone, since dist/assets/ is committed.

Sources (all on Matt's machine; adjust the paths if they move):
  BLOG    the MrBlahhhh.github.io checkout, assets/images/
  RENDER  kicad-cli output for the carrier (pcb_top.png, shiftlight_iso.png, shiftlight_bottom.png,
          bridge_iso.png, shiftlight.glb) plus google-play-badge.png
  STL     the R53 housing STL
"""
import base64
import io
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BLOG = os.environ.get("BLOG", r"C:\Projects\MrBlahhhh.github.io\assets\images")
RENDER = os.environ.get("RENDER", os.path.join(HERE, "render"))
STL = os.environ.get("STL", os.path.join(HERE, "render", "r53shiftlight.stl"))
OUT = os.path.join(HERE, "dist", "assets")

# key: (path, longest edge px, WebP quality, trim transparent margins)
IMAGES = {
    "installed":   (f"{BLOG}/r53-shift-light/shift-light-installed.jpg", 1600, 78, False),
    "bench":       (f"{BLOG}/r53-shift-light/shift-light-bench.jpg",     1200, 72, False),
    "wirerun":     (f"{BLOG}/r53-shift-light/install-wire-run.jpg",      1200, 72, False),
    "powertap":    (f"{BLOG}/r53-shift-light/install-power-tap.jpg",     1200, 72, False),
    "app_thr":     (f"{BLOG}/r53-shift-light/app-thresholds.jpg",         900, 74, False),
    "app_strip":   (f"{BLOG}/r53-shift-light/app-strip.jpg",              900, 74, False),
    "app_graph":   (f"{BLOG}/r53-shift-light/app-graph.jpg",              900, 74, False),
    "app_can":     (f"{BLOG}/r53-shift-light/app-canbus.jpg",             900, 74, False),
    "bridge_3d":   (f"{RENDER}/bridge_iso.png",                        1600, 90, True),
    "bridge_pict": (f"{BLOG}/r53-kline-bridge/board-pictorial.png",      1500, 80, False),
    "obd":         (f"{BLOG}/r53-kline-bridge/obd2-pin-colours.png",      900, 80, False),
    "log_afr3d":   (f"{BLOG}/r53-logger-august/afr-3d-surface.png",       900, 74, False),
    "log_live":    (f"{BLOG}/r53-logger-august/live-graph-pull.png",      900, 74, False),
    "log_main":    (f"{BLOG}/r53-logger-august/main-screen.png",          900, 74, False),
    "log_flash":   (f"{BLOG}/r53-logger-play-store/flash-options-pedal-fan.jpg", 900, 74, False),
    "log_garage":  (f"{BLOG}/r53-logger-august/garage-which-car.png",     900, 74, False),
    "coding":      (f"{BLOG}/r53-coding/race-seats-workflow.jpg",         900, 74, False),
    "sl_iso":      (f"{RENDER}/shiftlight_iso.png",                      1600, 90, True),
    "sl_top":      (f"{RENDER}/pcb_top.png",                             1600, 90, True),
    "sl_bottom":   (f"{RENDER}/shiftlight_bottom.png",                   1400, 80, True),
    "br_iso":      (f"{RENDER}/bridge_iso.png",                          1600, 90, True),
    "play_badge":  (f"{RENDER}/google-play-badge.png",                    646, 90, True),
}
# lossless: a lossy QR may not scan
PNGS = {"app_qr": f"{BLOG}/r53-shift-light/app-qr.png"}
MODELS = {"stl": (STL, "stl"), "glb": (f"{RENDER}/shiftlight.glb", "glb")}


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for key, (path, maxe, q, alpha) in IMAGES.items():
        im = Image.open(path).convert("RGBA" if alpha else "RGB")
        if alpha and im.getbbox():
            im = im.crop(im.getbbox())
        w, h = im.size
        s = min(1.0, maxe / max(w, h))
        if s < 1.0:
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=q, method=6)
        data = buf.getvalue()
        open(os.path.join(OUT, key + ".webp"), "wb").write(data)
        out[key] = {"uri": "data:image/webp;base64," + base64.b64encode(data).decode(), "ext": "webp"}
        print(f"{key:12s} {im.size[0]:5d}x{im.size[1]:<5d} {len(data)/1024:6.0f} KB")
    for key, path in PNGS.items():
        data = open(path, "rb").read()
        open(os.path.join(OUT, key + ".png"), "wb").write(data)
        out[key] = {"uri": "data:image/png;base64," + base64.b64encode(data).decode(), "ext": "png"}
    for key, (path, ext) in MODELS.items():
        data = open(path, "rb").read()
        name = {"stl": "housing.stl", "glb": "board.glb"}[key]
        open(os.path.join(OUT, name), "wb").write(data)
        out[key] = {"b64": base64.b64encode(data).decode(), "ext": ext}
        print(f"{key:12s} {len(data)/1024:6.0f} KB")
    json.dump(out, open(os.path.join(HERE, "assets.json"), "w"))
    print("assets.json written")


if __name__ == "__main__":
    main()
