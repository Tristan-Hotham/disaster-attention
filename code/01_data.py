"""Step 1: the event list, nation and region, the monthly series of each event's term and the attention measures.
Outputs: data/events.csv (one row per event, included and excluded, with measures), data/event_months.csv (event x month
panel k = -24..59 for the included events), SCR/panel.csv (k = -60..59, with the alternative terms) and SCR/r1.json."""
import numpy as np, pandas as pd
from shapely.geometry import Point
from common import *

H = hansard()
P = pd.read_csv(os.path.join(HP, "places.csv"))
E = pd.read_csv(os.path.join(ROOT, "code", "events.csv"), dtype={"term": str, "flag": str, "kind": str})
E["flag"] = E.flag.fillna(""); E["reason_v1"] = E.reason_v1.fillna(""); E["reason"] = E.reason.fillna(""); E["term"] = E.term.fillna(""); E["kind"] = E.kind.fillna("")
assert E.id.is_unique
R = {}

# ---------- volume: all unflagged "in <place>" series, per month
clean = set(P.loc[P.flag.isna(), "term"])
V = np.zeros(T1 - T0 + 1)
for t, s in H["inp"].items():
    if t in clean:
        for k, n in s.items():
            y, m = map(int, k.split("-"))
            if T0 <= mi(y, m) <= T1:
                V[mi(y, m) - T0] += n
R["volume"] = {"n_places": len(clean), "total": int(V.sum()), "months": int(len(V)), "zero_months": int((V == 0).sum())}
# a month with no sittings has V = 0; floor at 1 so the offset stays finite (those months get E = 0 anyway)
Vf = np.maximum(V, 1.0)
pd.DataFrame({"month": [ym(T0 + i) for i in range(len(V))], "volume": V.astype(int)}).to_csv(f"{SCR}/volume.csv", index=False)


def series(term, kind):
    s = H["plain" if kind == "plain" else "inp"].get(term)
    if s is None:
        return None
    a = np.zeros(T1 - T0 + 1)
    for k, n in s.items():
        y, m = map(int, k.split("-"))
        if T0 <= mi(y, m) <= T1:
            a[mi(y, m) - T0] = n
    return a


# ---------- nation and region
REG = topo_polys("rgn"); CTRY = topo_polys("ctry")


def where(lat, lon):
    p = Point(lon, lat)
    c = min(CTRY, key=lambda k: CTRY[k].distance(p))
    if c != "England":
        return c, c
    r = min(REG, key=lambda k: REG[k].distance(p))
    return c, r


E[["nation", "region"]] = [where(a, b) for a, b in zip(E.lat, E.lon)]
E["regiongrp"] = np.where(E.region.isin(["London", "South East"]), "London and South East",
                          np.where(E.nation == "England", "Rest of England", E.nation))
E["date"] = pd.to_datetime(E.date)
E["year"] = E.date.dt.year
E["t0"] = [mi(d.year, d.month) for d in E.date]
E["era"] = E.year.map(era)
E["typegrp"] = E.type.map(TYPEGRP)
E["war"] = (E.year.between(1914, 1918) | E.year.between(1939, 1945)).astype(int)
E["troubles"] = ((E.nation == "Northern Ireland") & (E.type == "violence")).astype(int)
E["mining"] = (E.type == "mining").astype(int)


def measures(a, t0, pre=PRE, post=POST, adj=True):
    """baseline, expected and observed counts for an event at month index t0 (absolute)"""
    i0 = t0 - T0
    lo = max(0, i0 - pre)
    if i0 - lo < MINPRE or i0 + post - 1 > len(a) - 1:
        return None
    pre_n = a[lo:i0]; pre_v = Vf[lo:i0]
    b = pre_n.mean()
    post_n = a[i0:i0 + post]; post_v = Vf[i0:i0 + post]
    Ek = b * post_v / pre_v.mean() if adj else np.full(post, b)
    X = post_n - Ek
    cx = X.sum()
    half = None
    if cx > 0:
        cum = np.cumsum(X)
        half = int(np.argmax(cum >= 0.5 * cx))
    return {"pre_months": int(i0 - lo), "b": float(b), "pre_sum": float(pre_n.sum()), "C": float(post_n.sum()), "E": float(Ek.sum()),
            "P": float(post_n[:3].sum()), "EP": float(Ek[:3].sum()), "CX": float(cx), "PX": float((post_n[:3] - Ek[:3]).sum()),
            "peak": float(post_n.max()), "peak_k": int(post_n.argmax()), "half_k": half,
            "C12": float(post_n[:12].sum()), "E12": float(Ek[:12].sum()), "first12_share": float(X[:12].sum() / cx) if cx > 0 else None}


rows = []
for r in E.itertuples():
    out = {"id": r.id}
    if r.include == 1 and r.term:
        a = series(r.term, r.kind)
        assert a is not None, r.term
        m = measures(a, r.t0)
        assert m is not None, r.id
        out.update(m)
        out["total_1909_2026"] = int(a.sum())
    rows.append(out)
M = pd.DataFrame(rows)
E = E.merge(M, on="id", how="left")
E["city"] = ((E.kind == "in") & (E.b >= CITY)).astype(int)
E.loc[E.city == 1, "flag"] = E.loc[E.city == 1, "flag"].where(E.loc[E.city == 1, "flag"] != "", "city")
E["main"] = ((E.include == 1) & (~E.flag.isin(["ambiguous", "city"]))).astype(int)
# first version (before the extension): the ext rows were all excluded for want of a term
E["include_v1"] = ((E.include == 1) & (E.ext == 0)).astype(int)
E["main_v1"] = ((E.main == 1) & (E.ext == 0)).astype(int)
E["any_list"] = (E.source != "harvest").astype(int)
print(E.loc[E.include == 1, ["id", "term", "kind", "flag", "deaths", "b", "C", "E", "P", "CX", "half_k", "regiongrp", "main"]].to_string())

# ---------- panel k = -60..59 (main term and the alternative term)
pan = []
for r in E[E.include == 1].itertuples():
    for which, (term, kind) in (("main", (r.term, r.kind)), ("alt", ALT.get(r.id, (None, None))),
                                ("phrase", (PHRASE[r.id], "plain") if r.id in PHRASE else (None, None))):
        if term is None:
            continue
        a = series(term, kind)
        if a is None:
            print("no alt series", r.id, term, kind); continue
        i0 = r.t0 - T0
        for k in range(-60, POST):
            i = i0 + k
            if 0 <= i < len(a):
                pan.append((r.id, which, term, kind, k, ym(T0 + i), a[i], V[i]))
PAN = pd.DataFrame(pan, columns=["id", "which", "term", "kind", "k", "month", "n", "volume"])
PAN.to_csv(f"{SCR}/panel.csv", index=False)
inc = E[E.include == 1]
em = PAN[(PAN.which == "main") & PAN.k.between(-PRE, POST - 1)].merge(inc[["id", "b"]], on="id")
em[["id", "term", "kind", "k", "month", "n", "volume"]].to_csv(f"{DATA}/event_months.csv", index=False)

# ---------- summary of the list, for the first version (v1) and the extension (ext)
def summary(inc_col, main_col, reason_col, pat="no term|London-wide|city term only"):
    inc = E[E[inc_col] == 1]; ex = E[E[inc_col] == 0]; mm = E[E[main_col] == 1]
    S = {"candidates": int(len(E)), "included": int(len(inc)), "main": int(len(mm)), "excluded": int(len(ex)),
         "flag_ambiguous": int((inc.flag == "ambiguous").sum()), "flag_city": int((inc.flag == "city").sum()),
         "flag_seat": int((inc.flag == "seat").sum()),
         "src_list": int((inc.source == "list").sum()), "src_wikidata": int((inc.source == "wikidata").sum()),
         "src_harvest": int((inc.source == "harvest").sum()),
         "kind_plain": int((mm.kind == "plain").sum()), "kind_in": int((mm.kind == "in").sum()),
         "excl_no_term": int(ex[reason_col].str.contains(pat).sum()),
         "deaths_main_total": int(mm.deaths.sum()), "deaths_main_median": float(mm.deaths.median()),
         "year_min": int(mm.year.min()), "year_max": int(mm.year.max()),
         "wd_rows": int(sum(1 for _ in open(os.path.join(RAW, "disasters_wd.tsv"))) - 1)}
    S["by_type"] = mm.typegrp.value_counts().to_dict()
    S["by_regiongrp"] = mm.regiongrp.value_counts().to_dict()
    S["by_era"] = mm.era.value_counts().to_dict()
    S["deaths_disagree"] = [{"id": r.id, "event": r.event, "list": int(r.deaths), "wikidata": int(r.deaths_wd)}
                            for r in E[E[inc_col] == 1].itertuples() if r.deaths_wd == r.deaths_wd and r.deaths == r.deaths and r.deaths != r.deaths_wd]
    S["needed_terms"] = [{"id": r.id, "event": r.event, "year": int(r.year), "deaths": None if r.deaths != r.deaths else int(r.deaths), "reason": getattr(r, reason_col)}
                         for r in ex.itertuples()]
    return S


inc = E[E.include == 1]
R["events"] = summary("include_v1", "main_v1", "reason_v1")
R["events_ext"] = summary("include", "main", "reason", pat="no term|London-wide|city term only|broad|names the|is a date|seat name in 1918")
added = E[E.ext == 1]
R["events_ext"]["added_included"] = int(added.include.sum()); R["events_ext"]["added_main"] = int(added.main.sum())
R["events_ext"]["added_ambiguous"] = int(((added.include == 1) & (added.flag == "ambiguous")).sum())
R["events_ext"]["added_deaths"] = int(added.loc[added.main == 1, "deaths"].sum())
R["events_ext"]["added_zero"] = int(((added.main == 1) & (added.C == 0)).sum())
R["events_ext"]["added_list"] = [{"id": r.id, "event": r.event, "year": int(r.year), "deaths": int(r.deaths), "term": r.term, "flag": r.flag, "C": int(r.C)}
                                 for r in added[added.include == 1].sort_values("date").itertuples()]
keep = ["id", "event", "date", "year", "deaths", "deaths_src", "deaths_wd", "type", "typegrp", "term", "kind", "flag", "lat", "lon",
        "coord_src", "nation", "region", "regiongrp", "era", "war", "troubles", "source", "include", "main", "reason", "ext", "include_v1", "main_v1", "reason_v1",
        "pre_months", "b", "pre_sum", "C", "E", "P", "EP", "CX", "PX", "peak", "peak_k", "half_k", "C12", "first12_share", "total_1909_2026"]
out = E[keep].copy(); out["date"] = out.date.dt.strftime("%Y-%m-%d")
out.round(3).to_csv(f"{DATA}/events.csv", index=False)
out.to_pickle(f"{SCR}/events.pkl")
jsave(R, f"{SCR}/r1.json", indent=1)
for k in ("events", "events_ext"):
    print(k, json.dumps({a: v for a, v in R[k].items() if a not in ("needed_terms", "added_list")}, indent=0)[:1500])
