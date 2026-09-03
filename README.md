# R53 shift light — product page

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
scp dist/index.html deploy@2.25.95.177:/var/www/r53/index.html
```

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
- **Google Play badge** — Google's own `en_badge_web_generic.png`.

## Hosting

Nginx on the Hostinger VPS serves `/var/www/r53` at `location ^~ /shiftlight/` inside the
`ryansdesigns.geekopolis.com` server block, ahead of WordPress's catch-all. `deploy` owns the
directory, so uploads need no sudo. Three.js r128 comes from cdnjs and its loaders from
jsdelivr; the fonts from Google Fonts. Everything else is in `dist/`.

## Open items

- Prices: the $125 shift light is confirmed. Housing and bridge are placeholders; the three
  logger unlocks (`appunlock`, `flashunlock`, `oemunlock`) are priced in Play Console and not
  shown yet.
- Photos of the finished products out of the car, and a clip of the bar going to redline.
- Brand: the page says Ryan Racing; the store is Ryan's Designs.
