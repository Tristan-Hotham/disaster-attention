# disaster-attention: working notes

Brief: /home/claude/work/new12/BRIEFS.md section 3 (+ shared rules new11, new10, new9, new8, house brief). Format refs:
pm-streets, wiki-vs-hansard. Scratch: /home/claude/scratch/disaster-attention (delete at the end).

Title: "Does Parliament notice disasters, and whose?" Slug disaster-attention.

Tone: these are real deaths. Plain, respectful wording; no sensational language; no ranking of tragedies as
"worst"; deaths reported as the sources give them.

## Inputs
- raw_new12/hansard_monthly.json: Commons spoken contributions per month 1909-01 to 2026-10 (Hansard API
  timeline-stats). "plain" = phrase anywhere (about 74 disaster-site terms plus by-election seat names); "inp" =
  "in <place>" for the 1,661 places of Mentioned in the House. Months absent = 0.
- raw_new12/wiki_lists.json: "List of disasters in Great Britain and Ireland by death toll" (40 or more deaths).
- raw_new12/disasters_wd.tsv: Wikidata (CC0), 479 items, mostly murders and small events; deaths (P1120) for some.
- src6/hansard-places/data/places.csv: coordinates, nation, population and ambiguity flags of the 1,661 places.

Before writing the plan I looked at: the parsed Wikipedia list, the Wikidata list, which terms were harvested, the
ambiguity flags, and (to vet terms) the monthly series of about ten terms around their event dates (Aberfan,
Senghenydd, Lockerbie, Hillsborough, Marchioness, Grenfell, Hungerford, Dunblane). No model was run.

## Analysis plan (written before running any outcome model)

Question: when a localised disaster kills people in the UK, how much does the House of Commons talk about the place,
how fast does that attention fade, and does it scale with the death toll or with where the disaster happened?

### Event list (inclusion rules, set before outcomes)
1. Sources: (a) every row of the Wikipedia list dated 1909 or later; (b) Wikidata items with recorded deaths of 8 or
   more dated 1909 or later; (c) the events behind the disaster-site terms harvested in hansard_monthly "plain"
   (the lead chose these; their deaths are hand-coded from the event's Wikipedia article and verified online,
   marked deaths_src = "hand"). Robustness drops source (c).
2. Keep: a single, localised event on UK soil or in UK waters next to a named place (incl. Northern Ireland and
   Piper Alpha on the UK continental shelf): mining, rail, air crashes on UK soil, fires, explosions, crowd
   crushes, floods and landslides, bombings and shootings, and a local disease outbreak. Drop: pandemics,
   heatwaves, smogs, storms over wide areas, ships and naval losses at sea (no community place term), air crashes
   abroad, events outside today's UK (Isle of Man: Summerland; Republic of Ireland), serial murders, events with
   no deaths (Boscastle, Buncefield, Somerset Levels, Arkwright).
3. Window: event month m0 needs at least 12 months of data before it (data start 1909-01) and 60 months after
   (data end 2026-10). Events after 2021-10 are dropped.
4. Deaths: Wikipedia list figure if listed (lower bound of a range), else Wikidata P1120, else hand-coded. Recorded
   as the source gives it (some include perpetrators). Discrepancies listed. Robustness: Wikidata figure where both.
5. One term per event. Rule: if the place is a town among the 1,661 Hansard places and not flagged there (shared,
   namesake, or below-60% ordinary word), use "in <town>"; otherwise use the harvested plain phrase of the site
   (pit, station, stadium, village) when it is unambiguous. Every term is vetted by hand and given a flag:
   - "ambiguous": the word has another common meaning or place in debate in the window (Hillsborough: Hillsborough
     Castle and the 1985 Anglo-Irish Agreement; Deal; Bentley; Markham; Hull; Cumbria; Lofthouse later an MP's
     surname; Clydach two places). Excluded from the main sample; included in a robustness check.
   - "seat": the plain phrase is also a Commons seat name throughout the window (Easington, Lewisham, Bethnal
     Green): "Member for" and pre-2004 division lists add a roughly constant level, which the baseline removes.
     Kept in main; dropped in a robustness check. Plain seat-name phrases whose seat starts or ends inside the
     window are excluded (contaminated).
   - "city": the term is a whole city with a pre-event baseline of 30 or more contributions a month (defined on the
     pre-period only): too broad to register a local event. Excluded from main; included in robustness.
   - Events whose only possible term is London-wide ("in London") are excluded and the needed term is listed.
6. Duplicate place terms within 5 years (Whitehaven 1910 and 1947 are far apart; fine): if two events share a term
   and windows overlap, keep the one with more deaths and list the other.

### Outcome and measures
- n(e,k): contributions in month k relative to the event month (k = -24..+60) containing the event's term.
- Volume: V(t) = sum over all unflagged "in <place>" series in month t (sitting months, recesses and the long-run
  growth of Hansard). Expected count without the event: E(e,k) = b_e * V(t)/Vbar_pre(e), where b_e is the mean of
  n over k = -24..-1 (or the months available, at least 12) and Vbar_pre the mean V over the same months.
- Excess X(e,k) = n - E. Peak = sum of n over k = 0..2 (first quarter); cumulative 5-year count C = sum k = 0..59;
  cumulative excess CX = sum X over k = 0..59.
- Time to half: first month by which half of the 5-year positive cumulative excess has accrued (events with CX > 0).

### Hypotheses and what counts against them
- H1 (focusing event): attention rises after a disaster. Event-study ratio for k = 0..2 > 1. Against: CI includes 1.
- H2 (scaling): attention rises with the death toll, less than proportionally (Birkland; psychic numbing). Main
  model M1: PPML of C on log deaths + log(1 + expected count E summed over k = 0..59) + term kind (plain or in) +
  type FE (mining, transport, fire/explosion, crowd, attack, other) + era FE (1909-38, 1939-45, 1946-69, 1970-89,
  1990-2021); HC1 errors clustered by term. Elasticity b with 95% CI. Same for the peak P (k = 0..2) with log(1 + E
  over k = 0..2). Against H2: b CI includes 0 (no scaling); b >= 1 (proportional or more).
- H3 (fading, Downs): attention fades fast. Half-life from the event-study path: exponential fit of
  log(ratio - 1) on k for k >= 1 among months with ratio > 1, half-life = ln2/lambda, cluster bootstrap by event
  (500 draws) for the CI. Also the median time to half of the 5-year excess. Against: median time to half > 12
  months.
- H4 (whose disaster): conditional on deaths, type and era, (a) London and the South East vs the rest of England,
  (b) Scotland, Wales, Northern Ireland each vs England, (c) mining disasters vs other types. Added to M1 as
  indicators (M1g). Two-sided; report what is found. Against a metropolitan bias: (a) CI includes 0 or negative.
- Heterogeneity by type and era: from M1g coefficients and by-era elasticities (pre-1946 vs post-1946).
  Public inquiry: not coded (the lists do not record it), so left out.

### Event-study model (M2)
Stacked PPML: n(e,k) = exp(alpha_e + sum_bins beta_bin + log V(t)) (offset), bins: pre -24..-13 (reference),
-12..-7, -6..-4, -3..-1 (pre-trend test), then each month 0..12, 13-24, 25-36, 37-48, 49-60. Errors clustered by
event. Ratios exp(beta). Pre-trend: joint Wald test of the three pre bins.

### Robustness (pre-specified)
- R1 alternative specification: OLS of log(1 + max(CX, 0)) on the same covariates; PPML of C without the type and
  era FE; negative binomial for C.
- R2 sample: drop "seat" terms; add "ambiguous" and "city" terms; drop hand-coded-deaths events (sources a and b
  only); drop wartime events (1914-18, 1939-45); drop Northern Ireland Troubles events.
- R3 influence: leave one nation/region group out; leave one type out; drop the three largest death tolls; drop
  the largest attention (top C).
- R4 measurement: window 36 months; baseline 12 months; no volume adjustment (offset off; E = b * months);
  plain-phrase terms only and "in" terms only; swap to the other term where both exist; Wikidata deaths where both.
- R5 placebo: (i) fake event date 36 months before the real one (needs data 60 months before; outcome C over 24
  months after the fake date, ending 13 months before the real event): elasticity should be about 0; (ii)
  permutation: deaths shuffled across events 2,000 times, p-value for the M1 elasticity; (iii) pre-trend bins in M2.
- Everything else exploratory and labelled so.

### Design honesty
Observational. Lists are a filter of memory: the Wikipedia list keeps events with 40 or more deaths, and smaller
events are in only if Wikidata or the lead's term list carried them, which favours remembered events (selection on
the outcome for source c, hence R2). Hansard search depends on digitisation of old volumes. Counts are of
contributions, not judgements of anyone's response. Deaths are the recorded tolls; sources differ.

## Log
- Term rule clarified before any outcome model (the first run of 01_data.py printed the event measures, no model):
  the harvested plain phrase is used when it names the specific site (pit, village not in the town list, station,
  stadium, building, "Piper Alpha", "Morecambe Bay"); otherwise "in <town>" for a town in the list; otherwise the
  plain name of the village. Read literally, the first wording would have sent Grenfell, Moorgate and King's Cross
  to "in London".
- Easington: the plan assumed its seat name was constant; in fact Easington became a seat at the 1950 election,
  inside the window (series zero to April 1951, then 10 to 40 a month for years). By the plan's own rule
  (seat starting inside the window = contaminated) it is excluded; needs "Easington Colliery".
- First data run: 105 candidates, 66 included, 64 in the main sample (Hillsborough and Deal flagged ambiguous; no
  term reached the city threshold: Birmingham's baseline is 7.7 a month). "in <town>" terms often stay at or near
  zero after events that are discussed by their own name (Staines 0, Lockerbie 10 against 794 for the plain word,
  Faversham and Freckleton 0 in wartime). Very early events (Senghenydd 1, Pretoria Pit 1) are near zero too:
  Hansard search of the 1910s volumes finds few matches. Kept as planned; the R4 swap check matters here.

## Results of the planned analysis (first run)
- Main sample 64 events, 1910 to 2020, 4,346 deaths; 6,500 contributions in the five years after (60 events with at
  least one). Raw Spearman of deaths and 5-year count -0.06.
- M1 elasticity 0.42 [0.05, 0.78] (p = 0.027); peak (first quarter) 0.24 [-0.07, 0.56]. Permutation p (two-sided)
  0.069. Placebo (fake date 36 months earlier) 0.01 [-0.31, 0.34]. Fragile: CI crosses 0 in OLS, PPML without FE,
  NB, leave out London/SE, Scotland, Wales, bombings, mining, transport, drop the top-attention event, plain-only,
  in-only. Swap terms 0.35 [0.14, 0.56]. H2: positive and less than proportional in the planned model, not robust.
- M2: month 0 ratio 10.4 [2.4, 44.9], month 1 8.3, month 2 4.7, months 3 to 12 about 2.3 to 5; years 2 to 5 about 1.8
  to 2.2 with CIs including 1. Pre-trend p = 0.47. Half-life 25 months, bootstrap [5, 60]: imprecise. Per event:
  median time to half of 5-year excess 8.5 months (IQR 1 to 23); 31 of 54 within the first year. H3 supported by the
  planned criterion, with a long tail for a few events.
- H4: London and South East +255% [20, 947] vs rest of England; Wales +400% [-7, 2580]; Scotland +12%; NI -41% (n.s.).
  Mining vs other (M1m) +250% [-56, 2675], n.s. Fire or explosion +962% vs transport; 1990 to 2021 +318% vs 1970 to
  1989; 1939 to 1945 -84%.

## Exploratory (after seeing the planned results)
- King's Cross: the 1988 to 1992 rise in "King's Cross" also reflects the King's Cross Railways Bill (Channel Tunnel
  terminal) debates, a confound I missed when vetting. Dropping it: elasticity 0.60 [0.18, 1.01]. Kept in main as
  planned; reported.
- The London and South East premium rests on Grenfell and King's Cross together: dropping both, +39% [-20, 142];
  with the swapped terms, +40% [-34, 198]. Jackknife dropping any one London/SE event: all 15 stay above 0.
- Wikipedia-list events only (40 or more deaths, N = 31): elasticity 2.02 [0.84, 3.21]. The harvested small events
  (source c) were chosen because they are remembered, which flattens the slope: a selection-on-memory effect.

## References: verification (WebSearch/WebFetch, 2026)
35 references in the paper. Checked (authors, year, title, venue, volume, pages, DOI) on publisher, RePEc/IDEAS,
repository (ORCA, Cronfa, Strathprints, Southampton, VUB) or library records; abstracts read for every article cited
for a claim. DOIs printed only where a record stated them or the publisher identifier gave them. Downs (1972): issue
28 and first page 38 confirmed; end page 50 from standard citations. Vliegenthart et al. (2016) cited as "and others"
(full author order not confirmed). Galtung and Ruge, Adams (1986) and Cengiz et al. (2019) dropped (details or
abstract not confirmed). Claims about books (Kingdon, Baumgartner and Jones, Boin et al. 2005, Hood, Turner,
McLean and Johnes, Scraton) are kept general. Hand-coded death tolls checked on the events' Wikipedia articles,
the Wikipedia list of UK rail accidents and NMRS (Golborne). Journal limits: JPP 5,000 to 8,000 words body,
abstract 150 (CUP author instructions); British Politics 9,000 words excl. bibliography (Palgrave); Sherpa Romeo 8302.

## Deliverables
index.html + js/page.js + img/; header.png; data/ (events.csv, event_months.csv, models.csv, results.json,
site.json); code/01..08 + events.csv + refs.bib + templates + qa; release/paper (PDF 24 pp, ~7,700 words before
references, abstract 244 words, cover_note.md); release/blog (post.html, 6 figures, meta.json); release/zenodo;
reddit/ (collage.py + png, post.md, disaster_attention.gif; GIF script /home/claude/gifs/scripts/disaster-attention.py).
QA: qa/*.jpg at 1280 and 390 px, 0 console errors. Scratch deleted at the end.

## Referee review and extension (independent reviewer, 2026)
Checked: full reproduction from raw inputs (01 to 03 reproduced data/results.json, events.csv, models.csv and site.json
byte for byte before any change); every paper number is filled from results.json by 06_paper.py, so tables and text
agree by construction; numbers in page, blog, post.md, README, collage and GIF are filled from results.json (spot-read).

Extension (made after the first results; reported beside them, never in place of them). Source:
raw_new12/hansard_monthly_extra.json (same Hansard API, Commons, Spoken, monthly; 51 plain phrases; identical to
hansard_monthly.json wherever both have a term, asserted in common.hansard()). Same inclusion and term rules. Vetting:
- Added to the main sample (22): Easington Colliery, Low Moor, Chilwell, R.38 (airship's name), Bentley Colliery,
  Wharncliffe Woodmoor, Markham Colliery (1938 and 1973; windows do not overlap; same term, one cluster), Valleyfield,
  Sneyd, Fauld, Burngrange, Llandow, Chessell (Aquila Airways), Little Baldon, Penmaenpool, Hither Green, Claudy,
  Denmark Place, Ballykelly (Droppin Well), Ballygawley, Gleision. Markham 1973 death toll 18 (Wikipedia article,
  checked 2026). Seven have no matching contribution in the five years after.
- Included but flagged ambiguous (robustness only): Bourne End (two villages), Fernhill (several places; Gatwick is the
  airport), McGurk and Kingsmill (surnames; Kingsmill 391 contributions 1945 to 1959).
- Still excluded: Silvertown (seat 1918), M62 (motorway; 47 in the 24 months before), Hyde Park / Regent's Park (broad;
  "Hyde Park bomb" 0 and "Regent's Park bomb" 1 in the five years after), Manchester Airport (91 before), 7 July (a
  date) and 7/7 (342 matches before 2005), London Bridge (85 before).
- Code: events.csv columns ext, reason_v1; 01 writes include_v1/main_v1 and both summaries; 02 runs with
  DA_SAMPLE=v1|ext (models.csv / models_extension.csv); 03 keeps the first version at the top level of results.json
  and the extension under "ext". Paper tables 1 to 5 and figures stay the first version; new Section 7 and Tables 6
  (side by side) and 7 (phrase sensitivity); appendix event table lists the 86 with the added ones marked.
- Results, first version -> extension: N 64 -> 86; M1 elasticity 0.42 [0.05, 0.78] -> 0.52 [0.12, 0.92]; peak 0.24
  [-0.07, 0.56] -> 0.37 [0.04, 0.71]; permutation p 0.069 -> 0.006; checks with CI crossing 0: 12 of 28 -> 10 of 28;
  month 0 ratio 10.4 -> 11.1; median time to half 8.5 -> 5.5 months; London/SE +255% -> +248% (both fall to about
  +30 to 40%, CI crossing 0, without Grenfell and King's Cross); Wales +400% [-7, 2580] -> +295% [11, 1308] (not treated
  as a finding: 9 events, appears only in the extension, Wales vs all England crosses 0).
- Search-phrase sensitivity (added in review): disaster-specific phrases (Aberfan disaster, Gresford disaster,
  Hillsborough disaster, Grenfell Tower, King's Cross fire, Moorgate disaster, Clapham rail, plain Lockerbie) give
  0.53 [0.27, 0.79] (v1) and 0.60 [0.35, 0.85] (ext); counts differ by up to an order of magnitude by phrase.
Fixed in place: author line now "Dr Tristan Hotham"; abstract cut to 148 words (cover note targets JPP, limit 150) and
asserted; Garcia-Gavilanes claim corrected (strong drop over about 45 years, not "near zero"; many or zero deaths
remembered most); Downs bib volume 28; Walgrave and Van Aelst issue 1; Vliegenthart left as "and others" (full order
not confirmed); "sustained attention for their tolls" replaced by numbers; exclusion counts stated; cover note word
counts (prose about 6,200 words) and tables count; collage inset title moved off the axis and extension line added;
GIF final frame now has no highlight rings and a one-line subtitle; page shows all 86 with a dark outline and a layer
toggle for the added ones, extension paragraph and counts; blog extension paragraph.
References spot-checked online (2026): Birkland 1998, Downs 1972 (issue 28, p. 38), Eisensee and Stromberg 2007,
Stromberg 2007, Healy and Malhotra 2009, Garrett and Sobel 2003, Johnes 2000, Pantti and Wahl-Jorgensen 2011, Boin et
al. 2009, Pidgeon and O'Leary 2000, Slovic 2007, Fetherstonhaugh et al. 1997, Candia et al. 2019, Garcia-Gavilanes et
al. 2017, Jennings and John 2009, Walgrave and Van Aelst 2006, Vliegenthart et al. 2016, Eggers and Spirling 2014:
details and the claims made match the records/abstracts (publisher pages blocked; RePEc, repositories used).
Still open for a referee: a complete register of fatal incidents (selection on memory); content coding of
contributions; whether to make the extension the main sample in a resubmission; Downs end page 50 from standard
citations only; Policy Studies Journal and Disasters limits unconfirmed.
