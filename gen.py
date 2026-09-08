#!/usr/bin/env python3
"""Generate the multi-page SEA OtTeRS & SEAL Lab website.

Inputs
  sheet_data.json      exported from the Google Sheet (People, Publications, Projects,
                       SEAL Lab capabilities, News, Team info)
  assets/photos/web    web-sized project/news photos
  assets/photos/people portraits (square)

Outputs
  dist/                real multi-page site (GitHub Pages ready)
  preview.html         single-file preview with all pages + hash routing,
                       images inlined (for the Claude artifact)
"""
import json, os, re, html, base64, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(ROOT, "sheet_data.json")))
T = D["team"]
E = html.escape
UPDATED = datetime.date.today().strftime("%B %-d, %Y")
VERSION = "0.10"

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def para(text):
    parts = [p.strip() for p in str(text).split("\n") if p.strip()]
    return "".join(f"<p>{E(p)}</p>" for p in parts)

def img(key, alt, cls=""):
    return f'<img src="assets/photos/web/{key}.jpg" alt="{E(alt)}" loading="lazy"{" class=%s" % chr(34)+cls+chr(34) if cls else ""}>'

# ---------------------------------------------------------------- data prep
PEOPLE = list(D["people"])
_names = {p["Full name *"] for p in PEOPLE}
for _n in ("That Chomchuen", "Atthaporn Pramoun", "Narenrit Thananusak"):   # members whose sheet row is still empty
    if _n not in _names:
        PEOPLE.append({"Full name *": _n, "Photo link": "x", "Group *": "", "Category *": "", "Position / role *": "", "Short bio (card) *": "", "Email *": "", "_pending": True})
for p in PEOPLE:
    if not str(p.get("Short bio (card) *", "")).strip() and not str(p.get("Long bio (profile page)", "")).strip():
        p["_pending"] = True   # sheet row exists but the bio is not written yet
    for k in ("Position / role *", "Role in the team"):
        p[k] = " ".join(str(p.get(k, "") or "").split()).rstrip(" /·")
    p["slug"] = slug(p["Full name *"])
    p["group"] = {"SEAOtTeRS": "SEA OtTeRS"}.get(str(p.get("Group *", "")).strip(), str(p.get("Group *", "")).strip())
    cat = str(p.get("Category *", "")).replace("Machanical", "Mechanical")
    p["cat"] = cat
    p["section"] = ("Principal Investigator" if cat == "PI" else
                    "Researchers & engineers" if cat in ("Research Assistant", "Mechanical Engineer", "Staff scientist / engineer", "Postdoc") else
                    "Students & interns" if cat in ("Internship Student", "PhD student", "MSc student", "Undergraduate / intern") else
                    "Admin & support" if cat == "Admin" else "New members")
    p["photo"] = f"assets/photos/people/{p['slug']}.jpg" if os.path.exists(os.path.join(ROOT, f"assets/photos/people/{p['slug']}.jpg")) else ""
    p["role"] = str(p.get("Position / role *", "")).replace("Research Assistance", "Research Assistant")

SECTION_ORDER = ["Principal Investigator", "Researchers & engineers", "Students & interns", "Admin & support", "New members"]

PROJECTS = [p for p in D["projects"] if str(p.get("Show on website? *", "Yes")) != "No"]
PROJ_IMG = {"CoLoRS": ("colors_night", "CoLoRS on the 0.7-m Thai Robotic Telescope at NARIT AstroPark"),
            "SPDT": ("spdt_machine", "Precitech Freeform L 5-axis SPDT machine at SEAL Lab"),
            "ARRAKIHS": ("arrakihs", "Simulated ARRAKIHS mock image of a galaxy halo (A. Camazón / ARRAKIHS consortium, CC BY 4.0)"),
            "MACS J1149 RM": ("ultraspec", "ULTRASPEC on the 2.4-m Thai National Telescope"),
            "LRS": ("lrs_tnt", "LRS mounted on the 2.4-m TNT with its cooling system"),
            "ML-HRO": ("mlhro_pred", "Random-forest star-formation rates recovered from photometry versus the SED-fitted values"),
            "MEGARA-LCBG": ("megara_shoc571", "The compact H II galaxy SHOC 571 imaged by Euclid (VIS, Y, J), one of the 26 LCBGs observed with MEGARA"),
            "JWST-SF": ("jwst_map", "Matter-density contrast maps of the JADES GOODS-N and GOODS-S fields with protocluster cores marked"),
            "SDSS-AGN": ("sdss_sample", "Black-hole mass, Eddington ratio, and bolometric luminosity of the SDSS DR17 AGN sample versus redshift"),
            "LAE-z6.5": ("lae_maps", "Mass-density maps of the z = 6.5 protocluster in three redshift slices"),
            "EMIR-HII": ("emir_footprint", "SHOC 571 in Euclid VIS/Y/J imaging with the MEGARA footprint and Hα contours"),
            "AGN-MORPH": ("agnm_n_mbh", "Sérsic index of the inner and outer host components versus black-hole mass, by redshift bin"),
            "PC-NOON": ("pcnoon_method", "The project pipeline: MAST data, SExtractor catalogs, EAZY photometric redshifts, and overdensity and friends-of-friends identification at z = 1.5–3.0"),
            "IFU-SPIN": ("ifu_targets", "SDSS images of the first MEGARA targets with the IFU position angles"),
            "DARTS": ("darts_mirror", "The diamond-turned slit-viewing mirror mounted on the DARTS bench, with its DynaFiz form map"),
            "AM-MIRRORS": ("am_substrates", "Six cast and 3D-printed aluminum substrates before and after single-point diamond turning"),
            "TSC-CUBESAT": ("tsc_align", "MHESI leadership viewing the 6U CubeSat telescope optics under alignment at SEAL Lab"),
            "HARMONI": ("harmoni_eso", "Artist's impression of the HARMONI instrument model for ESO's Extremely Large Telescope")}
# figure-type heroes are shown whole (object-fit: contain) instead of cropped
PROJ_FIG = {"ML-HRO", "JWST-SF", "SDSS-AGN", "LAE-z6.5", "MEGARA-LCBG", "EMIR-HII", "AGN-MORPH", "PC-NOON", "IFU-SPIN", "DARTS", "AM-MIRRORS"}
PROJ_GALLERY = {"CoLoRS": ["colors_night2", "colors_design", "colors_cad"], "LRS": ["lrs_box", "lrs_open", "lrs_model", "lrs_raytrace", "lrs_cooling"],
                "SPDT": ["spdt_action", "dynafiz", "coating", "mirrors", "substrates", "cleanroom", "seal_interior", "seal_team", "zegage"],
                "ARRAKIHS": ["arrakihs_bino", "arrakihs_assembly", "arrakihs_narit"],
                "ML-HRO": ["mlhro_filters", "mlhro_frame"],
                "MEGARA-LCBG": ["megara_kin", "megara_lsig"],
                "JWST-SF": ["jwst_sfms", "jwst_zsfr", "jwst_journey"],
                "SDSS-AGN": ["sdss_grid", "sdss_pca", "sdss_cutouts"],
                "LAE-z6.5": ["lae_spec", "lae_coadd"],
                "AGN-MORPH": ["agnm_model", "agnm_heat"],
                "PC-NOON": ["pcnoon_fields", "jwst_map"],
                "IFU-SPIN": ["ifu_kin", "ifu_select", "jwst_journey", "manga"],
                "DARTS": ["darts_kmirror_lab", "darts_kmirror_cad", "darts_render"],
                "AM-MIRRORS": ["am_lattice", "am_micro", "am_ral"],
                "TSC-CUBESAT": ["tsc_layout", "tsc_6u_mirrors", "tsc_3u_mirror", "tsc_cubesat"],
                "HARMONI": ["spdt_machine2"]}
PROJ_CREDIT = {"ML-HRO": "Figures: G. Cherdchoochavalit & K. Chanchaiworawit, SEA OtTeRS (ISAC 2026).",
               "MEGARA-LCBG": "Figures: Camazón-Pinilla, Guzmán & Chanchaiworawit, A&A (submitted 2026); image: Euclid / MEGARA-GTC.",
               "JWST-SF": "Figures: Chanchaiworawit et al., in preparation (APRIM 2026); data: JWST/JADES and HST.",
               "SDSS-AGN": "Figures: Chanchaiworawit & Sarajedini 2024, ApJ 969, 131; cutouts: SDSS.",
               "LAE-z6.5": "Figures: Chanchaiworawit et al. 2019, ApJ 877, 51; Calvi et al. 2019, MNRAS 489, 3294 (GTC/OSIRIS).",
               "ARRAKIHS": "Images: A. Camazón (IEEC) / ARRAKIHS Mission Consortium, CC BY 4.0; Satlantis / ARRAKIHS Mission Consortium; NARIT (news, 12 Jun 2026).",
               "EMIR-HII": "Figure: SEA OtTeRS / NARIT; imaging ESA/Euclid.",
               "AGN-MORPH": "Figures: T. Klipbua, K. Chanchaiworawit & V. Sarajedini, APRIM 2026 talk; data: SDSS.",
               "PC-NOON": "Flowchart: A. Pramoun, senior-project proposal (2026); PASSAGE field map: Huberty et al. 2026, ApJS 284, 64; density maps: Chanchaiworawit et al., in preparation.",
               "IFU-SPIN": "Figures: SEA OtTeRS / NARIT; SDSS imaging; MaNGA illustration: Dana Berry / SkyWorks Digital, David Law, and the SDSS collaboration (CC BY).",
               "DARTS": "Photos: SEAL Lab / NARIT; K-mirror photo and drawings: NARIT.",
               "AM-MIRRORS": "Photos and figures: SEAL Lab / NARIT with UK ATC; lattice substrate design and fabrication: UK ATC.",
               "TSC-CUBESAT": "Photos and drawings: SEAL Lab / NARIT / Thai Space Consortium; CubeSat render: NARIT.",
               "HARMONI": "HARMONI model: ESO (CC BY 4.0); machine photo: SEAL Lab / NARIT.",
               "CoLoRS": "Photos: SEA OtTeRS / NARIT.", "LRS": "Photos and drawings: SEA OtTeRS / NARIT.", "SPDT": "Photos: SEAL Lab / NARIT.",
               "MACS J1149 RM": "Photo: NARIT."}
for p in PROJECTS:
    p["short"] = str(p["Short name *"]).strip()
    p["slug"] = slug(p["short"])
    p["img"], p["imgalt"] = PROJ_IMG.get(p["short"], ("tno_night", "NARIT facilities"))
    p["order"] = float(p.get("Order on page") or 99)
PROJECTS.sort(key=lambda p: p["order"])
THEMES = [t for t in D.get("themes", []) if str(t.get("Show on website? *", "Yes")) != "No"]
for t in THEMES:
    t["key"] = str(t["Short name *"]).strip(); t["slug"] = "theme-" + slug(t["key"]); t["order"] = float(t.get("Order") or 99)
    t["projects"] = sorted([p for p in PROJECTS if str(p.get("Research theme *", "")).strip() == t["key"]], key=lambda p: float(p.get("Theme order") or 99))
THEMES.sort(key=lambda t: t["order"])
def themes_of(group): return [t for t in THEMES if t["Group *"] == group]
for p in PROJECTS:
    p["full"] = p["short"] in PROJ_IMG and bool(str(p.get("Description", "") or "").strip() or str(p.get("Key numbers", "") or "").strip())

NEWS = sorted(D["news"], key=lambda n: str(n["Date *"]), reverse=True)
NEWS_IMG = {"SEA-SPARC": "seasparc", "ESA adopts": "arrakihs", "ThaiPASS 2026": "thaipass26", "ThaiPASS 2025": "thaipass25",
            "ThaiPASS 2024": "thaipass24", "CoLoRS": "colors_night", "JDAP": "jdap", "EAYAM": "eayam",
            "ASTRO101": "how", "FOAMAS": "foamas", "website": "hero_lrs"}
for n in NEWS:
    n["date"] = str(n["Date *"])[:10]
    n["img"] = next((v for k, v in NEWS_IMG.items() if k in n["Headline *"]), "tno_night")

PUBS = D["pubs"]
for p in PUBS:
    p["year"] = int(float(p["Year *"]))
PUBS.sort(key=lambda p: (-p["year"], p["Type *"]))
SELECTED = [p for p in PUBS if str(p.get("Show in 'Selected papers'? *")) == "Yes"]
CAPS = [c for c in D["caps"] if str(c.get("Show on website? *", "Yes")) != "No"]

# papers per year (NASA ADS "Years" export, total/refereed), from the CV
YEARS = [(2016,1,0),(2017,1,1),(2018,2,1),(2019,3,2),(2020,3,1),(2021,0,0),(2022,1,0),(2023,0,0),(2024,1,1),(2025,17,0),(2026,17,4)]

PAGES = [  # (slug, nav label, title, status)
    ("index", "Home", "SEAL × OTTER", "Live"),
    ("sea-otters", "SEA OtTeRS", "SEA OtTeRS", "Live"),
    ("seal-lab", "SEAL Lab", "SEAL Lab", "Live"),
    ("people", "People", "People", "Live"),
    ("projects", "Projects", "Projects & Facilities", "Live"),
    ("publications", "Publications", "Publications", "Live"),
    ("news", "News", "News & Events", "Live"),
    ("contact", "Contact", "Contact for collaborations", "Planned"),
    ("internships", "Internships", "Internship application", "Planned"),
    ("shop", "Shop", "Merchandise shop", "Planned"),
]

# ---------------------------------------------------------------- CSS
CSS = r"""
:root {
  --bg:#FFFFFF; --bg-2:#F4F7F8; --bg-3:#EAEFF1; --ink:#111315; --ink-2:#3D4349; --muted:#6E767D; --rule:#E3E7EA;
  --sea:#1A9C86; --sea-soft:#E4F5F1; --seal:#2F86C9; --seal-soft:#E5F0FA; --gold:#C98A1F; --gold-soft:#FBF1DE; --link:#1A9C86;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace; --display:"Manrope","Helvetica Neue",Arial,sans-serif; --sans:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  --max:1140px; --measure:64ch;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --bg:#0F1214; --bg-2:#171B1E; --bg-3:#1F2529; --ink:#F2F4F5; --ink-2:#C5CACE; --muted:#868E95; --rule:#272D32; --sea:#4FD1B8; --sea-soft:#12312B; --seal:#6FB4EA; --seal-soft:#14283A; --gold:#E2AE55; --gold-soft:#3A2B10; --link:#4FD1B8; } }
:root[data-theme="dark"]{ --bg:#0F1214; --bg-2:#171B1E; --bg-3:#1F2529; --ink:#F2F4F5; --ink-2:#C5CACE; --muted:#868E95; --rule:#272D32; --sea:#4FD1B8; --sea-soft:#12312B; --seal:#6FB4EA; --seal-soft:#14283A; --gold:#E2AE55; --gold-soft:#3A2B10; --link:#4FD1B8; }
*{box-sizing:border-box}
html{scroll-behavior:smooth} @media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:16.5px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none} a:hover{text-decoration:underline;text-underline-offset:3px}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid var(--sea);outline-offset:3px}
h1,h2,h3,h4{font-family:var(--display);font-weight:600;line-height:1.12;margin:0;text-wrap:balance;letter-spacing:-0.02em}
h1{font-size:clamp(2.2rem,4.4vw,3.2rem);letter-spacing:-0.03em;font-weight:700} h2{font-size:clamp(1.6rem,2.8vw,2.1rem)} h3{font-size:1.2rem;letter-spacing:-0.01em} h4{font-size:1rem}
p{margin:0} img{max-width:100%;display:block}
.wrap{max-width:var(--max);margin:0 auto;padding:0 24px}
.mono{font-family:var(--mono);font-size:.85em}
.eyebrow{font-size:.76rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.eyebrow.sea{color:var(--sea)} .eyebrow.seal{color:var(--seal)} .eyebrow.gold{color:var(--gold)}
.measure{max-width:var(--measure)} .muted{color:var(--muted)} .ink2{color:var(--ink-2)}
.pill{display:inline-block;font-family:var(--mono);font-size:.74rem;padding:2px 9px;border-radius:999px;background:var(--bg-3);color:var(--ink-2);white-space:nowrap}
.pill.sea{background:var(--sea-soft);color:var(--sea)} .pill.seal{background:var(--seal-soft);color:var(--seal)} .pill.gold{background:var(--gold-soft);color:var(--gold)}
.chips{display:flex;flex-wrap:wrap;gap:6px} .chips .pill{white-space:normal}
.btn{display:inline-block;font-weight:600;padding:10px 16px;border-radius:6px;border:1px solid var(--rule);color:var(--ink);background:var(--bg)}
.btn:hover{background:var(--bg-2);text-decoration:none} .btn.primary{background:var(--ink);color:var(--bg);border-color:var(--ink)} .btn.primary:hover{opacity:.9}
.btn.sea{background:var(--sea);border-color:var(--sea);color:#fff} .btn.seal{background:var(--seal);border-color:var(--seal);color:#fff}
/* nav */
.nav{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
.nav .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px;height:60px}
.brand{font-family:var(--display);font-weight:700;font-size:1.02rem;letter-spacing:-0.01em;color:var(--ink);display:flex;align-items:center;gap:10px;white-space:nowrap}
.brand img.mark{width:34px;height:34px;object-fit:contain} .brand .x{color:var(--seal);font-weight:800;margin:0 2px} .brand:hover{text-decoration:none}
.nav ul{list-style:none;margin:0;padding:0;display:flex;gap:18px;font-size:.92rem;font-weight:500;flex-wrap:wrap;justify-content:flex-end}
.nav ul a{color:var(--ink-2);padding:4px 0;border-bottom:2px solid transparent} .nav ul a:hover{color:var(--ink);text-decoration:none}
.nav ul a.active{color:var(--ink);border-bottom-color:var(--sea)} .nav ul a.soon::after{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--gold);margin-left:5px;vertical-align:middle}
.nav .menu{display:none;border:1px solid var(--rule);background:var(--bg);border-radius:6px;padding:6px 10px;font:inherit;color:var(--ink)}
@media (max-width:900px){.nav ul{display:none;position:absolute;left:0;right:0;top:60px;background:var(--bg);border-bottom:1px solid var(--rule);padding:12px 24px 16px;flex-direction:column;gap:10px} .nav ul.open{display:flex} .nav .menu{display:block}}
/* status notices */
.notice{background:var(--gold-soft);border-bottom:1px solid color-mix(in srgb,var(--gold) 35%,transparent);font-size:.86rem;color:var(--ink-2)}
.notice .wrap{display:flex;gap:12px;align-items:center;justify-content:space-between;padding-top:8px;padding-bottom:8px}
.notice b{color:var(--ink)} .notice button{font:inherit;font-size:.8rem;background:none;border:1px solid var(--rule);border-radius:4px;padding:3px 8px;color:var(--ink-2);cursor:pointer;white-space:nowrap} .notice[hidden]{display:none}
.wip{border:1px solid color-mix(in srgb,var(--gold) 45%,transparent);border-left:4px solid var(--gold);border-radius:6px;padding:16px 18px;background:var(--gold-soft);display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:start}
.wip .ic{width:34px;height:34px;border-radius:50%;background:var(--gold);color:#fff;display:grid;place-items:center;font-family:var(--display);font-weight:800;font-size:1.1rem}
.wip h3{font-size:1rem} .wip p{font-size:.92rem;color:var(--ink-2);margin-top:4px} .wip ul{margin:8px 0 0;padding-left:18px;font-size:.9rem;color:var(--ink-2)} .wip li{margin:2px 0}
.wip .st{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.pill.ready{background:var(--sea-soft);color:var(--sea)} .pill.todo{background:var(--bg-3);color:var(--muted)}
.form.off{opacity:.6} .form.off input,.form.off select,.form.off textarea{background:var(--bg-2);cursor:not-allowed}
.stub{font-size:.88rem;color:var(--muted);font-style:italic}
.stub::before{content:"○ ";color:var(--gold);font-style:normal}
/* page frame */
.page{display:block} .page[hidden]{display:none}
.pagehead{padding:56px 0 28px} .pagehead h1{margin-top:8px} .pagehead .lede{font-size:1.18rem;color:var(--ink-2);margin-top:14px;max-width:62ch;line-height:1.5}
section{padding:56px 0;border-top:1px solid var(--rule)} section.flush{border-top:0;padding-top:0}
.sec-head{display:grid;grid-template-columns:1fr 2fr;gap:28px;align-items:start;margin-bottom:28px} @media (max-width:760px){.sec-head{grid-template-columns:1fr;gap:10px}}
.sec-head p{color:var(--ink-2);max-width:var(--measure)}
.group{--g:var(--sea);--g-soft:var(--sea-soft)} .group.seal{--g:var(--seal);--g-soft:var(--seal-soft)} .group.gold{--g:var(--gold);--g-soft:var(--gold-soft)}
.group h2{position:relative;padding-left:18px} .group h2::before{content:"";position:absolute;left:0;top:.2em;bottom:.2em;width:4px;background:var(--g)}
/* hero */
.hero{padding:48px 0 32px} .hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:36px;align-items:center} @media (max-width:860px){.hero-grid{grid-template-columns:1fr}}
.hero .lede{font-size:1.2rem;color:var(--ink-2);line-height:1.5;margin-top:18px;max-width:56ch}
.hero .org{margin-top:22px;font-size:.92rem;color:var(--muted);display:flex;gap:16px;flex-wrap:wrap}
.hero .cta{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}
.hero-logo{display:grid;place-items:center} .hero-logo img{width:min(100%,460px);aspect-ratio:1} .hero-photo{position:relative;border-radius:8px;overflow:hidden;aspect-ratio:4/3;background:var(--bg-2)} .hero-photo img{width:100%;height:100%;object-fit:cover}
.hero-photo .cap{position:absolute;left:0;right:0;bottom:0;padding:10px 14px;font-size:.78rem;color:#fff;background:linear-gradient(transparent,rgba(0,0,0,.55))}
.doors{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:36px} @media (max-width:760px){.doors{grid-template-columns:1fr}}
.door{display:grid;grid-template-columns:64px 1fr;gap:16px;color:var(--ink);border:1px solid var(--rule);border-top:3px solid var(--door);border-radius:6px;padding:22px 22px 24px;background:var(--bg);transition:background .15s}
.door:hover{background:var(--bg-2);text-decoration:none} .door.sea{--door:var(--sea)} .door.seal{--door:var(--seal)}
.door img{width:110px;height:110px;object-fit:contain} .gbadge{width:132px;height:132px;object-fit:contain;display:block;margin-bottom:14px} .door .acronym{font-family:var(--display);font-size:1.6rem;font-weight:700;letter-spacing:-0.02em}
.door .expands{color:var(--ink-2);margin-top:4px;font-size:.95rem;line-height:1.4} .door .go{display:inline-block;margin-top:12px;font-weight:600;color:var(--door)}
/* stats */
.stats{display:grid;grid-template-columns:repeat(6,1fr);border:1px solid var(--rule);border-radius:6px;overflow:hidden;background:var(--bg-2)} @media (max-width:980px){.stats{grid-template-columns:repeat(3,1fr)}} @media (max-width:560px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{padding:18px 18px 16px;border-right:1px solid var(--rule);border-bottom:1px solid var(--rule)} .stat .n{font-family:var(--display);font-size:2rem;font-weight:700;letter-spacing:-0.03em;line-height:1;font-variant-numeric:tabular-nums;color:var(--c,var(--ink))}
.stat .l{font-size:.86rem;color:var(--ink-2);margin-top:8px;line-height:1.35} .stat.sea{--c:var(--sea)} .stat.seal{--c:var(--seal)} .stat.gold{--c:var(--gold)}
/* pipeline infographic */
.pipe{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:8px;position:relative} @media (max-width:760px){.pipe{grid-template-columns:1fr 1fr}}
.pipe .step{padding:18px 18px 18px 0;border-top:3px solid var(--c);margin-right:18px} .pipe .step:last-child{margin-right:0}
.pipe .step .k{font-family:var(--mono);font-size:.74rem;color:var(--c);letter-spacing:.06em} .pipe .step h3{margin-top:8px;font-size:1.05rem} .pipe .step p{font-size:.92rem;color:var(--ink-2);margin-top:6px}
.pipe .step.sea{--c:var(--sea)} .pipe .step.seal{--c:var(--seal)} .pipe .step.mix{--c:var(--gold)}
/* cards */
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px} @media (max-width:900px){.cards{grid-template-columns:1fr 1fr}} @media (max-width:600px){.cards{grid-template-columns:1fr}}
.cards.two{grid-template-columns:1fr 1fr} @media (max-width:700px){.cards.two{grid-template-columns:1fr}}
.card{display:flex;flex-direction:column;border:1px solid var(--rule);border-radius:6px;overflow:hidden;background:var(--bg);color:var(--ink)}
a.card:hover{text-decoration:none;background:var(--bg-2)} .card .ph{aspect-ratio:16/10;background:var(--bg-3);overflow:hidden} .card .ph img{width:100%;height:100%;object-fit:cover}
.card .ph.tall{aspect-ratio:3/4} .card .body{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1} .card h3{font-size:1.08rem} .card p{font-size:.94rem;color:var(--ink-2)}
.card .meta{display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:.8rem;color:var(--muted);margin-top:auto;padding-top:6px}
/* people */
.people{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:22px}
.person{display:grid;grid-template-columns:72px 1fr;gap:14px;align-items:start;color:var(--ink)} a.person:hover{text-decoration:none} a.person:hover .name{text-decoration:underline;text-underline-offset:3px}
.avatar{width:72px;height:72px;border-radius:50%;object-fit:cover;background:var(--bg-2);border:1px solid var(--rule)} .avatar.init{display:grid;place-items:center;font-family:var(--display);font-weight:700;color:var(--muted)}
.person .name{font-family:var(--display);font-weight:600;font-size:1.02rem;letter-spacing:-0.01em} .person .role{font-size:.88rem;color:var(--ink-2);margin-top:2px;line-height:1.35} .person .bio{font-size:.86rem;color:var(--muted);margin-top:6px}
.profile{display:grid;grid-template-columns:260px 1fr;gap:40px;align-items:start} @media (max-width:760px){.profile{grid-template-columns:1fr}}
.profile .side img{width:100%;border-radius:8px} .profile .side .links{display:flex;flex-direction:column;gap:8px;margin-top:16px;font-size:.92rem}
.profile .main{min-width:0} .profile .main p{margin-top:12px;color:var(--ink-2)} .profile .main p:first-child{margin-top:0}
.kv{display:grid;grid-template-columns:140px 1fr;gap:6px 14px;font-size:.92rem;margin-top:20px} .kv dt{color:var(--muted)} .kv dd{margin:0}
/* tables */
.tbl{width:100%;border-collapse:collapse;font-size:.93rem} .tbl th{text-align:left;font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;color:var(--muted);font-weight:500;padding:8px 10px;border-bottom:1px solid var(--rule)}
.tbl td{padding:10px;border-bottom:1px solid var(--rule);vertical-align:top} .tbl td.v{font-family:var(--mono);font-size:.86rem;white-space:nowrap;color:var(--g,var(--ink))}
.scroll{overflow-x:auto}
/* publications */
.pub{display:grid;grid-template-columns:64px 1fr;gap:14px;padding:14px 0;border-bottom:1px solid var(--rule)} .pub .y{font-family:var(--mono);color:var(--muted);font-size:.9rem;padding-top:3px}
.pub .t{font-weight:600} .pub .a{color:var(--ink-2);font-size:.92rem;margin-top:2px} .pub .v{font-size:.88rem;color:var(--muted);margin-top:2px} .pub .v b{color:var(--ink-2);font-weight:600}
.chart{border:1px solid var(--rule);border-radius:6px;padding:16px 18px;background:var(--bg-2)} .chart svg{width:100%;height:auto;display:block} .chart .leg{display:flex;gap:16px;font-size:.8rem;color:var(--ink-2);margin-top:8px}
.leg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
/* news */
.timeline{display:grid;gap:0} .item{display:grid;grid-template-columns:120px 1fr 200px;gap:20px;padding:20px 0;border-bottom:1px solid var(--rule);align-items:start} @media (max-width:760px){.item{grid-template-columns:1fr}}
.item .d{font-family:var(--mono);font-size:.86rem;color:var(--muted);padding-top:3px} .item h3{font-size:1.08rem} .item p{color:var(--ink-2);font-size:.95rem;margin-top:6px} .item .ph{aspect-ratio:16/10;border-radius:6px;overflow:hidden;background:var(--bg-3)} .item .ph img{width:100%;height:100%;object-fit:cover}
/* project detail */
.pj{display:grid;grid-template-columns:1.1fr .9fr;gap:32px;align-items:start;padding:32px 0;border-top:1px solid var(--rule)} @media (max-width:800px){.pj{grid-template-columns:1fr}}
.pj .ph{border-radius:8px;overflow:hidden;aspect-ratio:16/10;background:var(--bg-3)} .pj .ph img{width:100%;height:100%;object-fit:cover} .pj .gal{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px} .pj .gal img{aspect-ratio:4/3;object-fit:cover;border-radius:4px;width:100%} .pj .ph.fig{aspect-ratio:auto;background:#fff} .pj .ph.fig img{object-fit:contain;height:auto} .pj .gal a{display:block} .pj .fig+.gal img{object-fit:contain;background:#fff;border:1px solid var(--rule)} .pj .cap{font-size:.74rem;color:var(--muted);margin-top:8px;line-height:1.45} .tgrid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px} .tidx{border-left:3px solid var(--sea);padding:2px 0 2px 16px} .tidx.seal{border-color:var(--seal)} .tidx ul{list-style:none;padding:0;margin:8px 0 0} .tidx li{padding:3px 0} .tidx a{font-weight:600;text-decoration:none;color:var(--ink)} .tidx a:hover{text-decoration:underline}
.theme{padding:34px 0 8px;border-top:1px solid var(--rule)} .theme .th{max-width:760px;margin-bottom:6px} .theme .th h2{font-size:1.7rem;margin:6px 0 8px} .theme .th .lede{font-size:1.02rem;margin-bottom:12px}
.pjs{border:1px solid var(--rule);border-radius:10px;padding:18px 20px;margin:14px 0;background:var(--bg-2)} .pjs h3{margin:10px 0 4px;font-size:1.12rem} .pjs .sum{margin:0 0 6px} .pjs .meta{font-size:.9rem;color:var(--ink-2);display:flex;flex-wrap:wrap;gap:6px 18px;margin:0 0 6px} .pjs .meta b{font-weight:600;color:var(--muted)} .pjs .stub{font-size:.86rem;color:var(--muted);font-style:italic;margin:6px 0 0}
@media(max-width:720px){.tgrid{grid-template-columns:1fr}}
.pj>div{min-width:0} .pj h3{font-size:1.35rem} .pj .sum{color:var(--ink-2);margin-top:8px} .pj .desc p{color:var(--ink-2);font-size:.95rem;margin-top:10px} .pj .facts{display:grid;grid-template-columns:110px 1fr;gap:4px 12px;font-size:.9rem;margin-top:14px} .pj .facts dt{color:var(--muted)} .pj .facts dd{margin:0}
/* forms & planned */
.planned{border:1px dashed var(--gold);background:var(--gold-soft);border-radius:6px;padding:12px 16px;font-size:.92rem;color:var(--ink-2);display:flex;gap:12px;align-items:flex-start}
.form{display:grid;gap:14px;max-width:640px} .form label{display:grid;gap:6px;font-size:.9rem;font-weight:500} .form input,.form select,.form textarea{font:inherit;padding:10px 12px;border:1px solid var(--rule);border-radius:6px;background:var(--bg);color:var(--ink)} .form textarea{min-height:120px} .form .row{display:grid;grid-template-columns:1fr 1fr;gap:14px} @media (max-width:600px){.form .row{grid-template-columns:1fr}}
.contactgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px} @media (max-width:800px){.contactgrid{grid-template-columns:1fr}}
.cbox{border:1px solid var(--rule);border-top:3px solid var(--c,var(--ink));border-radius:6px;padding:18px 20px} .cbox.sea{--c:var(--sea)} .cbox.seal{--c:var(--seal)} .cbox.gold{--c:var(--gold)} .cbox h3{font-size:1.05rem} .cbox p{font-size:.92rem;color:var(--ink-2);margin-top:6px} .cbox .mono{display:block;margin-top:8px}
.shop{display:grid;grid-template-columns:repeat(4,1fr);gap:18px} @media (max-width:900px){.shop{grid-template-columns:1fr 1fr}} .shop .card .ph{aspect-ratio:1;display:grid;place-items:center;font-family:var(--display);font-weight:700;color:var(--muted);font-size:1.4rem}
.fund{display:grid;grid-template-columns:1fr 1fr;gap:24px;border:1px solid var(--rule);border-radius:6px;padding:24px;margin-top:28px;background:var(--bg-2)} @media (max-width:760px){.fund{grid-template-columns:1fr}} .fund .big{font-family:var(--display);font-size:2rem;font-weight:700;letter-spacing:-0.03em;color:var(--gold)}
/* footer */
footer{border-top:1px solid var(--rule);padding:40px 0 48px;color:var(--muted);font-size:.9rem} .fgrid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:24px} @media (max-width:760px){.fgrid{grid-template-columns:1fr 1fr}} footer ul{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:6px} footer a{color:var(--ink-2)} footer .fh{font-weight:600;color:var(--ink);font-size:.9rem}
"""

# ---------------------------------------------------------------- page pieces
def nav(active, mode):
    def href(s): return f"#/{s}" if mode == "preview" else (f"{s}.html" if s != "index" else "index.html")
    items = "".join(f'<li><a href="{href(s)}" class="{"active " if s == active else ""}{"soon" if st == "Planned" else ""}" data-nav="{s}"{" title=%sIn preparation — draft page%s" % (chr(34), chr(34)) if st == "Planned" else ""}>{E(lbl)}</a></li>' for s, lbl, _, st in PAGES)
    return f'''<header class="nav"><div class="wrap">
<a class="brand" href="{href("index")}"><img src="assets/logo-sealxotter-320.png" alt="" class="mark"><span>SEAL <span class="x">×</span> OTTER</span></a>
<button class="menu" aria-label="Menu" onclick="this.nextElementSibling.classList.toggle('open')">Menu</button>
<ul>{items}</ul></div></header>
<div class="notice" id="notice"><div class="wrap"><span><b>Early release.</b> This site is being published in stages. Pages with a <span style="color:var(--gold)">●</span> in the menu are drafts; everything else is checked by the team as of {UPDATED}. Spotted an error? <a href="mailto:{E(T["SEA OtTeRS – contact email"])}">Tell us</a>.</span><button type="button" onclick="document.getElementById('notice').hidden=true;try{{localStorage.setItem('sxo-notice','1')}}catch(e){{}}">Got it</button></div></div>
<script>try{{if(localStorage.getItem('sxo-notice'))document.getElementById('notice').hidden=true}}catch(e){{}}</script>'''

def footer(mode):
    def href(s): return f"#/{s}" if mode == "preview" else f"{s}.html"
    return f'''<footer><div class="wrap"><div class="fgrid">
<div><div class="fh">SEAL × OTTER · {E(T["Institute / host organisation"])}</div><p style="margin-top:8px">{E(T["Postal address"])}</p>
<p style="margin-top:8px">SEA OtTeRS: <a href="mailto:{E(T["SEA OtTeRS – contact email"])}">{E(T["SEA OtTeRS – contact email"])}</a><br>SEAL Lab: <a href="mailto:{E(T["SEAL Lab – contact email"])}">{E(T["SEAL Lab – contact email"])}</a></p></div>
<div><div class="fh">Groups</div><ul><li><a href="{href("sea-otters")}">SEA OtTeRS</a></li><li><a href="{href("seal-lab")}">SEAL Lab</a></li><li><a href="{href("people")}">People</a></li></ul></div>
<div><div class="fh">Work</div><ul><li><a href="{href("projects")}">Projects &amp; facilities</a></li><li><a href="{href("publications")}">Publications</a></li><li><a href="{href("news")}">News &amp; events</a></li></ul></div>
<div><div class="fh">Get involved</div><ul><li><a href="{href("contact")}">Collaborate</a></li><li><a href="{href("internships")}">Internships</a></li><li><a href="{href("shop")}">Shop for the team fund</a></li><li><a href="{E(T["GitHub repository URL"])}">Site source</a></li></ul></div>
</div><p style="margin-top:28px">© {datetime.date.today().year} SEAL × OTTER — SEA OtTeRS &amp; SEAL Lab, NARIT · sealxotter.org. Photos: NARIT, SEA OtTeRS/SEAL Lab, ESA/ARRAKIHS consortium (CC BY 4.0 where noted). Site version {VERSION}, content last verified {UPDATED}. Generated from the team content sheet — <a href="mailto:{E(T["SEA OtTeRS – contact email"])}?subject=Website%20correction">report a correction</a>.</p></div></footer>'''

def L(mode, s, anchor=""):
    return (f"#/{s}" + (f"/{anchor}" if anchor else "")) if mode == "preview" else (f"{s}.html" + (f"#{anchor}" if anchor else ""))

def person_card(p, mode):
    ph = f'<img class="avatar" src="{p["photo"]}" alt="">' if p["photo"] else f'<div class="avatar init">{E("".join(w[0] for w in p["Full name *"].split()[:2]))}</div>'
    role = p["role"] or ("Profile in preparation" if p.get("_pending") else p["cat"])
    bio = str(p.get("Short bio (card) *", ""))
    return f'''<a class="person" href="{L(mode, "people", p["slug"]) if mode == "preview" else f"people/{p['slug']}.html"}">{ph}<div><div class="name">{E(p["Full name *"])}{(" · " + E(str(p["Degree / title"]))) if p.get("Degree / title") else ""}</div><div class="role">{E(role)}</div>{f'<div class="bio">{E(bio[:140])}{"…" if len(bio) > 140 else ""}</div>' if bio else ""}</div></a>'''

def project_card(p, mode):
    g = "sea" if p["Group *"] == "SEA OtTeRS" else "seal"
    return f'''<a class="card" href="{L(mode, "projects", p["slug"])}"><div class="ph">{img(p["img"], p["imgalt"])}</div><div class="body"><span class="pill {g}">{E(p["short"])}</span><h3>{E(p["Project name *"])}</h3><p>{E(p["One-line summary *"])}</p><div class="meta"><span>{E(p["Type *"])}</span><span>{E(p["Status *"])}</span></div></div></a>'''

def news_card(n, mode):
    return f'''<a class="card" href="{L(mode, "news", "n-" + n["date"])}"><div class="ph">{img(n["img"], n["Headline *"])}</div><div class="body"><span class="mono muted">{n["date"]}</span><h3>{E(n["Headline *"])}</h3><p>{E(str(n["Text *"])[:150])}{"…" if len(str(n["Text *"])) > 150 else ""}</p></div></a>'''

# ---------------------------------------------------------------- pages
def page_index(mode):
    stats = [("2", "research groups, one team", "sea"), ("3", "instruments &amp; capabilities built: CoLoRS, LRS, SPDT line", "seal"), ("46", "publications on ADS, 10 refereed", ""),
             (str(len(PEOPLE)), "team members and students", ""), ("8", "workshops &amp; conferences organized since 2023", ""), ("1", "ESA mission — ARRAKIHS, first Thai institute", "gold")]
    stats_html = "".join(f'<div class="stat {c}"><div class="n">{n}</div><div class="l">{l}</div></div>' for n, l, c in stats)
    feat = [p for p in PROJECTS if p["short"] in ("CoLoRS", "SPDT", "ARRAKIHS")]
    return f'''
<div class="hero"><div class="wrap"><div class="hero-grid"><div>
<div class="eyebrow">SEAL × OTTER · {E(T["City, country"])} · {E(T["Institute / host organisation"])}</div>
<h1>Extragalactic astronomy, astronomical instrumentation, and precision optics.</h1>
<p class="lede"><b>{E(T["Team tagline (one sentence)"])}</b> {E(T["Team intro paragraph"])}</p>
<div class="cta"><a class="btn sea" href="{L(mode,"sea-otters")}">Explore SEA OtTeRS</a><a class="btn seal" href="{L(mode,"seal-lab")}">Visit SEAL Lab</a><a class="btn" href="{L(mode,"contact")}">Collaborate with us</a></div>
</div>
<div class="hero-logo"><img src="assets/logo-sealxotter.png" alt="SEAL × OTTER — an otter and a seal in spacesuits aligning a mirror with a laser, under a telescope dome and a spiral galaxy"></div>
</div>
<div class="doors">
<a class="door sea" href="{L(mode,"sea-otters")}"><img src="assets/logo-sea-otters.png" alt=""><div><div class="eyebrow sea">Research group</div><div class="acronym">SEA OtTeRS</div><div class="expands">Synergy in Extragalactic Astronomy with Observation through Temporal and Redshift Spaces</div><span class="go">Galaxies, AGN, time-domain astronomy and the spectrographs that serve them →</span></div></a>
<a class="door seal" href="{L(mode,"seal-lab")}"><img src="assets/logo-seal-lab.png" alt=""><div><div class="eyebrow seal">Engineering group</div><div class="acronym">SEAL Lab</div><div class="expands">SPDT Engineering, Assembly, and Laser Metrology Laboratory</div><span class="go">Ultra-precision metallic and freeform optics for astronomy and space →</span></div></a>
</div></div></div>

<section><div class="wrap"><div class="eyebrow">The team in numbers</div><div class="stats" style="margin-top:14px">{stats_html}</div></div></section>

<section><div class="wrap"><div class="sec-head"><h2>One team, two workshops</h2><p>SEAL × OTTER is the joint effort of SEA OtTeRS and SEAL Lab: one loop from the sky to the instrument and back. SEA OtTeRS defines the science and the observing cadence; the instruments it needs are designed, machined, and measured at SEAL Lab; the optics then go back on the telescopes, where the next survey begins.</p></div>
<div class="pipe">
<div class="step sea"><div class="k">01 · OBSERVE</div><h3>Telescopes</h3><p>2.4-m TNT, the 0.7-m TRT network across four continents, GTC, JWST and SDSS archives.</p></div>
<div class="step sea"><div class="k">02 · ANALYZE</div><h3>Science</h3><p>Galaxy evolution at high redshift, AGN variability and reverberation mapping, machine-learning inference on survey data.</p></div>
<div class="step seal"><div class="k">03 · BUILD</div><h3>Instruments</h3><p>CoLoRS and LRS spectrographs, robotic autoguiding and control, CubeSat mirrors.</p></div>
<div class="step seal"><div class="k">04 · MACHINE &amp; MEASURE</div><h3>Ultra-precision optics</h3><p>5-axis diamond turning to Ra &lt; 5 nm, interferometry, coating, and cryo-testing under one roof.</p></div>
</div></div></section>

<section><div class="wrap"><div class="sec-head"><h2>Featured projects</h2><p>Three things the team is building or running right now. <a href="{L(mode,"projects")}">See all projects and facilities →</a></p></div>
<div class="cards">{"".join(project_card(p, mode) for p in feat)}</div></div></section>

<section><div class="wrap"><div class="sec-head"><h2>Latest news</h2><p>Runs, first light, papers, and the workshops we host. <a href="{L(mode,"news")}">All news and events →</a></p></div>
<div class="cards">{"".join(news_card(n, mode) for n in NEWS[:3])}</div></div></section>
'''

def group_page(mode, key):
    sea = key == "sea-otters"
    g = "sea" if sea else "seal"
    name = "SEA OtTeRS" if sea else "SEAL Lab"
    full = "Synergy in Extragalactic Astronomy with Observation through Temporal and Redshift Spaces" if sea else "SPDT Engineering, Assembly, and Laser Metrology Laboratory"
    intro = T["SEA OtTeRS – intro paragraph"] if sea else T["SEAL Lab – intro paragraph"]
    projs = [p for p in PROJECTS if p["Group *"] == name]
    people = [p for p in PEOPLE if p["group"] in (name, "Both")]
    pubs = [p for p in SELECTED if p["Group *"] == name]
    hero = ("colors_night", "CoLoRS on the 0.7-m TRT at NARIT AstroPark") if sea else ("spdt_action", "Diamond turning of a mirror substrate on the Freeform L")
    if sea:
        themes = [("Time-domain astronomy & AGN", "Ensemble and individual variability of active galactic nuclei; photometric reverberation mapping with ULTRASPEC on the 2.4-m TNT; rapid spectroscopic follow-up of transients with robotic telescopes."),
                  ("Galaxy evolution & cosmology", "Lyman-α emitters and protoclusters at the end of reionization; H II galaxies as cosmic distance indicators; low-z analogs with GTC/MEGARA; machine-learning inference of physical parameters for JWST-era galaxies; dark-matter halo science with ARRAKIHS."),
                  ("Instruments for spectroscopy", "All-in-house low-resolution spectrographs for the 2.4-m and 0.7-m telescopes, with robotic control so a transient alert can become a classified spectrum in under 30 minutes.")]
        extra = f'''<section><div class="wrap group"><div class="sec-head"><h2>Facilities we use</h2><p>{E(T["Other telescopes / facilities to name"])}. NARIT's CHALAWAN cluster runs the ARRAKIHS simulations.</p></div>
<div class="cards"><div class="card"><div class="ph">{img("tnt","The 2.4-m Thai National Telescope")}</div><div class="body"><h3>2.4-m Thai National Telescope</h3><p>Doi Inthanon, 2,457 m. Home of ULTRASPEC, MRES and the LRS. ~120 photometric nights a year.</p></div></div>
<div class="card"><div class="ph">{img("trt_chile","0.7-m Thai Robotic Telescope at Cerro Tololo, Chile")}</div><div class="body"><h3>Thai Robotic Telescope network</h3><p>0.7-m robotic nodes in Chile, China, the USA, Australia and Thailand — CoLoRS gives every node a spectroscopic voice.</p></div></div>
<div class="card"><div class="ph">{img("trt_map","Map of NARIT telescopes")}</div><div class="body"><h3>Regional and world coverage</h3><p>Longitude coverage near 100° E fills a gap left by the large observatories, with &lt; 6 h to any right ascension across the network.</p></div></div></div></div></section>'''
    else:
        themes = [("Design → CNC → polishing → SPDT → metrology", "A complete production line for metallic and freeform optics, now at TRL 6, with the first 5-axis single-point diamond-turning facility in Southeast Asia."),
                  ("Space and astronomical hardware", "Slit-viewing mirrors for DARTS, M1/M2 mirrors for the Thai Space Consortium's 6U CubeSat, retroreflectors, and additively manufactured mirror prototypes."),
                  ("Technology transfer", "MoUs and letters of intent with Durham University (CfAI), UKATC and RAL Space; training Thai engineers on Thai machines; an open facility for joint projects.")]
        caps = "".join(f'<tr><td>{E(c["Capability / specification *"])}</td><td class="v">{E(c["Value *"])}</td><td>{E(c.get("Applies to",""))}</td><td class="muted">{E(c.get("Notes",""))}</td></tr>' for c in CAPS)
        extra = f'''<section><div class="wrap group seal"><div class="sec-head"><h2>Capabilities</h2><p>Numbers the lab commits to, measured on its own metrology bench.</p></div>
<div class="scroll"><table class="tbl"><thead><tr><th>CAPABILITY</th><th>VALUE</th><th>APPLIES TO</th><th>NOTES</th></tr></thead><tbody>{caps}</tbody></table></div>
<div class="cards" style="margin-top:28px"><div class="card"><div class="ph">{img("spdt_machine","Precitech Freeform L")}</div><div class="body"><h3>Freeform L, 5-axis SPDT</h3><p>Ø ≤ 650 mm, form &lt; 0.125 µm P-V, micro-milling and grinding.</p></div></div>
<div class="card"><div class="ph">{img("dynafiz","Zygo DynaFiz interferometer")}</div><div class="body"><h3>DynaFiz interferometry + ZeGage profilometry</h3><p>Form and roughness verification down to 0.15 nm Sq.</p></div></div>
<div class="card"><div class="ph">{img("coating","Coating chamber")}</div><div class="body"><h3>High-vacuum coating</h3><p>Reflective coatings verified by spectrophotometry over 400–700 nm.</p></div></div></div></div></section>'''
    def _tcard(t):
        chips = "".join(f'<span class="pill {g}">{E(p["short"])}</span>' for p in t["projects"])
        return f'<a class="card" href="{L(mode, "projects", t["slug"])}"><div class="body"><h3>{E(t["Theme *"])}</h3><p>{E(str(t.get("One-line summary *", "")))}</p><div class="chips" style="margin-top:10px">{chips}</div></div></a>'
    themes_html = "".join(_tcard(t) for t in themes_of(name)) or "".join(f'<div class="card"><div class="body"><h3>{E(t)}</h3><p>{E(d)}</p></div></div>' for t, d in themes)
    return f'''
<div class="pagehead"><div class="wrap"><div class="hero-grid"><div><img class="gbadge" src="assets/{"logo-sea-otters" if sea else "logo-seal-lab"}.png" alt="{E(name)} logo"><div class="eyebrow {g}">{E(full)}</div><h1>{E(name)}</h1><p class="lede">{E(intro)}</p>
<div class="cta" style="display:flex;gap:10px;flex-wrap:wrap;margin-top:22px"><a class="btn {g}" href="{L(mode,"contact")}">Work with {E(name)}</a><a class="btn" href="{L(mode,"publications")}">Publications</a></div></div>
<div class="hero-photo">{img(*hero)}<div class="cap">{E(hero[1])}</div></div></div></div></div>
<section><div class="wrap group {g}"><div class="sec-head"><h2>What we work on</h2><p>{"Redshift surveys and time-domain monitoring, with machine learning where the data are sparse." if sea else "Nanometer-scale reflective optics for both astronomical instrumentation and industrial solutions."}</p></div><div class="cards">{themes_html}</div></div></section>
{extra}
<section><div class="wrap group {g}"><div class="sec-head"><h2>Projects</h2><p><a href="{L(mode,"projects")}">Full project pages with photos and key numbers →</a></p></div><div class="cards">{"".join(project_card(p, mode) for p in projs)}</div></div></section>
<section><div class="wrap group {g}"><div class="sec-head"><h2>People</h2><p><a href="{L(mode,"people")}">Everyone on the team →</a></p></div><div class="people">{"".join(person_card(p, mode) for p in people)}</div></div></section>
<section><div class="wrap group {g}"><div class="sec-head"><h2>Selected papers</h2><p><a href="{L(mode,"publications")}">Full list by year →</a></p></div>{"".join(pub_row(p) for p in pubs)}</div></section>
'''

def pub_row(p):
    v = E(str(p["Journal / venue *"])); vp = E(str(p.get("Volume, page / article no.", "")))
    links = []
    if p.get("DOI"): links.append(f'<a href="https://doi.org/{E(str(p["DOI"]))}">DOI</a>')
    if p.get("arXiv ID"): links.append(f'<a href="https://arxiv.org/abs/{E(str(p["arXiv ID"]))}">arXiv:{E(str(p["arXiv ID"]))}</a>')
    if str(p.get("ADS link", "")).startswith("http"): links.append(f'<a href="{E(str(p["ADS link"]))}">{"ADS" if "adsabs" in str(p["ADS link"]) else "Publisher"}</a>')
    if str(p.get("PDF link", "")).startswith("http"): links.append(f'<a href="{E(str(p["PDF link"]))}">PDF</a>')
    return f'''<div class="pub"><div class="y">{p["year"]}</div><div><div class="t">{E(str(p["Title *"]))}</div><div class="a">{E(str(p["Authors *"]))}</div><div class="v"><b>{v}</b>{(" · " + vp) if vp else ""} · {E(str(p["Type *"]))}{(" · " + " · ".join(links)) if links else ""}</div></div></div>'''

def page_people(mode):
    out = []
    for sec in SECTION_ORDER:
        ps = [p for p in PEOPLE if p["section"] == sec]
        if not ps: continue
        note = ' <span class="stub">Profiles in preparation — names and photos are confirmed; roles and bios are being written.</span>' if sec == "New members" else ""
        out.append(f'<section class="{"flush" if not out else ""}"><div class="wrap"><h2 style="font-size:1.35rem">{E(sec)}{note}</h2><div class="people" style="margin-top:20px">{"".join(person_card(p, mode) for p in ps)}</div></div></section>')
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow">People</div><h1>The team</h1><p class="lede">Astronomers, research assistants, opto-mechanical and mechanical engineers, software developers, and the people who keep the lab running. Every name opens a profile with a CV or résumé where one has been shared.</p></div></div>{"".join(out)}'''

def page_person(p, mode):
    ph = f'<img src="{("../" if mode == "dist" else "") + p["photo"]}" alt="{E(p["Full name *"])}">' if p["photo"] else ""
    links = []
    for k, lbl in [("CV link (PDF)", "Curriculum vitae (PDF)"), ("Résumé link (PDF)", "Résumé (PDF)"), ("ORCID", "ORCID"), ("ADS library / author link", "NASA ADS"), ("Google Scholar", "Google Scholar"), ("GitHub", "GitHub"), ("LinkedIn", "LinkedIn"), ("Personal website", "Website")]:
        v = str(p.get(k, "") or "").strip()
        if v and v.startswith("http"): links.append(f'<a href="{E(v)}">{lbl} ↗</a>')
        elif v and k == "ORCID": links.append(f'<a href="https://orcid.org/{E(v)}">ORCID {E(v)} ↗</a>')
    email = str(p.get("Email *", "") or "")
    if email: links.append(f'<a href="mailto:{E(email)}">{E(email)}</a>')
    long = str(p.get("Long bio (profile page)", "") or "")
    short = str(p.get("Short bio (card) *", "") or "")
    body = para(long) if long else (f"<p>{E(short)}</p>" if short else '<div class="wip"><div class="ic">!</div><div><h3>Profile in preparation</h3><p>This member has joined the team. Their biography and research interests will appear here once written and reviewed; until then we show only what has been confirmed.</p></div></div>')
    interests = str(p.get("Research / engineering interests *", "") or "")
    chips = "".join(f'<span class="pill">{E(i.strip())}</span>' for i in re.split(r"[;\n•]|(?<=[a-z])\. (?=[A-Z])", interests) if i.strip()) if interests else ""
    g = "sea" if p["group"] == "SEA OtTeRS" else "seal" if p["group"] == "SEAL Lab" else ""
    pubs = [q for q in PUBS if p["Full name *"] in str(q.get("Team authors", ""))]
    pubs_html = f'<h2 style="font-size:1.3rem;margin-top:36px">Publications with the team</h2>{"".join(pub_row(q) for q in pubs)}' if pubs else ""
    projs = [q for q in PROJECTS if p["Full name *"] in str(q.get("Team members", ""))]
    projs_html = f'<h2 style="font-size:1.3rem;margin-top:36px">Projects</h2><div class="cards" style="margin-top:16px">{"".join(project_card(q, mode) for q in projs)}</div>' if projs else ""
    back = L(mode, "people")
    return f'''<div class="pagehead"><div class="wrap"><a href="{back}" class="muted">← People</a><div class="eyebrow {g}" style="margin-top:14px">{E(p["group"] or "SEA OtTeRS & SEAL Lab")}{(" · " + E(p["cat"])) if p["cat"] else ""}</div>
<h1>{E(p["Full name *"])}{(", " + E(str(p["Degree / title"]))) if p.get("Degree / title") else ""}</h1><p class="lede">{E(p["role"])}</p></div></div>
<section class="flush"><div class="wrap"><div class="profile"><div class="side">{ph}<div class="links">{"".join(links)}</div>
<dl class="kv">{f'<dt>Affiliation</dt><dd>{E(str(p.get("Affiliation","")))}</dd>' if p.get("Affiliation") else ""}{f'<dt>Role in team</dt><dd>{E(str(p.get("Role in the team","")))}</dd>' if p.get("Role in the team") else ""}{f'<dt>Since</dt><dd>{int(float(p["Start year"]))}</dd>' if p.get("Start year") else ""}</dl></div>
<div class="main">{body}{f'<div class="chips" style="margin-top:18px">{chips}</div>' if chips else ""}{projs_html}{pubs_html}</div></div></div></section>'''

def project_block(p, mode):
    g = "sea" if p["Group *"] == "SEA OtTeRS" else "seal"
    status = str(p.get("Status *", "") or "").strip()
    if not p["full"]:
        team = str(p.get("Team members", "") or "").strip(); partners = str(p.get("Collaborators / partners", "") or "").strip(); fac = str(p.get("Facility / telescope", "") or "").strip()
        meta = "".join(f'<span><b>{k}</b> {E(v)}</span>' for k, v in [("Facility", fac), ("Team", team), ("Partners", partners)] if v)
        return f'''<div class="pjs" id="{p["slug"]}"><div class="chips"><span class="pill {g}">{E(p["short"])}</span><span class="pill">{E(p["Type *"])}</span>{f'<span class="pill">{E(status)}</span>' if status else '<span class="pill todo">○ Status to be confirmed</span>'}</div>
<h3>{E(p["Project name *"])}</h3><p class="sum">{E(p["One-line summary *"])}</p>{f'<p class="meta">{meta}</p>' if meta else ""}<p class="stub">Details in preparation — this entry has the project title and scope only; results, numbers, and figures will be added once the team has reviewed them.</p></div>'''
    gal = "".join(f'<a href="assets/photos/web/{k}.jpg" target="_blank" rel="noopener" title="Open full size"><img src="assets/photos/web/{k}.jpg" alt="" loading="lazy"></a>' for k in PROJ_GALLERY.get(p["short"], []))
    facts = "".join(f"<dt>{E(k)}</dt><dd>{E(str(p[c]))}</dd>" for k, c in [("Facility", "Facility / telescope"), ("Key numbers", "Key numbers"), ("Timeline", "Timeline"), ("Team", "Team members"), ("Partners", "Collaborators / partners"), ("Funding", "Funding")] if str(p.get(c, "") or "").strip())
    link = f'<p style="margin-top:12px"><a href="{E(str(p["Link"]))}">Project link ↗</a></p>' if str(p.get("Link", "") or "").strip() else ""
    cred = PROJ_CREDIT.get(p["short"], "")
    return f'''<div class="pj" id="{p["slug"]}"><div><div class="ph{" fig" if p["short"] in PROJ_FIG else ""}">{img(p["img"], p["imgalt"])}</div>{f'<div class="gal">{gal}</div>' if gal else ""}{f'<p class="cap">{E(p["imgalt"])}. {E(cred)}</p>' if cred else ""}</div>
<div><div class="chips"><span class="pill {g}">{E(p["Group *"])}</span><span class="pill">{E(p["Type *"])}</span><span class="pill">{E(status)}</span></div><h3 style="margin-top:12px">{E(p["Project name *"])} <span class="muted" style="font-weight:400">· {E(p["short"])}</span></h3><p class="sum">{E(p["One-line summary *"])}</p><div class="desc">{para(p.get("Description", "") or "") or '<p class="stub" style="margin-top:10px">Full description in preparation; the summary and key numbers above are current.</p>'}</div><dl class="facts">{facts}</dl>{link}</div></div>'''

def theme_section(t, mode):
    g = "sea" if t["Group *"] == "SEA OtTeRS" else "seal"
    chips = "".join(f'<a class="pill {g}" href="{L(mode, "projects", p["slug"])}">{E(p["short"])}</a>' for p in t["projects"])
    n_full = sum(1 for p in t["projects"] if p["full"]); n_stub = len(t["projects"]) - n_full
    return f'''<div class="theme" id="{t["slug"]}"><div class="th"><div class="eyebrow {g}">{E(t["Group *"])} · research theme</div><h2>{E(t["Theme *"])}</h2><p class="lede">{E(str(t.get("One-line summary *", "")))}</p><div class="chips">{chips}</div></div>
{"".join(project_block(p, mode) for p in t["projects"])}</div>'''

def page_projects(mode):
    idx = []
    for grp, g in (("SEA OtTeRS", "sea"), ("SEAL Lab", "seal")):
        items = "".join(f'<li><a href="{L(mode, "projects", t["slug"])}">{E(t["Theme *"])}</a> <span class="muted">· {len(t["projects"])}</span></li>' for t in themes_of(grp))
        idx.append(f'<div class="tidx {g}"><div class="eyebrow {g}">{E(grp)}</div><ul>{items}</ul></div>')
    unthemed = [p for p in PROJECTS if not str(p.get("Research theme *", "")).strip()]
    extra = f'<div class="theme"><div class="th"><h2>Other projects</h2></div>{"".join(project_block(p, mode) for p in unthemed)}</div>' if unthemed else ""
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow">Projects &amp; facilities</div><h1>What we work on, by question</h1><p class="lede">Our work is organized by research theme — the question each line of work answers — rather than by paper. Each theme lists its projects and instruments, finished and ongoing alike; the status chip on every entry tells you which. Numbers in monospace are measured or designed values, not aspirations.</p>
<div class="tgrid">{"".join(idx)}</div></div></div>
<section class="flush"><div class="wrap">{"".join(theme_section(t, mode) for t in THEMES)}{extra}</div></section>'''

def chart_svg():
    W, H, pad = 640, 200, 30; n = len(YEARS); bw = (W - 2 * pad) / n; mx = max(t for _, t, _ in YEARS)
    parts = [f'<svg viewBox="0 0 {W} {H+30}" role="img" aria-label="Papers per year">']
    for i, (y, t, r) in enumerate(YEARS):
        x = pad + i * bw + 6; w = bw - 12
        h_t = (H - pad) * t / mx; h_r = (H - pad) * r / mx
        parts.append(f'<rect x="{x:.1f}" y="{H - h_t:.1f}" width="{w:.1f}" height="{h_t:.1f}" fill="var(--seal)" opacity=".55"/>')
        parts.append(f'<rect x="{x:.1f}" y="{H - h_r:.1f}" width="{w:.1f}" height="{h_r:.1f}" fill="var(--sea)"/>')
        if t: parts.append(f'<text x="{x + w/2:.1f}" y="{H - h_t - 6:.1f}" text-anchor="middle" font-size="11" fill="var(--ink-2)" font-family="IBM Plex Mono, monospace">{t}</text>')
        parts.append(f'<text x="{x + w/2:.1f}" y="{H + 18}" text-anchor="middle" font-size="11" fill="var(--muted)" font-family="IBM Plex Mono, monospace">{y}</text>')
    parts.append(f'<line x1="{pad}" y1="{H}" x2="{W - pad}" y2="{H}" stroke="var(--rule)"/>')
    parts.append("</svg>")
    return "".join(parts)

def page_publications(mode):
    years = sorted({p["year"] for p in PUBS}, reverse=True)
    full = "".join(f'<h2 style="font-size:1.2rem;margin-top:28px;color:var(--muted)">{y}</h2>' + "".join(pub_row(p) for p in PUBS if p["year"] == y) for y in years)
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow">Publications</div><h1>Papers and proceedings</h1><p class="lede">Refereed articles, SPIE proceedings, and work in preparation. The full record lives in the team's <a href="{E(T["Team ADS library URL"])}">NASA ADS library ↗</a>.</p></div></div>
<section class="flush"><div class="wrap"><div class="cards two" style="align-items:start"><div class="chart"><div class="eyebrow">Papers per year</div>{chart_svg()}<div class="leg"><span><i style="background:var(--sea)"></i>refereed</span><span><i style="background:var(--seal);opacity:.55"></i>proceedings and other</span><span class="muted">source: NASA ADS, Sept 2026</span></div></div>
<div><div class="eyebrow">Selected</div>{"".join(pub_row(p) for p in SELECTED)}</div></div></div></section>
<section><div class="wrap"><h2>All publications</h2>{full}</div></section>'''

def page_news(mode):
    items = "".join(f'''<div class="item" id="n-{n["date"]}"><div class="d">{n["date"]}</div><div><span class="pill {"sea" if n["Group"]=="SEA OtTeRS" else "seal" if n["Group"]=="SEAL Lab" else ""}">{E(str(n["Group"]))}</span><h3 style="margin-top:8px">{E(n["Headline *"])}</h3><p>{E(str(n["Text *"]))}</p>{f'<p style="margin-top:8px"><a href="{E(str(n["Link"]))}">Event page ↗</a></p>' if str(n.get("Link","") or "").strip() else ""}</div><div class="ph">{img(n["img"], n["Headline *"])}</div></div>''' for n in NEWS)
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow">News &amp; events</div><h1>What happened, and what is coming</h1><p class="lede">First light, mission milestones, papers, and the workshops and conferences the team hosts in Chiang Mai.</p></div></div>
<section class="flush"><div class="wrap"><div class="timeline">{items}</div></div></section>'''

def wip(title, why, ready, todo, meanwhile):
    return f'''<div class="wip"><div class="ic">!</div><div><h3>{E(title)}</h3><p>{why}</p>
<div class="st">{"".join(f'<span class="pill ready">✓ {E(r)}</span>' for r in ready)}{"".join(f'<span class="pill todo">○ {E(t)}</span>' for t in todo)}</div>
<p style="margin-top:10px">{meanwhile}</p></div></div>'''
PLANNED = ""

def page_contact(mode):
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow gold">Contact for collaborations</div><h1>Work with us</h1><p class="lede">We collaborate on observing programs, instrument access, ultra-precision optics jobs, and student projects. Tell us which, and the right person answers.</p></div></div>
<section class="flush"><div class="wrap">{wip("This page is in preparation", "The contact addresses below are current and monitored. The inquiry form is shown so you can see what we will ask, but it is not connected yet — nothing you type here is sent.", ["Contact emails", "Visiting address"], ["Inquiry form", "Response-time policy", "Map"], f'<b>Until the form opens:</b> email the group directly — <a href="mailto:{E(T["SEA OtTeRS – contact email"])}">{E(T["SEA OtTeRS – contact email"])}</a> for SEA OtTeRS, <a href="mailto:{E(T["SEAL Lab – contact email"])}">{E(T["SEAL Lab – contact email"])}</a> for SEAL Lab. We answer from those mailboxes.')}
<div class="contactgrid" style="margin-top:24px">
<div class="cbox sea"><h3>SEA OtTeRS</h3><p>Observing time on the TNT/TRT with LRS or CoLoRS, joint survey and time-domain programs, machine-learning projects, ARRAKIHS simulations.</p><a class="mono" href="mailto:{E(T["SEA OtTeRS – contact email"])}">{E(T["SEA OtTeRS – contact email"])}</a></div>
<div class="cbox seal"><h3>SEAL Lab</h3><p>Diamond-turned metallic and freeform mirrors, CubeSat optics, metrology and coating services, technology-transfer partnerships.</p><a class="mono" href="mailto:{E(T["SEAL Lab – contact email"])}">{E(T["SEAL Lab – contact email"])}</a></div>
<div class="cbox gold"><h3>Visit</h3><p>{E(T["Institute / host organisation"])}<br>{E(T["Postal address"])}</p><span class="mono muted">Mon–Fri · by appointment</span></div></div>
<h2 style="margin-top:44px">Send an inquiry</h2>
<form class="form off" style="margin-top:18px" onsubmit="event.preventDefault()"><fieldset disabled style="display:contents">
<div class="row"><label>Name<input required placeholder="Your name"></label><label>Affiliation<input placeholder="Institute or company"></label></div>
<label>Email<input type="email" required placeholder="you@example.org"></label>
<label>Topic<select><option>Observing time / joint program (SEA OtTeRS)</option><option>Instrument access: LRS or CoLoRS</option><option>Optics job: SPDT, metrology, coating (SEAL Lab)</option><option>Student project or internship</option><option>Technology transfer / MoU</option><option>Visit or talk</option><option>Other</option></select></label>
<label>Message<textarea placeholder="What would you like to do together, and by when?"></textarea></label>
</fieldset><div><button class="btn" type="button" disabled>Form not open yet</button> <span class="stub">Preview of the questions we will ask.</span></div></form></div></section>'''

def page_internships(mode):
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow gold">Internship application</div><h1>Intern with SEA OtTeRS or SEAL Lab</h1><p class="lede">Undergraduate and graduate internships in extragalactic astronomy, instrumentation, software, and ultra-precision engineering, supervised by the team in Chiang Mai.</p></div></div>
<section class="flush"><div class="wrap">{wip("Applications are not open yet", "We are finalizing eligibility, periods, and how applications are reviewed. The topics below are real and current; the form is a preview and does not submit.", ["Internship topics"], ["Eligibility & periods", "Supervisor list", "Application form", "Review timeline"], f'<b>Interested now?</b> Send a short email with your CV and the topic you like to <a href="mailto:{E(T["SEA OtTeRS – contact email"])}">{E(T["SEA OtTeRS – contact email"])}</a> (astronomy, data, software) or <a href="mailto:{E(T["SEAL Lab – contact email"])}">{E(T["SEAL Lab – contact email"])}</a> (engineering). We reply to every message, and we will tell you when the formal call opens.')}
<div class="cards" style="margin-top:24px"><div class="card"><div class="body"><span class="pill sea">SEA OtTeRS</span><h3>Astronomy &amp; data</h3><p>Galaxy evolution with JWST and GTC data, AGN light curves, machine-learning parameter extraction, ARRAKIHS mock observations on the CHALAWAN cluster.</p></div></div>
<div class="card"><div class="body"><span class="pill sea">SEA OtTeRS</span><h3>Instrument software</h3><p>Autoguiding and robotic control for LRS and CoLoRS, QuickLook reduction pipelines, scheduler and broker tools.</p></div></div>
<div class="card"><div class="body"><span class="pill seal">SEAL Lab</span><h3>Precision engineering</h3><p>Opto-mechanical design, FEA, SPDT machining, interferometry and profilometry, additive-manufacturing prototypes.</p></div></div></div>
<h2 style="margin-top:44px">Apply</h2>
<form class="form off" style="margin-top:18px" onsubmit="event.preventDefault()"><fieldset disabled style="display:contents">
<div class="row"><label>Full name<input required></label><label>University / program<input required placeholder="e.g. Chiang Mai University, BSc Physics"></label></div>
<div class="row"><label>Email<input type="email" required></label><label>Preferred group<select><option>SEA OtTeRS</option><option>SEAL Lab</option><option>Either</option></select></label></div>
<div class="row"><label>Earliest start<input type="month"></label><label>Duration<select><option>2 months</option><option>3 months</option><option>4–6 months</option><option>Thesis project</option></select></label></div>
<label>Statement of interest<textarea placeholder="What do you want to learn, and what have you already done (courses, code, hardware)?"></textarea></label>
<label>CV (PDF)<input type="file" accept="application/pdf"></label>
</fieldset><div><button class="btn" type="button" disabled>Applications open soon</button> <span class="stub">Preview of the application form.</span></div></form></div></section>'''

def page_shop(mode):
    items = [("SEA OtTeRS tee", "T-shirt"), ("SEAL Lab tee", "T-shirt"), ("Otter sticker pack", "Stickers"), ("Mirror-finish mug", "Mug")]
    cards = "".join(f'<div class="card"><div class="ph">{E(n)}</div><div class="body"><h3>{E(n)}</h3><p>{E(t)} · not for sale yet</p><div class="meta"><span class="pill todo">○ Design in progress</span></div></div></div>' for n, t in items)
    return f'''<div class="pagehead"><div class="wrap"><div class="eyebrow gold">Merchandise shop</div><h1>Wear the otter, fund the team</h1><p class="lede">Team merchandise with a single purpose: every baht of profit goes to a wellness and healthcare fund for the students and non-permanent staff who work with SEA OtTeRS and SEAL Lab.</p></div></div>
<section class="flush"><div class="wrap">{wip("The shop is not open yet", "Nothing is for sale on this page today. The product cards are placeholders for designs still being drawn, and no prices, orders, or payments are taken here. The purpose of the shop — funding wellness and healthcare for students and non-permanent staff — is decided; the rest is in progress.", ["Purpose of the fund"], ["Designs", "Prices", "Ordering & payment", "Fund rules", "Running totals"], f'<b>Want to support the fund before the shop opens?</b> Write to <a href="mailto:{E(T["SEA OtTeRS – contact email"])}">{E(T["SEA OtTeRS – contact email"])}</a>. We will publish the fund rules and totals on this page before the first sale.')}
<div class="shop" style="margin-top:24px">{cards}</div>
<div class="fund"><div><div class="eyebrow gold">Where the money goes</div><div class="big">100% of profit</div><p class="ink2" style="margin-top:8px">After production and shipping costs, all profit is paid into the team wellness and healthcare fund. The fund covers health insurance top-ups, medical expenses, and wellness support for students and non-permanent staff associated with the two groups.</p></div>
<div><div class="eyebrow">Transparency</div><p class="ink2" style="margin-top:8px">This page will show the running total raised and paid out, updated with each sale cycle. Fund rules and the approval process will be published here before the first sale.</p></div></div></div></section>'''

# ---------------------------------------------------------------- assembly
def head(title, mode):
    fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">'
    return f'<title>{E(title)}</title>\n<meta name="description" content="SEAL × OTTER — extragalactic astronomy, astronomical instrumentation, and precision optics. The joint team of SEA OtTeRS and SEAL Lab at NARIT, Chiang Mai.">\n<link rel="icon" type="image/png" href="assets/favicon.png">\n{fonts}\n<style>{CSS}</style>\n'

def build_dist():
    out = os.path.join(ROOT, "dist"); shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, "people")); shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(out, "assets"), ignore=shutil.ignore_patterns("*.img"))
    pages = {"index": page_index, "sea-otters": lambda m: group_page(m, "sea-otters"), "seal-lab": lambda m: group_page(m, "seal-lab"), "people": page_people, "projects": page_projects, "publications": page_publications, "news": page_news, "contact": page_contact, "internships": page_internships, "shop": page_shop}
    for s, lbl, title, st in PAGES:
        body = pages[s]("dist")
        doc = "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + head(title + (" · SEAL × OTTER" if s != "index" else ""), "dist") + "</head>\n<body>\n" + nav(s, "dist") + f'<main class="page">{body}</main>' + footer("dist") + "\n</body>\n</html>\n"
        open(os.path.join(out, f"{s}.html"), "w").write(doc)
    for p in PEOPLE:
        body = page_person(p, "dist").replace('src="assets/', 'src="../assets/').replace('href="people.html', 'href="../people.html').replace('href="projects.html', 'href="../projects.html')
        doc = "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + head(p["Full name *"] + " · SEAL × OTTER", "dist") + "</head>\n<body>\n" + nav("people", "dist").replace('href="', 'href="../').replace('src="assets/', 'src="../assets/') + f'<main class="page">{body}</main>' + footer("dist").replace('href="', 'href="../').replace('href="../mailto', 'href="mailto').replace('href="../http', 'href="http') + "\n</body>\n</html>\n"
        open(os.path.join(out, "people", f"{p['slug']}.html"), "w").write(doc)
    open(os.path.join(out, "CNAME"), "w").write("sealxotter.org\n")
    open(os.path.join(out, "README.md"), "w").write("# SEAL x OTTER website\n\nGenerated by `gen.py` from the team content sheet. Open `index.html`, or serve the folder (GitHub Pages works as-is).\n")

def build_preview():
    """One file, all pages, hash routing, images as data URIs (downsized)."""
    from PIL import Image; import io
    cache = {}
    def uri(path):
        if path in cache: return cache[path]
        full = os.path.join(ROOT, path)
        im = Image.open(full); fmt = "PNG" if path.endswith(".png") else "JPEG"
        if fmt == "JPEG":
            im = im.convert("RGB"); im.thumbnail((900, 900)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=62, optimize=True); mime = "image/jpeg"
        else:
            im.thumbnail((400, 400)); buf = io.BytesIO(); im.save(buf, "PNG", optimize=True); mime = "image/png"
        cache[path] = f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode(); return cache[path]
    pages = {"index": page_index, "sea-otters": lambda m: group_page(m, "sea-otters"), "seal-lab": lambda m: group_page(m, "seal-lab"), "people": page_people, "projects": page_projects, "publications": page_publications, "news": page_news, "contact": page_contact, "internships": page_internships, "shop": page_shop}
    secs = "".join(f'<main class="page" data-page="{s}" data-title="{E(t)}"{"" if s == "index" else " hidden"}>{pages[s]("preview")}</main>' for s, lbl, t, st in PAGES)
    secs += "".join(f'<main class="page" data-page="people/{p["slug"]}" data-title="{E(p["Full name *"])}" hidden>{page_person(p, "preview")}</main>' for p in PEOPLE)
    js = r"""<script>
(function(){
  var pages=document.querySelectorAll('main.page');
  function show(){
    var h=location.hash.replace(/^#\/?/,'')||'index'; var parts=h.split('/'); var key=parts[0]==='people'&&parts[1]?'people/'+parts[1]:parts[0]; var anchor=parts[0]==='people'?null:parts[1];
    var found=false; pages.forEach(function(p){var on=p.dataset.page===key; p.hidden=!on; if(on)found=true;});
    if(!found){pages.forEach(function(p){p.hidden=p.dataset.page!=='index';}); key='index';}
    document.querySelectorAll('.nav a[data-nav]').forEach(function(a){a.classList.toggle('active',a.dataset.nav===key.split('/')[0]);});
    document.querySelector('.nav ul').classList.remove('open');
    var t=document.querySelector('main.page:not([hidden])'); document.title=(t&&t.dataset.title?t.dataset.title+' · ':'')+'SEAL × OTTER';
    if(anchor){var el=document.getElementById(anchor); if(el){el.scrollIntoView({block:'start'}); return;}}
    window.scrollTo(0,0);
  }
  window.addEventListener('hashchange',show); show();
})();
</script>"""
    doc = head("SEAL × OTTER", "preview") + nav("index", "preview") + secs + footer("preview") + js
    # inline images
    def repl(m):
        path = m.group(1)
        return f'src="{uri(path)}"' if os.path.exists(os.path.join(ROOT, path)) else m.group(0)
    doc = re.sub(r'src="((?:\.\./)?assets/[^"]+)"', lambda m: repl(type("M", (), {"group": lambda self, i: m.group(i).replace("../", "")})()), doc)
    open(os.path.join(ROOT, "preview.html"), "w").write(doc)
    print("preview.html", len(doc) // 1024, "KB;", len(cache), "images inlined")

if __name__ == "__main__":
    build_dist(); build_preview()
    print("dist pages:", len(os.listdir(os.path.join(ROOT, "dist"))), "+", len(PEOPLE), "profiles")
