"""Reddit collage (2700 x 2025, light background): map of the disasters, the event-study curve and key numbers.
Every number is read from data/results.json. Run: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.ops import transform as stransform
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
PAPER, INK, MUT, LAND, ACC, GREY = "#F8F4EA", "#24211D", "#6B655B", "#E6DFD0", "#8C3B2E", "#B9B2A5"
plt.rcParams.update({"font.family": "Source Serif 4", "figure.facecolor": PAPER, "axes.facecolor": PAPER, "pdf.fonttype": 42})
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
EV = pd.read_csv(f"{DATA}/events.csv"); D0 = EV[EV.main_v1 == 1].copy()
T = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
D0["x"], D0["y"] = T.transform(D0.lon.values, D0.lat.values)
D0["xpd"] = D0.CX.clip(lower=0) / D0.deaths
cols = ["#C9C2B4", "#C9A27A", "#B4652E", "#7A2A22"]
D0["cb"] = pd.cut(D0.xpd, [-0.01, 0.25, 1, 4, 1e9], labels=False)

fig = plt.figure(figsize=(20, 15), dpi=135)
fig.text(0.035, 0.955, "Does Parliament notice disasters?", fontsize=46, family=DISP, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.885, f"{R['desc']['n']} UK disasters, 1910 to 2020 ({R['desc']['deaths_total']:,} deaths), and how often House of Commons speeches\nnamed the place, month by month, from two years before to five years after", fontsize=19, color=MUT, va="top", linespacing=1.35)
# map
ax = fig.add_axes([0.02, 0.07, 0.46, 0.76]); ax.set_facecolor(PAPER)
for nm, g in topo_polys("ctry").items():
    gg = stransform(lambda x, y, z=None: T.transform(x, y), g)
    for p in gg.geoms:
        if p.area < 4e6: continue
        xx, yy = p.exterior.xy; ax.fill(xx, yy, color=LAND, ec="#CFC6B4", lw=0.6)
for r in D0.sort_values("deaths", ascending=False).itertuples():
    ax.scatter(r.x, r.y, s=30 + 7 * r.deaths ** 0.85, color=cols[r.cb], alpha=0.88, edgecolor="white", lw=1.2, zorder=3)
ax.set_xlim(-60000, 700000); ax.set_ylim(-10000, 1240000); ax.set_aspect("equal"); ax.axis("off")
lab = [("aberfan", 70000, 260000, "right", "Aberfan 1966\n146 deaths"), ("grenfell", 560000, 20000, "center", "Grenfell Tower 2017\n72 deaths"),
       ("piperalpha", 540000, 1080000, "center", "Piper Alpha 1988\n167 deaths"), ("lockerbie", 480000, 660000, "left", "Lockerbie 1988\n270 deaths"),
       ("senghenydd", 70000, 175000, "right", "Senghenydd 1913\n439 deaths"), ("gresford", 255000, 445000, "right", "Gresford 1934\n266 deaths")]
for i, lx, ly, ha, t in lab:
    r = D0[D0.id == i].iloc[0]
    assert str(int(r.deaths)) in t and str(int(r.year)) in t, i
    ax.annotate(t, (r.x, r.y), (lx, ly), fontsize=15, color=INK, ha=ha, va="center", path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.9, shrinkB=5), linespacing=1.15, zorder=5)
hs = [Line2D([], [], marker="o", ls="", color=c, markersize=13, label=l) for c, l in zip(cols, ["under ¼", "¼ to 1", "1 to 4", "4 or more"])]
lg = ax.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=15, title="Extra Commons speeches in five\nyears, per death (size: deaths)", title_fontsize=15, labelspacing=0.9)
lg._legend_box.align = "left"
# big numbers
def big(x, y, num, txt, c=ACC):
    fig.text(x, y, num, fontsize=60, family=DISP, fontweight="bold", color=c, va="top")
    fig.text(x, y - 0.075, txt, fontsize=17, color=INK, va="top", linespacing=1.4)
p = R["prose"]
big(0.52, 0.83, f"{p['m0']:.0f}x", "the usual number of speeches\nnaming the place, in the month\nof the disaster")
big(0.77, 0.83, f"{R['half']['median']:.1f}", "months, the median time for a\ndisaster to reach half of its\nextra attention over five years", INK)
big(0.52, 0.58, f"+{p['el_double_pc']:.0f}%", f"more attention for twice the deaths\n(planned model; not robust: unclear\nin {p['n_checks_cross']} of {p['n_checks']} checks; +{R['ext']['prose']['el_double_pc']:.0f}% with\n{R['ext']['events']['added_main']} disasters added later)", INK)
# event study inset
a2 = fig.add_axes([0.775, 0.39, 0.2, 0.18])
es = [d for d in R["M2"]["bins"]]
xs = [d["mid"] for d in es]; ys = [d["ratio"] for d in es]
a2.fill_between(xs, [d["lo"] for d in es], [d["hi"] for d in es], color=ACC, alpha=0.12, lw=0)
a2.plot(xs, ys, color=ACC, lw=2.5); a2.axhline(1, color=MUT, lw=1); a2.axvline(-0.5, color=GREY, lw=1, ls=":")
a2.set_yscale("log"); a2.set_yticks([1, 3, 10, 30]); a2.set_yticklabels(["1x", "3x", "10x", "30x"]); a2.minorticks_off()
a2.set_xticks([-24, 0, 24, 60]); a2.set_xticklabels(["-2 yrs", "event", "+2", "+5 yrs"])
a2.tick_params(labelsize=12, colors=MUT); [a2.spines[s].set_visible(False) for s in ("top", "right")]
fig.text(0.765, 0.632, "Speeches against the usual level\n(shading: 95% range)", fontsize=14, color=MUT, va="top")
# list
fig.text(0.52, 0.335, "Most extra attention in the five years after", fontsize=19, color=ACC, va="top")
top = D0.sort_values("CX", ascending=False).head(6)
for j, r in enumerate(top.itertuples()):
    y = 0.29 - j * 0.03
    nm = r.event.split(" (")[0]
    fig.text(0.52, y, f"{nm}, {r.year}", fontsize=16, color=INK, va="top")
    fig.text(0.83, y, f"{int(r.deaths)} deaths", fontsize=15, color=MUT, va="top", ha="right", family="IBM Plex Mono")
    fig.text(0.965, y, f"{int(round(r.CX)):,}", fontsize=15, color=INK, va="top", ha="right", family="IBM Plex Mono")
fig.text(0.965, 0.315, "extra speeches", fontsize=13, color=MUT, ha="right", va="top")
fig.text(0.52, 0.098, "Extra: above the place's usual level, allowing for sittings. King's Cross was also debated for the\nChannel Tunnel railway; London's lead rests on two disasters. Counts of speeches, not of care.", fontsize=13.5, color=MUT, va="top", linespacing=1.35)
fig.text(0.035, 0.02, "Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia (CC BY-SA); Wikidata (CC0); ONS.   Dr Tristan Hotham  ·  maps.tristanhotham.com/disaster-attention",
         fontsize=13, family="IBM Plex Mono", color=MUT)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disaster_attention_collage.png")
fig.savefig(out, dpi=135, facecolor=PAPER); print(out)
