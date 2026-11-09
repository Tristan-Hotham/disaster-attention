"""Step 4: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background, quiet colours: these are real deaths."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.ops import transform as stransform
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE, LAND, SEA = "#F6F1E6", "#24211D", "#6B655B", "#DCD3C2", "#E6DFD0", "#F6F1E6"
ACC, ACC2, GREY = "#8C3B2E", "#2F5F7A", "#B9B2A5"
TCOL = {"Mining": "#4A4038", "Transport": "#2F6A9E", "Fire or explosion": "#B4652E", "Crowd crush": "#7A4FA0",
        "Bombing or shooting": "#A23B4B", "Other": "#3B8B6A"}
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3.2, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
EV = pd.read_csv(f"{DATA}/events.csv")
D0 = EV[EV.main_v1 == 1].copy()       # paper figures: the first version (pre-specified)
EM = pd.read_csv(f"{DATA}/event_months.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
SRC = "Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia; Wikidata (CC0). maps.tristanhotham.com/disaster-attention"


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.058, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.015, s, fontsize=8.5, family=MONO, color=MUT)


# ---------- 1. event study
es = R["M2"]["bins"]
fig = plt.figure(figsize=(11, 7.2))
title(fig, "A sharp rise, then a long, low tail",
      f"Commons contributions naming the place, relative to its own level two years before (Poisson event study, {R['M2']['n_events']} disasters; 95% intervals)")
ax = fig.add_axes([0.08, 0.14, 0.88, 0.66])
xs = [d["mid"] for d in es]; ys = [d["ratio"] for d in es]
for d in es:
    w = 0.32 if d["bin"].lstrip("-").isdigit() else (abs(eval(d["bin"].split(" to ")[1]) - eval(d["bin"].split(" to ")[0])) / 2)
    ax.plot([d["mid"], d["mid"]], [d["lo"], d["hi"]], color=ACC if d["mid"] >= 0 else GREY, lw=2, solid_capstyle="round", zorder=2)
    if not d["bin"].lstrip("-").isdigit():
        ax.plot([d["mid"] - w, d["mid"] + w], [d["ratio"]] * 2, color=ACC if d["mid"] >= 0 else MUT, lw=3, zorder=3)
ax.scatter(xs, ys, s=38, color=[ACC if x >= 0 else MUT for x in xs], zorder=4, edgecolor=PAPER, lw=0.8)
ax.plot([-18.5, -18.5 + 5.5], [1, 1], color=MUT, lw=3)
ax.axhline(1, color=INK, lw=0.9); ax.axvline(-0.5, color=RULE, lw=1, ls=(0, (3, 3)))
ax.set_yscale("log"); ax.set_ylim(0.3, 60)
ax.set_yticks([0.5, 1, 2, 5, 10, 20, 50]); ax.set_yticklabels(["½", "1", "2", "5", "10", "20", "50"])
ax.set_xlim(-25, 61); ax.set_xticks([-24, -12, 0, 12, 24, 36, 48, 60])
ax.set_xlabel("Months from the disaster"); ax.set_ylabel("Times the usual level (log scale)")
ax.grid(axis="y", color=RULE, lw=0.6)
k0 = R["M2"]["k0"]
ax.annotate(f"Month of the disaster: {k0['ratio']:.1f} times the usual level", (0, k0["ratio"]), (6, 32), fontsize=11.5, color=INK,
            arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8), path_effects=HALO)
ax.text(36, 3.6, f"Years two to five: about {R['prose']['late_min']:.1f} to {R['prose']['late_max']:.1f} times,\nintervals include no change", fontsize=11, color=MUT, ha="center", path_effects=HALO)
ax.text(-18.5, 0.42, "reference: months -24 to -13", fontsize=10, color=MUT, ha="left")
foot(fig); out(fig, "event")

# ---------- 2. deaths against attention
fig = plt.figure(figsize=(11, 8))
title(fig, "Attention follows the death toll only loosely",
      f"Each dot is a disaster: deaths against Commons contributions naming the place in the five years after (N = {len(D0)})")
ax = fig.add_axes([0.09, 0.12, 0.62, 0.7])
for g, c in TCOL.items():
    d = D0[D0.typegrp == g]
    ax.scatter(d.deaths, d.C + 1, s=46, color=c, alpha=0.9, edgecolor=PAPER, lw=0.8, label=g, zorder=3)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.7, 700); ax.set_ylim(0.8, 3500)
ax.set_xticks([1, 3, 10, 30, 100, 300]); ax.set_xticklabels(["1", "3", "10", "30", "100", "300"])
ax.set_yticks([1, 2, 11, 101, 1001]); ax.set_yticklabels(["0", "1", "10", "100", "1,000"])
ax.set_xlabel("Deaths (log scale)"); ax.set_ylabel("Contributions in the five years after (log scale)")
ax.grid(color=RULE, lw=0.5)
LAB = {"grenfell": (120, 2700, "left"), "kingscross": (14, 1800, "right"), "lewisham": (140, 1250, "left"), "aberfan": (95, 420, "right"),
       "piperalpha": (260, 300, "left"), "gresford": (360, 62, "left"), "lockerbie": (270, 24, "center"), "senghenydd": (430, 5.2, "center"),
       "quintinshill": (290, 1.0, "left"), "grayrigg": (1.3, 34, "left"),
       "hixon": (14, 42, "left"), "enniskillen": (5.2, 175, "right"), "arena": (8.5, 52, "right"), "dunblane": (30, 52, "left")}
NM = {"grenfell": "Grenfell Tower 2017", "kingscross": "King's Cross fire 1987", "lewisham": "Lewisham rail crash 1957", "aberfan": "Aberfan 1966",
      "piperalpha": "Piper Alpha 1988", "gresford": "Gresford 1934", "lockerbie": "Lockerbie 1988", "senghenydd": "Senghenydd 1913",
      "pretoria": "Pretoria Pit 1910", "quintinshill": "Quintinshill 1915", "staines": "Staines air crash 1972", "grayrigg": "Grayrigg 2007",
      "hixon": "Hixon 1968", "enniskillen": "Enniskillen 1987", "arena": "Manchester Arena 2017", "dunblane": "Dunblane 1996"}
for i, (tx, ty, ha) in LAB.items():
    r = D0[D0.id == i].iloc[0]
    ax.annotate(NM[i], (r.deaths, r.C + 1), (tx, ty), fontsize=9.5, color=INK, ha=ha, va="center", path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6, shrinkA=2, shrinkB=3))
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=10.5, title="Kind of disaster", title_fontsize=11)
m1 = R["M1"]["ld"]
fig.text(0.735, 0.47, f"Raw rank correlation: {R['desc']['spearman_deaths_C']:.2f}\n\nPlanned model, holding the\nusual level, kind, era and\nsearch term fixed: twice the\ndeaths, about {R['prose']['el_double_pc']:.0f}% more\ncontributions (95% interval\n{R['prose']['el_double_lo']:.0f}% to {R['prose']['el_double_hi']:.0f}%). The link\nloses clarity in {R['prose']['n_checks_cross']} of {R['prose']['n_checks']}\nchecks.", fontsize=10.5, color=INK, va="top", linespacing=1.3)
foot(fig); out(fig, "scatter")

# ---------- 3. robustness forest
rob = [r for r in R["robust"] if r["group"] != "X"] + [r for r in R["robust"] if r["group"] == "X"]
fig = plt.figure(figsize=(11, 12))
title(fig, "How sure is the death-toll link?", "Elasticity of five-year attention with respect to deaths, main model and every check (95% intervals)")
ax = fig.add_axes([0.42, 0.06, 0.54, 0.84])
y = np.arange(len(rob))[::-1]
for yy, r in zip(y, rob):
    c = ACC if r["lo"] > 0 else (ACC2 if r["group"] == "R5" else MUT)
    if r["group"] == "X": c = "#8E8778"
    ax.plot([r["lo"], r["hi"]], [yy, yy], color=c, lw=2.2, solid_capstyle="round")
    ax.scatter([r["b"]], [yy], s=34, color=c, zorder=3, marker="D" if r["group"] in ("main",) else "o")
    lab = r["label"] + f"  (N = {r['n']})"
    if r["group"] == "X": lab = "Exploratory: " + lab
    ax.text(-1.55, yy, lab, ha="right", va="center", fontsize=9.8, color=INK if r["group"] != "X" else MUT)
ax.axvline(0, color=INK, lw=0.9); ax.axvline(R["M1"]["ld"]["b"], color=ACC, lw=0.8, ls=(0, (3, 3)))
ax.set_xlim(-1.5, 3.4); ax.set_yticks([]); ax.set_ylim(-1, len(rob))
ax.set_xlabel("Elasticity (1 = attention rises in proportion to deaths)"); ax.grid(axis="x", color=RULE, lw=0.6)
ax.spines["left"].set_visible(False)
foot(fig); out(fig, "robust", blog=False)

# ---------- 4. group contrasts
rows = [("London and South East", R["M1g"]["London and South East"]), ("  without Grenfell and King's Cross (exploratory)", R["X_london"]["drop Grenfell and King's Cross"]),
        ("  with the other search term (exploratory)", R["X_london"]["swap terms"]),
        ("Scotland", R["M1g"]["Scotland"]), ("Wales", R["M1g"]["Wales"]), ("Northern Ireland", R["M1g"]["Northern Ireland"]),
        ("Mining disaster (vs other kinds)", R["M1m"]["mining"])]
fig = plt.figure(figsize=(11, 6.6))
title(fig, "Whose disasters get talked about?", "Five-year Commons attention against disasters elsewhere in England (or other kinds), same deaths,\nkind, era and search term (% change, 95% intervals)")
ax = fig.add_axes([0.42, 0.13, 0.54, 0.7])
lg = lambda v: np.log10(1 + v / 100)
for i, (lab, v) in enumerate(rows):
    yy = len(rows) - 1 - i
    c = ACC if v["lo"] > 0 else MUT
    ax.plot([lg(v["lo"]), lg(v["hi"])], [yy, yy], color=c, lw=2.4, solid_capstyle="round")
    ax.scatter([lg(v["b"])], [yy], s=44, color=c, zorder=3)
    ax.text(-1.32, yy, lab, ha="right", va="center", fontsize=11, color=INK if not lab.startswith("  ") else MUT)
ax.axvline(0, color=INK, lw=0.9)
tk = [-90, -50, 0, 100, 300, 1000, 3000]
ax.set_xticks([lg(t) for t in tk]); ax.set_xticklabels([f"{t:+,}%" if t else "0" for t in tk])
ax.set_xlim(-1.3, 1.6); ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.grid(axis="x", color=RULE, lw=0.6)
ax.set_xlabel("Change in attention (log scale)")
foot(fig); out(fig, "groups")

# ---------- 5. map
T = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
C = topo_polys("ctry")
fig = plt.figure(figsize=(9, 11.5))
title(fig, "Disasters and the attention that followed", "Sized by deaths; colour: Commons contributions above the usual level in five years, per death", y=0.975)
ax = fig.add_axes([0.02, 0.06, 0.96, 0.84]); ax.set_facecolor(PAPER)
for nm, g in C.items():
    gg = stransform(lambda x, y, z=None: T.transform(x, y), g)
    for p in gg.geoms:
        if p.area < 4e6: continue
        xx, yy = p.exterior.xy; ax.fill(xx, yy, color=LAND, ec="#CFC6B4", lw=0.5, zorder=1)
x, y = T.transform(D0.lon.values, D0.lat.values)
D0["x"], D0["y"] = x, y
D0["xpd"] = D0.CX.clip(lower=0) / D0.deaths
bins = [-0.01, 0.25, 1, 4, 1e9]; cols = ["#C9C2B4", "#C9A27A", "#B4652E", "#7A2A22"]
labs = ["under ¼ per death", "¼ to 1", "1 to 4", "4 or more"]
D0["cb"] = pd.cut(D0.xpd, bins, labels=False)
for r in D0.sort_values("deaths", ascending=False).itertuples():
    ax.scatter(r.x, r.y, s=18 + 4.2 * r.deaths ** 0.85, color=cols[r.cb], alpha=0.85, edgecolor="white", lw=1.0, zorder=3)
ax.set_xlim(-30000, 700000); ax.set_ylim(-10000, 1240000); ax.set_aspect("equal"); ax.axis("off")
pl = [("grenfell", 400000, 45000, "center", "Grenfell Tower 2017"), ("kingscross", 590000, 80000, "center", "King's Cross fire 1987"),
      ("aberfan", 150000, 232000, "right", "Aberfan 1966"), ("senghenydd", 150000, 195000, "right", "Senghenydd 1913"),
      ("piperalpha", 560000, 1010000, "left", "Piper Alpha 1988"), ("lockerbie", 470000, 650000, "left", "Lockerbie 1988"),
      ("gresford", 245000, 402000, "right", "Gresford 1934"), ("pretoria", 290000, 470000, "right", "Pretoria Pit 1910"),
      ("enniskillen", 60000, 445000, "center", "Enniskillen 1987")]
for i, lx, ly, ha, nm in pl:
    r = D0[D0.id == i].iloc[0]
    ax.annotate(nm, (r.x, r.y), (lx, ly), fontsize=9.5, color=INK, ha=ha, va="center", path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6, shrinkB=4), zorder=5)
hs = [Line2D([], [], marker="o", ls="", color=c, markersize=9, label=l) for c, l in zip(cols, labs)]
hs += [Line2D([], [], marker="o", ls="", color="#9C9486", markersize=np.sqrt(18 + 4.2 * d ** 0.85), alpha=0.6, label=f"{d} deaths") for d in (10, 50, 250)]
ax.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.0, 0.985), frameon=False, fontsize=10, title="Extra contributions per death", title_fontsize=10.5, labelspacing=1.0)
fig.text(0.04, 0.04, f"{len(D0)} disasters, 1910 to 2020, with a usable search term. United Kingdom.", fontsize=10, color=MUT)
foot(fig); out(fig, "map")

# ---------- 6. time to half
fig = plt.figure(figsize=(11, 6.6))
title(fig, "Most of the extra attention comes early", f"Month by which each disaster reached half of its five-year excess attention ({R['half']['n']} disasters with excess attention)")
ax = fig.add_axes([0.08, 0.14, 0.88, 0.66])
pos = D0[D0.CX > 0].sort_values(["half_k", "typegrp"])
cnt = {}
for r in pos.itertuples():
    b3 = int(r.half_k // 3) * 3
    cnt[b3] = cnt.get(b3, 0) + 1
    ax.scatter(b3 + 1.5, cnt[b3], s=150, color=TCOL[r.typegrp], edgecolor=PAPER, lw=1, zorder=3)
ax.axvline(R["half"]["median"], color=ACC, lw=1.4)
ax.text(R["half"]["median"] + 1, 12.3, f"median: month {R['half']['median']:.1f}", color=ACC, fontsize=11.5, path_effects=HALO)
ax.axvline(12, color=MUT, lw=0.8, ls=(0, (3, 3)))
ax.text(12.6, 10.6, f"{R['half']['within12']} of {R['half']['n']} within the first year", color=MUT, fontsize=11, path_effects=HALO)
ax.set_xlim(0, 60); ax.set_ylim(0, 16); ax.set_xticks(range(0, 61, 12)); ax.set_yticks([])
ax.spines["left"].set_visible(False); ax.set_xlabel("Months after the disaster (3-month bins; each dot is a disaster)")
hs = [Line2D([], [], marker="o", ls="", color=c, markersize=9, label=g) for g, c in TCOL.items()]
ax.legend(handles=hs, loc="upper right", frameon=False, fontsize=10, ncol=2)
foot(fig); out(fig, "half")

# ---------- 7. timeline
fig = plt.figure(figsize=(12, 6.4))
title(fig, "A century of disasters in the Commons", f"Contributions naming the place in the five years after each disaster, {D0.year.min()} to {D0.year.max()} (dot size: deaths)")
ax = fig.add_axes([0.07, 0.14, 0.9, 0.66])
for r in D0.itertuples():
    ax.plot([r.year, r.year], [0.8, r.C + 1], color=TCOL[r.typegrp], lw=1.1, alpha=0.6)
    ax.scatter([r.year], [r.C + 1], s=14 + 2.4 * r.deaths ** 0.85, color=TCOL[r.typegrp], edgecolor=PAPER, lw=0.8, zorder=3)
ax.set_yscale("log"); ax.set_ylim(0.8, 4000); ax.set_yticks([1, 11, 101, 1001]); ax.set_yticklabels(["0", "10", "100", "1,000"])
ax.set_xlim(1905, 2024); ax.grid(axis="y", color=RULE, lw=0.5); ax.set_ylabel("Contributions, five years (log scale)")
for i, dx, dy in (("grenfell", -2, 1.25), ("kingscross", -2, 1.3), ("aberfan", 0, 1.6), ("gresford", 0, 1.6), ("senghenydd", 3, 4.5), ("bethnalgreen", 0, 1.6),
                  ("piperalpha", 0, 2.4), ("lewisham", 0, 1.35)):
    r = D0[D0.id == i].iloc[0]
    nm = r.event.split(" (")[0].replace(" disaster", "").replace(" colliery", "").replace(" Tower fire", "").replace(" tube station crush", "").replace(" rail crash", " rail crash")
    ax.text(r.year + dx, (r.C + 1) * dy, nm, fontsize=9.5, ha="right" if dx < 0 else ("left" if dx > 0 else "center"), color=INK, path_effects=HALO)
hs = [Line2D([], [], marker="o", ls="", color=c, markersize=8, label=g) for g, c in TCOL.items()]
ax.legend(handles=hs, loc="upper left", frameon=False, fontsize=9.5, ncol=3)
foot(fig); out(fig, "timeline")

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.text(0.05, 0.86, "Does Parliament notice", fontsize=38, family=DISP, fontweight="bold", color=INK, va="top")
fig.text(0.05, 0.72, "disasters, and whose?", fontsize=38, family=DISP, fontweight="bold", color=ACC, va="top")
fig.text(0.05, 0.53, f"{len(D0)} UK disasters, 1910 to 2020, and how often the\nHouse of Commons named the place in the five years after.", fontsize=15, color=INK, va="top", linespacing=1.35)
fig.text(0.05, 0.08, "Dr Tristan Hotham · maps.tristanhotham.com/disaster-attention", fontsize=11, family=MONO, color=MUT)
ax = fig.add_axes([0.07, 0.17, 0.45, 0.22])
xs = [d["mid"] for d in es if d["mid"] >= -12]; ys = [d["ratio"] for d in es if d["mid"] >= -12]
ax.plot(xs, ys, color=ACC, lw=2.2); ax.scatter(xs, ys, s=12, color=ACC)
ax.axhline(1, color=MUT, lw=0.8); ax.set_yscale("log"); ax.set_yticks([]); ax.set_xticks([]); ax.minorticks_off()
for s in ax.spines.values(): s.set_visible(False)
ax.text(1, 11, "month of the disaster", fontsize=10, color=MUT)
ax2 = fig.add_axes([0.58, 0.04, 0.4, 0.92]); ax2.set_facecolor(PAPER)
for nm, g in C.items():
    gg = stransform(lambda x, y, z=None: T.transform(x, y), g)
    for p in gg.geoms:
        if p.area < 4e6: continue
        xx, yy = p.exterior.xy; ax2.fill(xx, yy, color=LAND, ec="#CFC6B4", lw=0.4)
for r in D0.sort_values("deaths", ascending=False).itertuples():
    ax2.scatter(r.x, r.y, s=6 + 1.6 * r.deaths ** 0.85, color=cols[r.cb], alpha=0.85, edgecolor="white", lw=0.6)
ax2.set_xlim(-30000, 700000); ax2.set_ylim(-10000, 1240000); ax2.set_aspect("equal"); ax2.axis("off")
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
plt.close(fig)
assert Image.open(os.path.join(ROOT, "header.png")).size == (1200, 630)
D0[["id", "x", "y", "xpd", "cb"]].to_csv(f"{SCR}/mapxy.csv", index=False)
print("figures done")
