#!/usr/bin/env bash
# Imports the site's screenshots and share images from the app repo's store listing build.
#
#   scripts/import-screens.sh <path-to-app-repo>
#
# Reads the unframed captures that `scripts/store/listing-assets.sh` leaves in
# build/store/raw/<device>/<lang>/ and the feature graphics under app/src/main/play/listings/, and
# writes WebP/JPEG copies at the captures' full resolution (with half-size copies for small
# screens) to assets/screens/<lang>/ and assets/og/<lang>.jpg. Needs
# ImageMagick. Run scripts/build.py afterwards.
set -euo pipefail

app=${1:?usage: scripts/import-screens.sh <path-to-app-repo>}
site=$(cd "$(dirname "$0")/.." && pwd)
raw="$app/build/store/raw"
listings="$app/app/src/main/play/listings"
[[ -d $raw ]] || { echo "No captures in $raw: run scripts/store/listing-assets.sh in the app first." >&2; exit 1; }

# Writes $1 as WebP $2 at quality $3, with any further ImageMagick options (a resize) after it.
webp() {
  local in=$1 out=$2 quality=$3
  shift 3
  magick "$in" "$@" -strip -quality "$quality" -define webp:use-sharp-yuv=true "$out"
}

# The app's language tag and the Play listing locale holding its feature graphic.
while IFS=$'\t' read -r lang play _; do
  [[ -z $lang || $lang == \#* ]] && continue
  out="$site/assets/screens/$lang"
  rm -rf "$out" && mkdir -p "$out" "$site/assets/og"
  # Shot files are NN-name.png; the site drops the order prefix. Phones and the tablet get their
  # full capture plus a half-size copy (-sm) for srcset; the TV its full 1920px. sharp-yuv keeps thin
  # coloured text crisp, which plain WebP chroma subsampling blurs.
  for f in "$raw/phone/$lang"/*.png; do
    b=$(basename "$f" .png); b=${b#??-}
    webp "$f" "$out/phone-$b.webp" 92
    webp "$f" "$out/phone-$b-sm.webp" 90 -resize 720x
  done
  for f in "$raw/tv/$lang"/*.png; do
    b=$(basename "$f" .png); b=${b#??-}
    case $b in search | settings) continue ;; esac # Not shown on the site.
    webp "$f" "$out/tv-$b.webp" 95
  done
  webp "$raw/tablet10/$lang/01-home.png" "$out/tablet-home.webp" 92
  webp "$raw/tablet10/$lang/01-home.png" "$out/tablet-home-sm.webp" 90 -resize 1280x
  magick "$listings/$play/graphics/feature-graphic/feature-graphic.png" -strip -quality 88 "$site/assets/og/$lang.jpg"
  echo "import-screens: $lang"
done <"$app/scripts/store/locales.tsv"
