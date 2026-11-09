"""Step 2: the planned models (NOTES.md): M1 elasticity of 5-year attention to deaths (PPML), peak model, group contrasts,
M2 stacked event study with half-life, robustness R1 to R5. Writes SCR/r2.json and data/models.csv."""
import warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20261109)
EV = pd.read_pickle(f"{SCR}/events.pkl")
PAN = pd.read_csv(f"{SCR}/panel.csv")
VOL = pd.read_csv(f"{SCR}/volume.csv").volume.values.astype(float)
VF = np.maximum(VOL, 1.0)
EV["ld"] = np.log(EV.deaths)
EV["plain"] = (EV.kind == "plain").astype(int)
EV["mining"] = (EV.type == "mining").astype(int)
if SAMPLE == "v1":                    # the first version: drop the events added in the extension
    EV = EV[EV.ext == 0].copy()
D0 = EV[EV.main == 1].copy()
print("sample", SAMPLE, len(D0), "events")
R = {}
MODELS = []
CTRL = "plain + C(typegrp, Treatment('Transport')) + C(era, Treatment('1970 to 1989'))"


def ppml(df, y, expo, extra="", ctrl=CTRL, label=None, keep=("ld",)):
    df = df.assign(Y=df[y].astype(float), EXP=df[expo].astype(float)).drop(columns=["C"], errors="ignore")
    f = "Y ~ ld + np.log1p(EXP)" + (f" + {ctrl}" if ctrl else "") + (f" + {extra}" if extra else "")
    m = smf.glm(f, data=df, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df.term)[0]}, maxiter=200)
    out = {"n": int(m.nobs), "label": label or y}
    for k in m.params.index:
        out[k] = {"b": float(m.params[k]), "se": float(m.bse[k]), "lo": float(m.conf_int().loc[k, 0]), "hi": float(m.conf_int().loc[k, 1]),
                  "p": float(m.pvalues[k])}
    MODELS.append(pd.DataFrame({"model": label or y, "term": m.params.index, "b": m.params.values, "se": m.bse.values, "p": m.pvalues.values, "n": int(m.nobs)}))
    return out, m


def el(o, k="ld"):
    v = o[k]
    return {"b": v["b"], "lo": v["lo"], "hi": v["hi"], "p": v["p"], "n": o["n"]}


def pc(v):  # coefficient -> % change
    return {"b": 100 * (math.exp(v["b"]) - 1), "lo": 100 * (math.exp(v["lo"]) - 1), "hi": 100 * (math.exp(v["hi"]) - 1), "p": v["p"]}


# ---------- descriptive
R["desc"] = {"n": int(len(D0)), "any_post": int((D0.C > 0).sum()), "zero_post": int((D0.C == 0).sum()),
             "C_total": int(D0.C.sum()), "C_median": float(D0.C.median()), "P_total": int(D0.P.sum()),
             "pos_excess": int((D0.CX > 0).sum()), "deaths_total": int(D0.deaths.sum()),
             "spearman_deaths_C": float(D0[["deaths", "C"]].corr("spearman").iloc[0, 1]),
             "spearman_deaths_CX": float(D0[["deaths", "CX"]].corr("spearman").iloc[0, 1]),
             "top_C": [{"id": r.id, "event": r.event, "term": r.term, "year": int(r.year), "deaths": int(r.deaths), "C": int(r.C), "E": round(float(r.E), 1),
                        "P": int(r.P), "peak": int(r.peak), "half_k": None if r.half_k != r.half_k else int(r.half_k)} for r in D0.sort_values("C", ascending=False).head(12).itertuples()]}
R["desc"]["top3_share_pc"] = 100 * D0.sort_values("C", ascending=False).head(3).C.sum() / D0.C.sum()

# ---------- M1 main, peak, groups
o, m = ppml(D0, "C", "E", label="M1"); R["M1"] = {"ld": el(o), "lE": el(o, "np.log1p(EXP)"), "plain": pc(o["plain"]), "n": o["n"], "all": o}
o, _ = ppml(D0, "P", "EP", label="M1 peak"); R["M1p"] = {"ld": el(o), "n": o["n"]}
o, _ = ppml(D0, "C", "E", extra="C(regiongrp, Treatment('Rest of England'))", label="M1 region groups")
R["M1g"] = {"ld": el(o), "n": o["n"]}
for g in ("London and South East", "Scotland", "Wales", "Northern Ireland"):
    R["M1g"][g] = pc(o[f"C(regiongrp, Treatment('Rest of England'))[T.{g}]"])
o, _ = ppml(D0, "C", "E", extra="C(nation, Treatment('England'))", label="M1 nations")
R["M1n"] = {"ld": el(o), "n": o["n"]}
for g in ("Scotland", "Wales", "Northern Ireland"):
    R["M1n"][g] = pc(o[f"C(nation, Treatment('England'))[T.{g}]"])
o, _ = ppml(D0, "C", "E", ctrl="plain + C(era, Treatment('1970 to 1989')) + mining", label="M1 mining")
R["M1m"] = {"ld": el(o), "mining": pc(o["mining"]), "n": o["n"]}
types = {}
for g in ("Mining", "Fire or explosion", "Crowd crush", "Bombing or shooting", "Other"):
    types[g] = pc(R["M1"]["all"][f"C(typegrp, Treatment('Transport'))[T.{g}]"])
R["M1"]["types"] = types
R["M1"]["eras"] = {e: pc(R["M1"]["all"][f"C(era, Treatment('1970 to 1989'))[T.{e}]"]) for _, _, e in ERAS if e != "1970 to 1989"}
D0["post46"] = (D0.year >= 1946).astype(int)
o, _ = ppml(D0, "C", "E", extra="ld:post46", label="M1 deaths x post-1946")
R["M1era"] = {"pre46": el(o), "diff": {"b": o["ld:post46"]["b"], "lo": o["ld:post46"]["lo"], "hi": o["ld:post46"]["hi"], "p": o["ld:post46"]["p"]},
              "post46_b": o["ld"]["b"] + o["ld:post46"]["b"], "n": o["n"]}
del R["M1"]["all"]


# ---------- recompute measures from the panel (robustness)
def remeasure(ids, which="main", shift=0, pre=PRE, post=POST, adj=True):
    out = {}
    for i in ids:
        g = PAN[(PAN.id == i) & (PAN.which == which)].set_index("k")
        if not len(g):
            continue
        ks = range(shift - pre, shift)
        ks = [k for k in ks if k in g.index]
        if len(ks) < MINPRE or (shift + post - 1) not in g.index:
            continue
        pn = g.loc[ks, "n"].values; pv = np.maximum(g.loc[ks, "volume"].values, 1.0)
        b = pn.mean()
        q = list(range(shift, shift + post))
        n = g.loc[q, "n"].values; v = np.maximum(g.loc[q, "volume"].values, 1.0)
        Ek = b * v / pv.mean() if adj else np.full(post, b)
        out[i] = {"C": n.sum(), "E": Ek.sum(), "P": n[:3].sum(), "EP": Ek[:3].sum(), "CX": (n - Ek).sum(), "term": g.term.iloc[0], "kind": g.kind.iloc[0]}
    return pd.DataFrame(out).T.reset_index().rename(columns={"index": "id"})


def with_measures(df, M):
    d = df.drop(columns=["C", "E", "P", "EP", "CX", "term", "kind"]).merge(M, on="id")
    for c in ("C", "E", "P", "EP", "CX"):
        d[c] = d[c].astype(float)
    d["plain"] = (d.kind == "plain").astype(int)
    return d


ROB = []


def add(label, df, y="C", expo="E", ctrl=CTRL, group="robust", extra=""):
    try:
        o, _ = ppml(df, y, expo, ctrl=ctrl, extra=extra, label=label)
        ROB.append(dict(label=label, group=group, **el(o)))
    except Exception as ex:
        print("FAILED", label, ex)


add("Main model (M1)", D0, group="main")
add("Peak: first three months", D0, y="P", expo="EP", group="main")
# R1 alternative specifications
d = D0.copy(); d["y"] = np.log1p(d.CX.clip(lower=0)); d["E5"] = d.E; d = d.drop(columns=["C"])
m = smf.ols(f"y ~ ld + np.log1p(E5) + {CTRL}", data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.term)[0]})
ROB.append(dict(label="OLS of log(1 + excess)", group="R1", b=m.params["ld"], lo=m.conf_int().loc["ld", 0], hi=m.conf_int().loc["ld", 1], p=m.pvalues["ld"], n=int(m.nobs)))
add("PPML without type and era", D0, ctrl="plain", group="R1")
try:
    nb = smf.negativebinomial(f"Y ~ ld + np.log1p(EXP) + {CTRL}", data=D0.assign(Y=D0.C, EXP=D0.E).drop(columns=["C"])).fit(disp=0, maxiter=500, cov_type="cluster", cov_kwds={"groups": pd.factorize(D0.term)[0]})
    ROB.append(dict(label="Negative binomial", group="R1", b=nb.params["ld"], lo=nb.conf_int().loc["ld", 0], hi=nb.conf_int().loc["ld", 1], p=nb.pvalues["ld"], n=int(nb.nobs)))
except Exception as ex:
    print("NB failed", ex)
# R2 sample
add("Drop seat-name terms", D0[D0.flag != "seat"], group="R2")
add("Add ambiguous terms", EV[(EV.include == 1)], group="R2")
add("Wikipedia list and Wikidata events only", D0[D0.source != "harvest"], group="R2")
add("Drop wartime events", D0[D0.war == 0], ctrl=CTRL.replace(" + C(era, Treatment('1970 to 1989'))", " + C(era, Treatment('1970 to 1989'))"), group="R2")
add("Drop Northern Ireland bombings and shootings", D0[D0.troubles == 0], group="R2")
add("Wikipedia list events only (40 or more deaths)", D0[D0.source == "list"], group="X")
# R3 influence
LOO = []
for g in sorted(D0.regiongrp.unique()):
    o, _ = ppml(D0[D0.regiongrp != g], "C", "E", label=f"Leave out {g}")
    LOO.append(dict(label=f"Leave out {g}", group="R3 region", **el(o)))
for g in sorted(D0.typegrp.unique()):
    dd = D0[D0.typegrp != g]
    ctrl = CTRL if g != "Transport" else CTRL.replace("Treatment('Transport')", "Treatment('Mining')")
    o, _ = ppml(dd, "C", "E", ctrl=ctrl, label=f"Leave out {g}")
    LOO.append(dict(label=f"Leave out {g.lower()}", group="R3 type", **el(o)))
ROB.extend(LOO)
top3 = D0.sort_values("deaths", ascending=False).head(3).id.tolist()
add("Drop the three largest death tolls", D0[~D0.id.isin(top3)], group="R3")
topc = D0.sort_values("C", ascending=False).head(1).id.tolist()
add("Drop the event with most attention", D0[~D0.id.isin(topc)], group="R3")
R["influence"] = {"top3_deaths": D0[D0.id.isin(top3)].event.tolist(), "top_attention": D0[D0.id.isin(topc)].event.tolist()}
# R4 measurement
add("Window 36 months", with_measures(D0, remeasure(D0.id, post=36)), group="R4")
add("Baseline 12 months", with_measures(D0, remeasure(D0.id, pre=12)), group="R4")
add("No volume adjustment", with_measures(D0, remeasure(D0.id, adj=False)), group="R4")
add("Plain-phrase terms only", D0[D0.kind == "plain"], ctrl=CTRL.replace("plain + ", ""), group="R4")
add("\"in\" terms only", D0[D0.kind == "in"], ctrl=CTRL.replace("plain + ", ""), group="R4")
sw = remeasure(D0.id, which="alt")
D_sw = with_measures(D0[D0.id.isin(sw.id)], sw)
D_sw = pd.concat([D_sw, D0[~D0.id.isin(sw.id)]])
add("Swap to the other term where one exists", D_sw, group="R4")
R["swap"] = {"n_swapped": int(len(sw)), "C_main_swapped": int(D0[D0.id.isin(sw.id)].C.sum()), "C_alt_swapped": int(sw.C.astype(float).sum())}
dw = D0.copy(); dw.loc[dw.deaths_wd == dw.deaths_wd, "ld"] = np.log(dw.deaths_wd)
add("Wikidata death toll where both", dw, group="R4")
# R5 placebo: fake date 36 months earlier, 24 months after it
pl = remeasure(D0.id, shift=-36, post=24)
D_pl = with_measures(D0[D0.id.isin(pl.id)], pl)
R["placebo"] = {"n": int(len(D_pl)), "C_total": int(D_pl.C.sum()), "any": int((D_pl.C > 0).sum())}
try:
    o, _ = ppml(D_pl, "C", "E", label="Placebo: fake date 36 months earlier")
    ROB.append(dict(label="Placebo: fake date 36 months earlier", group="R5", **el(o)))
except Exception as ex:
    print("placebo failed", ex)
    o, _ = ppml(D_pl, "C", "E", ctrl="plain", label="Placebo: fake date 36 months earlier (no FE)")
    ROB.append(dict(label="Placebo: fake date 36 months earlier (no FE)", group="R5", **el(o)))
real = R["M1"]["ld"]["b"]; perm = []
X = D0.assign(Y=D0.C, EXP=D0.E).drop(columns=["C"])
for _ in range(2000):
    X["ld"] = rng.permutation(D0.ld.values)
    try:
        mm = smf.glm(f"Y ~ ld + np.log1p(EXP) + {CTRL}", data=X, family=sm.families.Poisson()).fit(maxiter=100)
        perm.append(mm.params["ld"])
    except Exception:
        pass
perm = np.array(perm)
R["perm"] = {"draws": int(len(perm)), "p_two": float((np.abs(perm) >= abs(real)).mean()), "p_one": float((perm >= real).mean())}
# ---------- sensitivity to the search phrase (added in review): the disaster-specific phrase where one was harvested
ph = remeasure(EV[EV.id.isin(PHRASE)].id, which="phrase")
base = pd.concat([D0, EV[(EV.id == "hillsborough") & (EV.include == 1)]])
D_ph = pd.concat([with_measures(base[base.id.isin(ph.id)], ph), base[~base.id.isin(ph.id)]])
add("Disaster-specific phrase where one exists (adds Hillsborough)", D_ph, group="S")
R["phrase"] = {"n_swapped": int(len(ph)), "cases": {r.id: {"phrase": r.term, "C_phrase": int(float(r.C)), "P_phrase": int(float(r.P)),
               "C_main": None if EV[EV.id == r.id].C.iloc[0] != EV[EV.id == r.id].C.iloc[0] else int(EV[EV.id == r.id].C.iloc[0]),
               "term": EV[EV.id == r.id].term.iloc[0], "kind": EV[EV.id == r.id].kind.iloc[0]} for r in ph.itertuples()}}
# ---------- exploratory (added after the planned results were seen; labelled so)
add("Drop King's Cross (railway bill debates in the window)", D0[D0.id != "kingscross"], group="X")
XL = {}
for lab, dd in (("main", D0), ("drop King's Cross", D0[D0.id != "kingscross"]), ("drop Grenfell", D0[D0.id != "grenfell"]),
                ("drop Grenfell and King's Cross", D0[~D0.id.isin(["grenfell", "kingscross"])]), ("swap terms", D_sw)):
    o, _ = ppml(dd, "C", "E", extra="C(regiongrp, Treatment('Rest of England'))", label=f"Region groups, {lab}")
    XL[lab] = pc(o["C(regiongrp, Treatment('Rest of England'))[T.London and South East]"]); XL[lab]["n"] = o["n"]
jk = []
for i in D0[D0.regiongrp == "London and South East"].id:
    o, _ = ppml(D0[D0.id != i], "C", "E", extra="C(regiongrp, Treatment('Rest of England'))", label=f"jk {i}")
    jk.append({"id": i, **pc(o["C(regiongrp, Treatment('Rest of England'))[T.London and South East]"])})
XL["jackknife_min"] = min(jk, key=lambda d: d["b"]); XL["jackknife_max"] = max(jk, key=lambda d: d["b"])
XL["jackknife_sig"] = int(sum(1 for d in jk if d["lo"] > 0)); XL["jackknife_n"] = len(jk)
R["X_london"] = XL
R["robust"] = [{k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()} for r in ROB]
R["loro"] = [r for r in R["robust"] if r["group"].startswith("R3 ")]

# ---------- M2 stacked event study
BINS = [(-24, -13, "-24 to -13"), (-12, -7, "-12 to -7"), (-6, -4, "-6 to -4"), (-3, -1, "-3 to -1")] + [(k, k, str(k)) for k in range(0, 13)] + \
       [(13, 24, "13 to 24"), (25, 36, "25 to 36"), (37, 48, "37 to 48"), (49, 59, "49 to 59")]
MID = {lab: (a + b) / 2 for a, b, lab in BINS}


def es_frame(ids):
    p = PAN[(PAN.which == "main") & PAN.id.isin(ids) & PAN.k.between(-24, 59)].copy()
    tot = p.groupby("id").n.sum()
    p = p[p.id.isin(tot[tot > 0].index)]
    p["bin"] = ""
    for a, b, lab in BINS:
        p.loc[p.k.between(a, b), "bin"] = lab
    p["lv"] = np.log(np.maximum(p.volume, 1.0))
    return p


def es_fit(p, cluster=True):
    X = pd.get_dummies(p.bin).astype(float).drop(columns=["-24 to -13"])
    F = pd.get_dummies(p.id).astype(float)
    Z = pd.concat([X, F], axis=1)
    m = sm.GLM(p.n.values, Z.values, family=sm.families.Poisson(), offset=p.lv.values)
    r = m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(p.id)[0]}, maxiter=300) if cluster else m.fit(maxiter=300)
    nb = X.shape[1]
    return list(X.columns), r.params[:nb], (r.bse[:nb] if cluster else None), r, nb


def halflife(cols, b):
    pts = [(MID[c], v) for c, v in zip(cols, b) if MID[c] >= 1 and math.exp(v) > 1]
    if len(pts) < 3:
        return None
    x = np.array([q[0] for q in pts]); y = np.log(np.exp([q[1] for q in pts]) - 1)
    lam = -np.polyfit(x, y, 1)[0]
    return math.log(2) / lam if lam > 0 else None


p = es_frame(D0.id)
cols, b, se, res, nb = es_fit(p)
V = res.cov_params()[:nb, :nb]
es = [{"bin": c, "mid": MID[c], "b": float(bb), "ratio": math.exp(bb), "lo": math.exp(bb - 1.96 * s), "hi": math.exp(bb + 1.96 * s), "p": float(pv)}
      for c, bb, s, pv in zip(cols, b, se, res.pvalues[:nb])]
order = [lab for _, _, lab in BINS if lab != "-24 to -13"]
es = sorted(es, key=lambda d: order.index(d["bin"]))
pre_ix = [cols.index(c) for c in ("-12 to -7", "-6 to -4", "-3 to -1")]
bb = np.asarray(b)[pre_ix]; VV = V[np.ix_(pre_ix, pre_ix)]
wald = float(bb @ np.linalg.inv(VV) @ bb)
from scipy import stats
hl = halflife(cols, b)
boots = []
ids = p.id.unique()
for _ in range(500):
    s = rng.choice(ids, len(ids), replace=True)
    q = pd.concat([p[p.id == i].assign(id=f"{i}_{j}") for j, i in enumerate(s)])
    try:
        c2, b2, _, _, _ = es_fit(q, cluster=False)
        h = halflife(c2, b2)
        boots.append(h if h is not None else np.nan)
    except Exception:
        boots.append(np.nan)
boots = np.array(boots, dtype=float)
R["M2"] = {"n_events": int(p.id.nunique()), "n_obs": int(len(p)), "bins": es, "pretrend_chi2": wald, "pretrend_df": 3,
           "pretrend_p": float(1 - stats.chi2.cdf(wald, 3)),
           "halflife": hl, "halflife_lo": float(np.nanpercentile(boots, 2.5)), "halflife_hi": float(np.nanpercentile(boots, 97.5)),
           "boot_ok": int(np.isfinite(boots).sum())}
R["M2"]["k0"] = next(d for d in es if d["bin"] == "0"); R["M2"]["k1"] = next(d for d in es if d["bin"] == "1")
R["M2"]["k0_2"] = [next(d for d in es if d["bin"] == str(k)) for k in range(3)]
R["M2"]["late"] = next(d for d in es if d["bin"] == "49 to 59")
R["M2"]["y2"] = next(d for d in es if d["bin"] == "13 to 24")

# time to half, per event
pos = D0[D0.CX > 0]
R["half"] = {"n": int(len(pos)), "median": float(pos.half_k.median()), "q1": float(pos.half_k.quantile(.25)), "q3": float(pos.half_k.quantile(.75)),
             "within12": int((pos.half_k <= 11).sum()), "within12_pc": 100 * float((pos.half_k <= 11).mean()),
             "pooled_first12_pc": 100 * float((pos.first12_share * pos.CX).sum() / pos.CX.sum()),
             "median_first12_pc": 100 * float(pos.first12_share.median())}

# attention per death (descriptive, for the map)
D0["xpd"] = D0.CX.clip(lower=0) / D0.deaths
R["per_death"] = {"median": float(D0.xpd.median())}
pd.concat(MODELS).round(5).to_csv(f"{DATA}/models.csv" if SAMPLE == "v1" else f"{DATA}/models_extension.csv", index=False)
jsave(R, f"{SCR}/r2_{SAMPLE}.json", indent=1)
print(json.dumps({k: R[k] for k in ("M1", "M1p", "M1g", "M1n", "M1m", "M1era", "perm", "half", "placebo", "swap")}, indent=0, default=str)[:4000])
print("M2", R["M2"]["pretrend_p"], R["M2"]["halflife"], R["M2"]["halflife_lo"], R["M2"]["halflife_hi"])
for e in es: print(e["bin"], round(e["ratio"], 2), round(e["lo"], 2), round(e["hi"], 2))
for r in R["robust"]: print(f"{r['label']:55s} {r['b']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}] n={r['n']}")
