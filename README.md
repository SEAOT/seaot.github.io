# SEA OtTeRS & SEAL Lab — team website

Static, multi-page site generated from the team content sheet
(Google Sheet `SEAOtTeRS_SEALLab_website_content`).

- `docs/` — the published site (GitHub Pages serves this folder). Do not edit by hand.
- `gen.py` — generator. Reads `sheet_data.json` + `assets/`, writes `docs/` and `preview.html`.
- `sheet_data.json` — export of the content sheet (People, Publications, Projects, capabilities, News, Team info).
- `assets/` — logos, web-sized photos (`assets/photos/web`), portraits (`assets/photos/people`).
- `content/` — the original intake workbook.

## Update the site

1. Edit the Google Sheet (or ask Claude to re-export it to `sheet_data.json`).
2. `python3 gen.py`
3. `git add -A && git commit -m "Update content" && git push`

GitHub Pages: Settings → Pages → Source "Deploy from a branch", branch `main`, folder `/docs`.
