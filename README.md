# SEA OtTeRS & SEAL Lab — team website

Website for the research team, covering two working groups:

- **SEA OtTeRS** — Synergy in Extragalactic Astronomy with Observation through Temporal and Redshift Spaces (observational cosmology and extragalactic astronomy)
- **SEAL Lab** — SPDT Engineering, Assembly, and Laser Metrology Laboratory (instrumentation and support technology)

## Structure

Single static page, no build step:

```
index.html   # all markup, CSS and content
README.md
```

Sections (anchors): `#sea-otters`, `#seal-lab`, `#people`, `#projects`, `#publications`, `#news`, `#contact`.

Text shown in *grey italics* in the page (class `placeholder`) marks content still to be filled in.

## Editing

Open `index.html` in any editor. Fonts load from Google Fonts (Newsreader, Source Sans 3, IBM Plex Mono); everything else is self-contained. Colours and type are defined as CSS variables at the top of the `<style>` block; light and dark themes are both supported.

## Publishing on GitHub Pages

```
git remote add origin git@github.com:<user>/<repo>.git
git push -u origin main
```

Then in the repository settings enable **Pages → Deploy from branch → main / (root)**.
