"""Step 8: README.md, LICENSE and reddit/post.md, with every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); p = R["prose"]; d = R["desc"]; h = R["half"]; m1 = R["M1"]["ld"]
readme = f"""# Does Parliament notice disasters, and whose?

How much does the House of Commons talk about the place where a disaster happened, how fast does that attention fade, and does it follow the death toll or the location? This study follows {d['n']} localised disasters in the UK, 1910 to 2020 ({d['deaths_total']:,} deaths), through monthly counts of Commons contributions that name the place.

Dr Tristan Hotham, Independent researcher, 2026.

**Interactive version:** {PAGE}

**Paper:** {{https://doi.org/10.5281/zenodo.24094466}}

**Blog post:** {{https://blog.tristanhotham.com/2026/10/31/disaster-attention/}}

## Headline results

- In the month of a disaster, Commons contributions naming the place rise to {p['m0']:.1f} times their usual level (95% CI {p['m0_lo']:.1f} to {p['m0_hi']:.1f}); no pre-trend (p = {R['M2']['pretrend_p']:.2f}).
- Half of a disaster's five-year excess attention comes within a median of {h['median']:.1f} months; {h['within12']} of {h['n']} disasters with excess attention reached half within the first year. Grenfell Tower ({R['cases']['grenfell']['half_k']} months), Piper Alpha ({R['cases']['piperalpha']['half_k']}) and Gresford ({R['cases']['gresford']['half_k']}) held attention much longer.
- Attention rises with the death toll only weakly: elasticity {m1['b']:.2f} (95% CI {m1['lo']:.2f} to {m1['hi']:.2f}) in the pre-specified model, about {p['el_double_pc']:.0f}% more attention for twice the deaths. Not robust: the interval includes zero in {p['n_checks_cross']} of {p['n_checks']} planned checks; permutation p = {R['perm']['p_two']:.2f}; placebo {p['placebo_b']:.2f}.
- London and the South East: {p['london_x']:.1f} times the attention of the rest of England in the planned model, but about +{p['london_drop2_b']:.0f}% (CI includes 0) without Grenfell Tower and the King's Cross fire. No clear differences for Scotland, Wales, Northern Ireland or mining disasters.
- Extension (made after the first results, reported beside them): {R['ext']['events']['added_main']} disasters that became searchable once further phrases were harvested, same rules. With {R['ext']['desc']['n']} disasters the elasticity is {R['ext']['M1']['ld']['b']:.2f} (95% CI {R['ext']['M1']['ld']['lo']:.2f} to {R['ext']['M1']['ld']['hi']:.2f}), permutation p = {R['ext']['perm']['p_two']:.3f}, but the interval still includes zero in {R['ext']['prose']['n_checks_cross']} of {R['ext']['prose']['n_checks']} checks; month 0 ratio {R['ext']['prose']['m0']:.1f}; median time to half {R['ext']['half']['median']:.1f} months.
- Lists of disasters and search words are filters of memory: among the {p['listonly']['n']} disasters on the Wikipedia list alone (40+ deaths) the elasticity is {p['listonly']['b']:.2f} (exploratory).

## Files

| Path | What |
|---|---|
| `index.html`, `js/page.js`, `img/` | interactive map page (MapLibre, OpenFreeMap Positron): disasters sized by deaths, coloured by attention per death or kind; filters by kind and years; search; popups with a monthly sparkline; excluded candidates as rings |
| `header.png` | social card, 1200 x 630 |
| `data/events.csv` | every candidate disaster (included and excluded): date, deaths and source, kind, search term and kind of phrase, flags, nation and region, baseline, five-year count, expected count, peak, excess, time to half, reason for exclusion |
| `data/event_months.csv` | event x month panel, months -24 to 59, for the included disasters |
| `data/models.csv`, `data/models_extension.csv` | coefficients of every model, first version and extension |
| `data/results.json` | every number used on the page, in the paper, blog, collage and post |
| `data/site.json` | compact page data |
| `code/` | the pipeline (below); `code/events.csv` is the hand-curated event list with inclusion decisions |
| `release/paper/` | paper (PDF, LaTeX, figures, refs.bib) and `cover_note.md` (journals and a 150-word summary) |
| `release/blog/` | blog post (WordPress block markup with image placeholders), figures, `meta.json` |
| `release/zenodo/` | paper PDF, data and code zip, `metadata.json` |
| `reddit/` | collage, its script, looping GIF and `post.md` |
| `NOTES.md` | working notes, the analysis plan written before any outcome model, and the log of decisions |

## Method in brief

- **Disasters**: the Wikipedia list of disasters in Great Britain and Ireland by death toll (40+ deaths), Wikidata disasters in the UK with 8+ recorded deaths, and a list of well-known disaster place names (tolls checked by hand). Kept: single localised events on UK soil or UK waters since 1909 with deaths; excluded: pandemics, heatwaves, smogs, losses at sea, events abroad, the Isle of Man, events without a usable search term ({R['data']['events']['excluded']} candidates in the first version, {R['ext']['events']['excluded']} after the extension; listed with the reason). `code/events.csv` column `ext` marks the rows changed in the extension.
- **Attention**: Commons spoken contributions per month containing the site name (pit, village, station) or "in" plus the town, from the UK Parliament Hansard API; baseline = mean of months -24 to -1, scaled by the monthly volume of all place mentions.
- **Models**: PPML of the five-year count on log deaths, log expected count, phrase type, kind and era (errors clustered by term); stacked Poisson event study with event fixed effects and a volume offset; {p['n_checks']} planned robustness checks, a placebo and a permutation test. Plan in `NOTES.md`.
- **Limits**: counts of speeches, not of care or action; lists of disasters favour remembered events; search words differ in how they are used; early Hansard volumes match few searches; observational design.

## How to rerun

```
python3 code/01_data.py      # event list, nation and region, monthly series, measures
DA_SAMPLE=v1 python3 code/02_models.py    # planned models, event study, robustness, first version (about 3 minutes)
DA_SAMPLE=ext python3 code/02_models.py   # the same for the extension
python3 code/03_results.py   # data/results.json and page data
python3 code/04_figures.py   # figures and header.png
python3 code/05_build_site.py
python3 code/06_paper.py     # DOI=10.5281/zenodo.N to fill the DOI
python3 reddit/collage.py
python3 code/08_readme.py
python3 code/07_release.py
```

Inputs (paths in `code/common.py`): `hansard_monthly.json`, `hansard_monthly_extra.json` (phrases harvested after the first results), `wiki_lists.json`, `disasters_wd.tsv` (raw harvest), `places.csv` from Mentioned in the House, ONS `uk_topo.json`. Python 3 with pandas, statsmodels, shapely, pyproj, matplotlib; xelatex and bibtex.

## Sources and licences

- Hansard, House of Commons, via the UK Parliament Hansard API. Contains Parliamentary information licensed under the Open Parliament Licence v3.0.
- English Wikipedia, "List of disasters in Great Britain and Ireland by death toll" and event articles (CC BY-SA 4.0).
- Wikidata (CC0).
- Town points from Mentioned in the House (Hotham 2026, https://doi.org/10.5281/zenodo.23761431).
- ONS countries and regions (Open Government Licence v3.0). Base map: OpenFreeMap Positron (OpenStreetMap, ODbL).

Licence: text, figures and data CC BY 4.0 (fields derived from Wikipedia CC BY-SA 4.0); code MIT (see LICENSE).

## Citation

Hotham, T. (2026) Does Parliament notice disasters, and whose? Attention in the House of Commons to the places of UK disasters, 1910 to 2020. Zenodo. {{https://doi.org/10.5281/zenodo.24094466}}

{AI}
"""
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and data: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
Fields derived from English Wikipedia: CC BY-SA 4.0. Wikidata: CC0. Hansard: Open Parliament Licence v3.0.
"""
top = sorted([r for r in R["cases"].values() if r["main"]], key=lambda r: -(r["CX"] or 0))[:4]
post = f"""**Title:** [OC] Does Parliament notice disasters? Commons speeches naming the place jump to {p['m0']:.0f}x their usual level in the month of a UK disaster, then mostly fade within the year ({d['n']} disasters, 1910 to 2020)

**Body:**

I counted, month by month, the House of Commons speeches that named the place of {d['n']} UK disasters between 1910 and 2020 (pit explosions, rail and air crashes, fires, crowd crushes, bombings and shootings; {d['deaths_total']:,} deaths), from two years before to five years after.

- In the month of a disaster, speeches naming the place rise to {p['m0']:.1f}x their usual level. Nothing builds up beforehand.
- Half of the extra attention over five years comes within a median of {h['median']:.1f} months. A few disasters followed by public inquiries, such as Grenfell Tower and Piper Alpha, held attention for years.
- The death toll explains little: the raw rank correlation is {d['spearman_deaths_C']:.2f}. In my planned model twice the deaths goes with about {p['el_double_pc']:.0f}% more attention, and even that is not robust.
- London and the South East seem to get more attention, but that rests on two disasters (Grenfell Tower and the King's Cross fire).
- Later I found search words for {R['ext']['events']['added_main']} more disasters and added them under the same rules. With all {R['ext']['desc']['n']}, twice the deaths goes with about {R['ext']['prose']['el_double_pc']:.0f}% more attention: a bit clearer, still not robust.
- Any list of disasters is a list of what is remembered, and the words matter: "in Lockerbie" turns up {R['cases']['lockerbie']['C']} times in five years, "Lockerbie" {R['swapcases']['lockerbie']['C']}.

Interactive map with a month-by-month chart for each disaster: {PAGE}

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia list of disasters in Great Britain and Ireland by death toll (CC BY-SA); Wikidata (CC0); ONS boundaries. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Paper and code: {REPO}
"""
for t in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS", "civil serv"):
        assert bad not in t, bad
open(os.path.join(ROOT, "README.md"), "w").write(readme)
open(os.path.join(ROOT, "LICENSE"), "w").write(lic)
open(os.path.join(ROOT, "reddit", "post.md"), "w").write(post)
print("readme", len(readme.split()), "words")
