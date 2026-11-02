# Muslim Haven

Static landing page for [quranradio.app](https://quranradio.app), hosted free on GitHub Pages. The
home page and the privacy policy are published in every language the app speaks: English at `/` and
`/privacy-policy.html`, the others under `/<lang>/`.

## Develop

The pages are generated, so edit the sources, not `index.html`, `privacy-policy.html` or anything
under `<lang>/`:

- `src/home.html`, `src/privacy.html`: the page templates (`{{key}}` placeholders), and
  `src/partials/`: the parts they share (`{{> name}}`), such as the header and footer.
- `i18n/<lang>.json`: each language's text. Headings, the lede and feature text come from the
  app's Play listing and screenshot captions; the rest is the site's own.
- `privacy/<lang>.html`: the privacy policy's text in each language. English is the original; a
  change to it should be carried into every translation.
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

`404.html` is edited by hand.

## Deploy

Pushing to `main` auto-publishes via GitHub Pages. Custom domain is set in `CNAME`.
