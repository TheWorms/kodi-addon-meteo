#!/usr/bin/env bash
#
# Construit le zip installable de l'addon, nommé d'après la version
# déclarée dans weather.meteoconcept/addon.xml.
#
# Usage : ./build.sh
#
set -euo pipefail

ADDON_ID="weather.meteoconcept"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

if [[ ! -f "$ADDON_ID/addon.xml" ]]; then
  echo "Erreur : $ADDON_ID/addon.xml introuvable." >&2
  exit 1
fi

VERSION="$(grep -oE 'version="[0-9]+\.[0-9]+\.[0-9]+"' "$ADDON_ID/addon.xml" \
            | head -1 | sed -E 's/version="([^"]+)"/\1/')"

mkdir -p dist
ZIP="dist/${ADDON_ID}-${VERSION}.zip"
rm -f "$ZIP"

# Nettoyage des caches Python avant packaging
find "$ADDON_ID" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$ADDON_ID" -name "*.pyc" -delete 2>/dev/null || true

# Le zip doit contenir le dossier de l'addon à sa racine
zip -r -q "$ZIP" "$ADDON_ID"

echo "OK -> $ZIP"
