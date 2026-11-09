# Does Parliament notice disasters, and whose?

How much does the House of Commons talk about the place where a disaster happened, how fast does that attention fade, and does it follow the death toll or the location? This study follows 64 localised disasters in the UK, 1910 to 2020 (4,346 deaths), through monthly counts of Commons contributions that name the place.

Dr Tristan Hotham, Independent researcher, 2026.

**Interactive version:** https://maps.tristanhotham.com/disaster-attention/

**Paper:** https://doi.org/10.5281/zenodo.24094466

**Blog post:** https://blog.tristanhotham.com/2026/10/31/disaster-attention/

## Headline results

- In the month of a disaster, Commons contributions naming the place rise to 10.4 times their usual level (95% CI 2.4 to 44.9); no pre-trend (p = 0.47).
- Half of a disaster's five-year excess attention comes within a median of 8.5 months; 31 of 54 disasters with excess attention reached half within the first year. Grenfell Tower (23 months), Piper Alpha (28) and Gresford (29) held attention much longer.
- Attention rises with the death toll only weakly: elasticity 0.42 (95% CI 0.05 to 0.78) in the pre-specified model, about 33% more attention for twice the deaths. Not robust: the interval includes zero in 12 of 28 planned checks; permutation p = 0.07; placebo 0.01.
- London and the South East: 3.5 times the attention of the rest of England in the planned model, but about +39% (CI includes 0) without Grenfell Tower and the King's Cross fire. No clear differences for Scotland, Wales, Northern Ireland or mining disasters.
- Extension (made after the first results, reported beside them): 22 disasters that became searchable once further phrases were harvested, same rules. With 86 disasters the elasticity is 0.52 (95% CI 0.12 to 0.92), permutation p = 0.006, but the interval still includes zero in 10 of 28 checks; month 0 ratio 11.1; median time to half 5.5 months.
- Lists of disasters and search words are filters of memory: among the 31 disasters on the Wikipedia list alone (40+ deaths) the elasticity is 2.02 (exploratory).

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

- **Disasters**: the Wikipedia list of disasters in Great Britain and Ireland by death toll (40+ deaths), Wikidata disasters in the UK with 8+ recorded deaths, and a list of well-known disaster place names (tolls checked by hand). Kept: single localised events on UK soil or UK waters since 1909 with deaths; excluded: pandemics, heatwaves, smogs, losses at sea, events abroad, the Isle of Man, events without a usable search term (39 candidates in the first version, 13 after the extension; listed with the reason). `code/events.csv` column `ext` marks the rows changed in the extension.
- **Attention**: Commons spoken contributions per month containing the site name (pit, village, station) or "in" plus the town, from the UK Parliament Hansard API; baseline = mean of months -24 to -1, scaled by the monthly volume of all place mentions.
- **Models**: PPML of the five-year count on log deaths, log expected count, phrase type, kind and era (errors clustered by term); stacked Poisson event study with event fixed effects and a volume offset; 28 planned robustness checks, a placebo and a permutation test. Plan in `NOTES.md`.
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

Hotham, T. (2026) Does Parliament notice disasters, and whose? Attention in the House of Commons to the places of UK disasters, 1910 to 2020. Zenodo. https://doi.org/10.5281/zenodo.24094466

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
