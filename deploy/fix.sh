#!/usr/bin/env bash
# Repair after the first install.sh: the config backup landed in sites-enabled, where nginx
# includes it as a second copy of the server block. Move it out, restore the symlink if the
# enabled file used to be one, test, reload.
#   sudo bash ~/r53-site/fix.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "run with sudo"; exit 1; }
mkdir -p /etc/nginx/backups
for f in /etc/nginx/sites-enabled/*.bak.*; do [ -e "$f" ] && mv -v "$f" /etc/nginx/backups/; done
if [ -f /etc/nginx/sites-available/ryansdesigns ] && [ ! -L /etc/nginx/sites-enabled/ryansdesigns ]; then
  cp /etc/nginx/sites-enabled/ryansdesigns /etc/nginx/sites-available/ryansdesigns
  ln -sf /etc/nginx/sites-available/ryansdesigns /etc/nginx/sites-enabled/ryansdesigns
  echo "sites-available updated and symlink restored"
fi
nginx -t && systemctl reload nginx
echo "--- live check"
curl -sI https://ryansdesigns.geekopolis.com/shiftlight/ | head -1
curl -sI https://ryansdesigns.geekopolis.com/shiftlight/assets/board.glb | grep -i "HTTP/\|content-type"
curl -sI https://ryansdesigns.geekopolis.com/ | head -1
