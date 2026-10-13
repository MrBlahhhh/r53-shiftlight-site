# R53 shift light — product page

## Current to-do review — 2026-10-13

Outstanding: confirm housing/bridge prices, shipping and lead time; supply a fully assembled bridge photo and redline clip; settle Ryan Racing versus Ryan's Designs branding. The page already shows logger unlock prices, so adding them is not pending.

The Android tile still says Version 1.5 while source is 1.11. Match the actual published APK and its requirements before updating the tile; source version alone is not proof that a signed customer release has been published. Keep the VPS live and staging copies aligned as documented below.

The page at **https://ryansdesigns.geekopolis.com/shiftlight/**: the printed housing, the
assembled CAN shift light, the free companion app, the R53 Logger · Flasher and the K-line + CAN
bridge, with the housing STL and the carrier board live in Three.js.

> **Not AWS Route 53.** R53 is the chassis code for the 2002–2006 supercharged MINI Cooper S.

## Layout

| | |
|---|---|
| `template.html` | the page. `{{ASSET:key}}` placeholders stand in for every image and model |
| `build.py` | fills the placeholders two ways: `dist/index.html` (files) and `preview.html` (inline) |
| `dist/` | what the server serves. `dist/assets/` is committed so a deploy needs nothing else |
| `deploy/install.sh` | first-time install on the VPS: `/var/www/r53`, the nginx location, MIME types |
| `deploy/fix.sh` | the repair for the first install's misplaced backup; kept for the record |

Not committed: `assets.json` (the packed base64 asset map, ~8 MB, rebuilt by `pack.py`
from the blog checkout and the KiCad exports) and `preview.html` (~9 MB).

## Editing

Edit `template.html`, then:

```sh
python build.py
# assets first, so the new index.html never names a file the server does not have yet
rsync -av dist/assets/ deploy@2.25.95.177:/var/www/r53/assets/
rsync -av dist/index.html deploy@2.25.95.177:/var/www/r53/index.html
# and the same into the staging copy install.sh deploys from
rsync -av dist/assets/ deploy@2.25.95.177:r53-site/assets/
rsync -av dist/index.html deploy@2.25.95.177:r53-site/index.html
```

Keep `~/r53-site` on the server current. `deploy/install.sh` runs
`rsync --delete` from it into `/var/www/r53`, so a stale staging copy puts the old page
back live and deletes anything else in the web root. That happened on 2026-09-29: the
Sep 3 page came back after the no-cache fix. On Windows, which has no rsync, `scp` the
same files to the same places.

New images go in `dist/assets/` as WebP (photos) or PNG (the QR), referenced from the
template as `{{ASSET:name}}`; add the key to `assets.json` if you regenerate the preview.

The hero's LED bar is a port of `shiftlightRender()` from
[esp32-shift-light-R53-mini](https://github.com/MrBlahhhh/esp32-shift-light-R53-mini)
`src/shiftlight.cpp`, with the defaults from `settings.cpp`. If the firmware's fill or blink
logic changes, change `barState()` in the template to match.

## Where the pieces come from

- **Housing model** — the R53 housing STL (105.1 × 23.3 × 54.9 mm). The eight slots were measured
  off the top face: 5.75 mm windows on a 6.64 mm pitch, centred at y 69.98, under a 1.8 mm skin.
  The LEDs in the hero sit under those coordinates.
- **Carrier board** — `r53-shiftlight-carrier.kicad_pcb` from the shift light repo, exported with
  `kicad-cli pcb export glb --subst-models --include-tracks --include-pads --include-zones
  --include-silkscreen --include-soldermask`. glTF is y-up; no rotation is applied.
- **Board renders** — `kicad-cli pcb render`, top and `--perspective --rotate "-35,0,25"`.
- **Photos and screenshots** — `assets/images/r53-shift-light/`, `r53-kline-bridge/`,
  `r53-logger-august/`, `r53-logger-play-store/` in the blog repo.
- **Google Play badge** — Google's own `en_badge_web_generic.png`. Not on the page while the
  logger is in Play closed testing, where the listing is "not found" until you join the testers.

### Rev C product pictures (2026-10-11)

The main CAN and K-line + CAN images are Matt's photographs of the actual red
Rev C boards, kept in `photos/`. The CAN board is assembled; the bridge photo
is labelled as partially assembled. Its original pixels are retained and CSS
rotates it 180 degrees for readable board markings.

The CAN gallery keeps a color CAD top view and the interactive 3D model. Both
come from the committed `dist/assets/board.glb` from `fda212b` (2026-09-03,
“Board renders with the real ESP32 models, rev C boards”). The Blender helper
renders that GLB directly, retaining all KiCad materials and part geometry.
It does not convert through STL, which has no material colors.

- `tools/render_revc.py`: run with Blender's `--background --factory-startup
  --python` options to regenerate the two CAN PNGs in ignored `render/`.
  Optional arguments after `--`: `--can-glb` and `--output`.
- `pack.py`: packages the original photos, the color CAN PNGs, and the frozen
  K-line Rev C `pictures/board-iso.png` for the supplementary bridge render
  assets. Current Rev D files are not used.
- `model-renders.json`: records photo/model input hashes and packaged outputs.
- `build.py`: regenerates hosted and inline pages with content-based asset URLs.

## Hosting

Nginx on the Hostinger VPS serves `/var/www/r53` at `location ^~ /shiftlight/` inside the
`ryansdesigns.geekopolis.com` server block, ahead of WordPress's catch-all. `deploy` owns the
directory, so uploads need no sudo. `index.html` goes out with `Cache-Control: no-cache` and
`/shiftlight` redirects to `/shiftlight/`; both need `deploy/install.sh` re-run on the server
(its v2 block replaces the one from the first install). Three.js r128 comes from cdnjs and its loaders from
jsdelivr; the fonts from Google Fonts. Everything else is in `dist/`.

## Open items

- Prices: the $125 shift light is confirmed. Housing and bridge are placeholders; the three
  logger unlocks (`appunlock`, `flashunlock`, `oemunlock`) are already shown as $25/$50/$50 in template.html. Housing ($19) and bridge ($189) are visible placeholders, not confirmed prices.
- A photo of the fully assembled K-line + CAN bridge, and a clip of the bar going to redline.
- Brand: the page says Ryan Racing; the store is Ryan's Designs.
