#!/usr/bin/env bash
# Publish the R53 shift light page at https://ryansdesigns.geekopolis.com/shiftlight/
# Run once on the VPS as root (sudo). Idempotent: safe to re-run after a re-upload.
#
#   sudo bash ~/r53-site/install.sh
#
# What it does:
#   1. creates /var/www/r53 owned by deploy, so later uploads need no sudo
#   2. copies the staged site from ~deploy/r53-site into it
#   3. adds a static `location ^~ /shiftlight/` to the ryansdesigns nginx server block,
#      ahead of WordPress's `location /`, with a dated backup of the config
#   4. nginx -t, then reload only if the test passes
set -euo pipefail

SRC=/home/deploy/r53-site
DST=/var/www/r53
CONF=/etc/nginx/sites-enabled/ryansdesigns
MARK="# r53-shift-light-site"

[ "$(id -u)" -eq 0 ] || { echo "run with sudo"; exit 1; }
[ -f "$SRC/index.html" ] || { echo "no staged site at $SRC"; exit 1; }

mkdir -p "$DST"
rsync -a --delete --exclude '*.sh' "$SRC/" "$DST/"
chown -R deploy:www-data "$DST"
find "$DST" -type d -exec chmod 755 {} + ; find "$DST" -type f -exec chmod 644 {} +
echo "site copied to $DST ($(du -sh "$DST" | cut -f1))"

if ! grep -q "$MARK" "$CONF"; then
  mkdir -p /etc/nginx/backups
  cp "$CONF" "/etc/nginx/backups/ryansdesigns.$(date +%Y%m%d-%H%M%S)"   # never inside sites-enabled: nginx includes everything there
  # insert before WordPress's catch-all location
  awk -v mark="$MARK" '
    /^\s*location \/ \{/ && !done {
      print "    " mark
      print "    location ^~ /shiftlight/ {"
      print "        alias /var/www/r53/;"
      print "        index index.html;"
      print "        try_files $uri $uri/ =404;"
      print "        location ~* \\.(webp|stl|glb)$ { expires 30d; add_header Cache-Control \"public\"; }"
      print "    }"
      print ""
      done=1
    }
    { print }' "$CONF" > "$CONF.new" && mv "$CONF.new" "$CONF"
  echo "nginx location added"
else
  echo "nginx location already present"
fi

# the STL and GLB need their MIME types or Chrome logs a sniff warning
if ! grep -q "model/gltf-binary" /etc/nginx/mime.types; then
  sed -i 's|^\(\s*\)application/octet-stream\s*bin exe dll;|\1application/octet-stream  bin exe dll;\n\1model/gltf-binary  glb;\n\1model/stl  stl;|' /etc/nginx/mime.types
  echo "mime types added"
fi

nginx -t && systemctl reload nginx && echo "live: https://ryansdesigns.geekopolis.com/shiftlight/"
