"""Step 3: data/results.json (every number quoted anywhere) and the page data data/site.json."""
import numpy as np, pandas as pd
from common import *

R1 = jload(f"{SCR}/r1.json"); R2 = jload(f"{SCR}/r2_v1.json"); R2x = jload(f"{SCR}/r2_ext.json")
R = {"data": R1}
R.update(R2)                     # the first version (pre-specified analysis on the events searchable at the time)
EV = pd.read_pickle(f"{SCR}/events.pkl"); EV["date"] = pd.to_datetime(EV.date)
EM = pd.read_csv(f"{DATA}/event_months.csv")


# ---------- prose numbers (all derived here, nothing typed by hand)
def prose(R, D0):
  m1 = R["M1"]["ld"]
  pr = {}
  pr["el_double_pc"] = 100 * (2 ** m1["b"] - 1)
  pr["el_double_lo"] = 100 * (2 ** m1["lo"] - 1)
  pr["el_double_hi"] = 100 * (2 ** m1["hi"] - 1)
  pr["el_10x_pc"] = 100 * (10 ** m1["b"] - 1)
  rob = [r for r in R["robust"] if r["group"] not in ("main", "X", "R5", "S")]
  pr["n_checks"] = len(rob)
  pr["n_checks_pos"] = sum(1 for r in rob if r["lo"] > 0)
  pr["n_checks_cross"] = sum(1 for r in rob if r["lo"] <= 0)
  pr["checks_b_min"] = min(r["b"] for r in rob); pr["checks_b_max"] = max(r["b"] for r in rob)
  pl = next(r for r in R["robust"] if r["group"] == "R5")
  pr["placebo_b"] = pl["b"]; pr["placebo_lo"] = pl["lo"]; pr["placebo_hi"] = pl["hi"]
  es = {d["bin"]: d for d in R["M2"]["bins"]}
  pr["m0"] = es["0"]["ratio"]; pr["m0_lo"] = es["0"]["lo"]; pr["m0_hi"] = es["0"]["hi"]
  pr["m1"] = es["1"]["ratio"]; pr["m2"] = es["2"]["ratio"]; pr["m3"] = es["3"]["ratio"]
  pr["m3_12_min"] = min(es[str(k)]["ratio"] for k in range(3, 13)); pr["m3_12_max"] = max(es[str(k)]["ratio"] for k in range(3, 13))
  late = [es[b] for b in ("13 to 24", "25 to 36", "37 to 48", "49 to 59")]
  pr["late_min"] = min(d["ratio"] for d in late); pr["late_max"] = max(d["ratio"] for d in late)
  pr["late_all_cross"] = int(all(d["lo"] < 1 for d in late))
  pr["pre_min"] = min(es[b]["ratio"] for b in ("-12 to -7", "-6 to -4", "-3 to -1"))
  pr["pre_max"] = max(es[b]["ratio"] for b in ("-12 to -7", "-6 to -4", "-3 to -1"))
  pr["first_sig_cross"] = next(k for k in range(0, 13) if es[str(k)]["lo"] < 1)
  X = R["X_london"]
  pr["london_b"] = R["M1g"]["London and South East"]["b"]; pr["london_x"] = 1 + pr["london_b"] / 100
  pr["london_drop2_b"] = X["drop Grenfell and King's Cross"]["b"]
  pr["london_swap_b"] = X["swap terms"]["b"]
  pr["listonly"] = next(r for r in R["robust"] if r["label"].startswith("Wikipedia list events only"))
  pr["dropkx"] = next(r for r in R["robust"] if r["label"].startswith("Drop King's Cross"))
  pr["swap"] = next(r for r in R["robust"] if r["label"].startswith("Swap"))
  pr["half_med"] = R["half"]["median"]
  pr["harvest_median_deaths"] = float(D0[D0.source == "harvest"].deaths.median())
  pr["list_median_deaths"] = float(D0[D0.source == "list"].deaths.median())
  by = D0.groupby("regiongrp").agg(n=("id", "size"), deaths=("deaths", "sum"), C=("C", "sum"), CX=("CX", "sum")).reset_index()
  pr["by_region"] = {r.regiongrp: {"n": int(r.n), "deaths": int(r.deaths), "C": int(r.C), "CX": round(float(r.CX), 1)} for r in by.itertuples()}
  byt = D0.groupby("typegrp").agg(n=("id", "size"), deaths=("deaths", "sum"), C=("C", "sum")).reset_index()
  pr["by_type"] = {r.typegrp: {"n": int(r.n), "deaths": int(r.deaths), "C": int(r.C)} for r in byt.itertuples()}
  KEYS = {"ols": "OLS of log", "noFE": "PPML without", "nb": "Negative binomial", "dropseat": "Drop seat", "addamb": "Add ambiguous", "nohand": "Wikipedia list and Wikidata",
          "nowar": "Drop wartime", "noNI": "Drop Northern Ireland", "top3": "Drop the three", "topatt": "Drop the event with most", "w36": "Window 36", "b12": "Baseline 12",
          "novol": "No volume", "plain": "Plain-phrase", "in": "\"in\" terms", "swap": "Swap", "wd": "Wikidata death"}
  pr["rb"] = {k: next(r for r in R["robust"] if r["label"].startswith(v)) for k, v in KEYS.items()}
  pr["n_flagged_places"] = 1661 - R1["volume"]["n_places"]
  return pr


D0 = EV[EV.main_v1 == 1]; D0x = EV[EV.main == 1]
pr = prose(R, D0)
R["prose"] = pr
R["perm"]["p_two_pc"] = 100 * R["perm"]["p_two"]
# the extension: same plan, events added after the first results (code/events.csv ext = 1)
X2 = dict(R2x); X2["prose"] = prose(R2x, D0x); X2["perm"]["p_two_pc"] = 100 * X2["perm"]["p_two"]
X2["events"] = R1["events_ext"]
for k in ("M1", "M1p", "M1g", "M1n", "M1m"):
    X2["d_" + k] = X2[k]["ld"]["b"] - R[k]["ld"]["b"]
R["ext"] = X2
R["phrase"]["sens"] = next(r for r in R["robust"] if r["group"] == "S")
R["phrase"]["sens_ext"] = next(r for r in X2["robust"] if r["group"] == "S")

# named events used in the text
cases = {}
for i in ("grenfell", "kingscross", "aberfan", "piperalpha", "gresford", "senghenydd", "pretoria", "quintinshill", "lockerbie", "dunblane",
          "hungerford", "staines", "faversham", "freckleton", "grayrigg", "hixon", "enniskillen", "morecambe", "arena", "lewisham", "bethnalgreen",
          "flixborough", "birmingham", "hillsborough", "bradford", "ibrox", "harrow", "moorgate", "omagh", "carmont", "clapham", "ladbroke", "easington",
          "droppinwell", "hithergreen", "gleision", "fauld", "lowmoor", "chilwell"):
    r = EV[EV.id == i].iloc[0]
    cases[i] = {"event": r.event, "year": int(r.year), "deaths": int(r.deaths), "term": r.term, "kind": r.kind,
                "C": None if r.C != r.C else int(r.C), "E": None if r.E != r.E else round(float(r.E), 1),
                "P": None if r.P != r.P else int(r.P), "CX": None if r.CX != r.CX else round(float(r.CX), 1),
                "peak": None if r.peak != r.peak else int(r.peak), "half_k": None if r.half_k != r.half_k else int(r.half_k),
                "main": int(r.main), "flag": r.flag}
R["cases"] = cases
# plain-word totals for the swapped terms quoted in the text
H = hansard()
def win(term, kind, d):
    s = H["plain" if kind == "plain" else "inp"].get(term, {})
    t0 = mi(d.year, d.month)
    return int(sum(v for k, v in s.items() if t0 <= mi(*map(int, k.split("-"))) < t0 + POST))
R["swapcases"] = {i: {"term": ALT[i][0], "kind": ALT[i][1], "C": win(*ALT[i], EV[EV.id == i].date.iloc[0])} for i in ("lockerbie", "hungerford", "dunblane")}

# ---------- consistency checks for statements in the text
assert R["M1"]["ld"]["lo"] > 0 and R["M1"]["ld"]["hi"] < 1          # positive, less than proportional
assert pr["n_checks_cross"] >= 5                                      # "not robust"
assert R["perm"]["p_two"] > 0.05                                      # permutation not significant at 5%
assert abs(pr["placebo_b"]) < 0.1 and pr["placebo_lo"] < 0
assert R["M2"]["pretrend_p"] > 0.1
assert pr["late_all_cross"] == 1
assert R["half"]["median"] <= 12
X = R["X_london"]
assert R["M1g"]["London and South East"]["lo"] > 0 and X["drop Grenfell and King's Cross"]["lo"] < 0 and X["swap terms"]["lo"] < 0
for g in ("Scotland", "Wales", "Northern Ireland"):
    assert R["M1g"][g]["lo"] < 0 < R["M1g"][g]["hi"], g
assert R["M1m"]["mining"]["lo"] < 0
assert R["desc"]["spearman_deaths_C"] < 0.1
# statements about the extension (written after both runs were seen)
x, xp = R["ext"], R["ext"]["prose"]
assert x["M1"]["ld"]["lo"] > 0 and x["M1"]["ld"]["hi"] < 1 and x["M1"]["ld"]["b"] > R["M1"]["ld"]["b"]
assert x["M1p"]["ld"]["lo"] > 0 > R["M1p"]["ld"]["lo"]                # peak: significant only in the extension
assert x["perm"]["p_two"] < 0.05 < R["perm"]["p_two"]                  # permutation: significant only in the extension
assert xp["n_checks_cross"] >= 5 and xp["n_checks"] == pr["n_checks"]  # still not robust
assert x["M1g"]["London and South East"]["lo"] > 0 and x["X_london"]["drop Grenfell and King's Cross"]["lo"] < 0 and x["X_london"]["swap terms"]["lo"] < 0
assert x["M1g"]["Wales"]["lo"] > 0 > R["M1g"]["Wales"]["lo"]          # Wales: excludes zero only in the extension
for g in ("Scotland", "Northern Ireland"):
    assert x["M1g"][g]["lo"] < 0 < x["M1g"][g]["hi"], g
assert x["M1m"]["mining"]["lo"] < 0 and abs(xp["placebo_b"]) < 0.1 and xp["placebo_lo"] < 0
assert x["M2"]["pretrend_p"] > 0.1 and xp["late_all_cross"] == 1 and x["half"]["median"] <= 12
lw = next(r for r in x["robust"] if r["label"] == "Leave out Wales")
assert lw["lo"] < 0

# ---------- page data
S = {"events": [], "excluded": []}
for r in EV.itertuples():
    if r.include == 1:
        e = EM[EM.id == r.id].sort_values("k")
        S["events"].append({"id": r.id, "n": r.event, "d": r.date.strftime("%Y-%m-%d"), "y": int(r.year), "dt": int(r.deaths), "src": r.deaths_src,
                            "ty": r.type, "tg": r.typegrp, "t": r.term, "kd": r.kind, "fl": r.flag, "lat": round(float(r.lat), 4), "lon": round(float(r.lon), 4),
                            "na": r.nation, "rg": r.region, "m": int(r.main), "b": round(float(r.b), 2), "C": int(r.C), "E": round(float(r.E), 1),
                            "P": int(r.P), "X": round(float(r.CX), 1), "xpd": round(max(float(r.CX), 0) / r.deaths, 2), "h": None if r.half_k != r.half_k else int(r.half_k),
                            "x": int(r.ext), "m1": int(r.main_v1), "s": [int(v) for v in e.n.values]})
    else:
        S["excluded"].append({"n": r.event, "y": int(r.year), "dt": None if r.deaths != r.deaths else int(r.deaths), "why": r.reason,
                              "lat": round(float(r.lat), 4), "lon": round(float(r.lon), 4)})
jsave(S, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results.json", os.path.getsize(f"{DATA}/results.json") // 1024, "KB; site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
print(json.dumps({k: v for k, v in pr.items() if not isinstance(v, dict)}, indent=0))
print(R["swapcases"])
