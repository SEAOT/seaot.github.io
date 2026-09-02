# SEA OtTeRS & SEAL Lab — team website

Website for the research team led by Krittapas Chanchaiworawit, PhD, covering two working groups:

- **SEA OtTeRS** — Synergy in Extragalactic Astronomy with Observation through Temporal and Redshift Spaces (observational cosmology and extragalactic astronomy)
- **SEAL Lab** — SPDT Engineering, Assembly, and Laser Metrology Laboratory (instrumentation and support technology)

## Structure

Static site, no build step:

```
index.html                          # main page (all sections)
people/
  krittapas-chanchaiworawit.html    # PI profile
  template.html                     # copy this for each new member
assets/
  logo-sea-otters.png
  logo-seal-lab.png
```

Main-page anchors: `#sea-otters`, `#seal-lab`, `#people`, `#projects`, `#publications`, `#news`, `#contact`.

Text shown in *grey italics* (class `placeholder`) marks content still to be filled in.

## Adding a member

1. Copy `people/template.html` to `people/firstname-lastname.html`.
2. Fill in name, role, bio, interests, publications and contact; put the CV / résumé PDFs next to the page (e.g. `people/cv_lastname.pdf`) and point the buttons at them.
3. Add a card in the People section of `index.html` linking to the new page.

## Editing the look

Colours and type are CSS variables at the top of each `<style>` block (aquamarine `--sea` for SEA OtTeRS, light blue `--seal` for SEAL Lab). Fonts load from Google Fonts (Manrope, IBM Plex Sans, IBM Plex Mono). Light and dark themes are both supported.

## Publishing on GitHub Pages

```
git remote add origin git@github.com:<user>/<repo>.git
git push -u origin main
```

Then in the repository settings enable **Pages → Deploy from branch → main / (root)**.
