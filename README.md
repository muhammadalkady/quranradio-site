# Muslim Haven

Static landing page for [quranradio.app](https://quranradio.app), hosted free on GitHub Pages. The
home page is published in every language the app speaks: English at `/`, the others at `/<lang>/`.

## Develop

The home pages are generated, so edit the sources, not `index.html` or `<lang>/index.html`:

- `src/home.html`: the page template (`{{key}}` placeholders).
- `i18n/<lang>.json`: each language's text. Headings, the lede and feature text come from the
  app's Play listing and screenshot captions; the rest is the site's own.
- `fonts/src/`: the app's fonts, one face per script, which the build cuts down to the characters
  the pages use.

Then rebuild (fontTools is optional: without it the fonts in `fonts/` are kept as they are):

```sh
pip install fonttools brotli
python3 scripts/build.py
```

To refresh the screenshots and share images from the app repo after it has run
`scripts/store/listing-assets.sh`:

```sh
scripts/import-screens.sh ../QuranRadio2
```

`privacy-policy.html` and `404.html` are edited by hand.

## Deploy

Pushing to `main` auto-publishes via GitHub Pages. Custom domain is set in `CNAME`.
