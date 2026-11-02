#!/usr/bin/env bash
# Imports the site's screenshots and share images from the app repo's store listing build.
#
#   scripts/import-screens.sh <path-to-app-repo>
#
# Reads the unframed captures that `scripts/store/listing-assets.sh` leaves in
# build/store/raw/<device>/<lang>/ and the feature graphics under app/src/main/play/listings/, and
# writes WebP/JPEG copies, sharp on 2x screens (the TV shots at their full 1920px, at a quality
# that keeps text crisp), to assets/screens/<lang>/ and assets/og/<lang>.jpg. Needs
# ImageMagick. Run scripts/build.py afterwards.
set -euo pipefail

app=${1:?usage: scripts/import-screens.sh <path-to-app-repo>}
site=$(cd "$(dirname "$0")/.." && pwd)
raw="$app/build/store/raw"
listings="$app/app/src/main/play/listings"
[[ -d $raw ]] || { echo "No captures in $raw: run scripts/store/listing-assets.sh in the app first." >&2; exit 1; }

# The app's language tag and the Play listing locale holding its feature graphic.
while IFS=$'\t' read -r lang play _; do
  [[ -z $lang || $lang == \#* ]] && continue
  out="$site/assets/screens/$lang"
  rm -rf "$out" && mkdir -p "$out" "$site/assets/og"
  # Shot files are NN-name.png; the site drops the order prefix.
  for f in "$raw/phone/$lang"/*.png; do
    b=$(basename "$f" .png); magick "$f" -resize 1080x -strip -quality 90 "$out/phone-${b#??-}.webp"
  done
  for f in "$raw/tv/$lang"/*.png; do
    b=$(basename "$f" .png); b=${b#??-}
    case $b in search | settings) continue ;; esac # Not shown on the site.
    magick "$f" -strip -quality 95 -define webp:sns-strength=0 -define webp:filter-strength=0 "$out/tv-$b.webp"
  done
  magick "$raw/tablet10/$lang/01-home.png" -resize 2048x -strip -quality 90 "$out/tablet-home.webp"
  magick "$listings/$play/graphics/feature-graphic/feature-graphic.png" -strip -quality 88 "$site/assets/og/$lang.jpg"
  echo "import-screens: $lang"
done <"$app/scripts/store/locales.tsv"
