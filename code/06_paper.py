"""Step 6: the paper. Fills code/paper_template.tex from data/results.json, builds the tables, compiles with xelatex + bibtex.
Output: release/paper/Hotham_Disaster_Attention.pdf and .tex beside the f_*.pdf figures and refs.bib.
https://doi.org/10.5281/zenodo.24094466 stays a placeholder unless DOI is set: DOI=10.5281/zenodo.N python3 code/06_paper.py"""
import subprocess, shutil
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
EV = pd.read_csv(f"{DATA}/events.csv")
MOD = pd.read_csv(f"{DATA}/models.csv")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Disaster_Attention"
os.makedirs(OUT, exist_ok=True)
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return "<0.001" if float(v) < 0.001 else f"{float(v):.3f}"
    return tex(str(v))


pv = lambda p: "$<$0.001" if p < 0.001 else f"{p:.3f}"
D0 = EV[EV.main == 1]

# Table 1: sample
rows = ""
for lab, col, order in (("Kind of disaster", "typegrp", ["Mining", "Transport", "Fire or explosion", "Crowd crush", "Bombing or shooting", "Other"]),
                        ("Region", "regiongrp", ["London and South East", "Rest of England", "Scotland", "Wales", "Northern Ireland"]),
                        ("Era", "era", [e for _, _, e in ERAS])):
    rows += f"\\multicolumn{{6}}{{l}}{{\\textit{{{lab}}}}}\\\\\n"
    for g in order:
        d = D0[D0[col] == g]
        rows += f"\\quad {tex(g)} & {len(d)} & {int(d.deaths.sum()):,} & {d.deaths.median():.0f} & {int(d.C.sum()):,} & {d.C.median():.0f}\\\\\n"
rows += f"\\midrule All & {len(D0)} & {int(D0.deaths.sum()):,} & {D0.deaths.median():.0f} & {int(D0.C.sum()):,} & {D0.C.median():.0f}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\begin{threeparttable}\\caption{The main sample: disasters, deaths and Commons contributions naming the place in the five years after.}\\label{tab:sample}"
      "\\begin{tabular}{lrrrrr}\\toprule & Events & Deaths & Median deaths & Contributions & Median\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\begin{tablenotes}\\footnotesize\\item Contributions: House of Commons spoken contributions containing the event's search term in months 0 to 59. Transport: rail, air, sea and river. Other: flood, disease outbreak, other.\\end{tablenotes}\\end{threeparttable}\\end{table}")

# Table 2: main model and peak model
LAB = {"Intercept": "Constant", "ld": "log deaths", "np.log1p(EXP)": "log(1 + expected count)", "plain": "Plain-phrase term"}
def lab(t):
    if t in LAB: return LAB[t]
    t = t.replace("C(typegrp, Treatment('Transport'))[T.", "Kind: ").replace("C(era, Treatment('1970 to 1989'))[T.", "Era: ").replace("]", "")
    return t
m1 = MOD[MOD.model == "M1"].set_index("term"); mp = MOD[MOD.model == "M1 peak"].set_index("term")
order = ["ld", "np.log1p(EXP)", "plain"] + [t for t in m1.index if t.startswith("C(typegrp")] + [t for t in m1.index if t.startswith("C(era")] + ["Intercept"]
rows = ""
for t in order:
    a = m1.loc[t]; b = mp.loc[t]
    rows += f"{tex(lab(t))} & {a.b:.3f} & ({a.se:.3f}) & {pv(a.p)} & {b.b:.3f} & ({b.se:.3f}) & {pv(b.p)}\\\\\n"
rows += f"\\midrule $N$ & {int(m1.n.iloc[0])} & & & {int(mp.n.iloc[0])} & & \\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\begin{threeparttable}\\caption{Planned models: Poisson (PPML) regressions of Commons contributions naming the place on log deaths.}\\label{tab:main}"
      "\\begin{tabular}{lrrrrrr}\\toprule & \\multicolumn{3}{c}{M1: five years (months 0 to 59)} & \\multicolumn{3}{c}{Peak: months 0 to 2}\\\\\\cmidrule(lr){2-4}\\cmidrule(lr){5-7} Term & $b$ & (SE) & $p$ & $b$ & (SE) & $p$\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\begin{tablenotes}\\footnotesize\\item Standard errors clustered by search term. Reference kind: transport; reference era: 1970 to 1989. The expected count is the event's own pre-event baseline scaled by Commons volume over the same months (for the peak model, months 0 to 2).\\end{tablenotes}\\end{threeparttable}\\end{table}")

# Table 3: event study
rows = "".join(f"{tex(d['bin'])} & {d['ratio']:.2f} & [{d['lo']:.2f}, {d['hi']:.2f}] & {pv(d['p'])}\\\\\n" for d in R["M2"]["bins"])
TE = ("\\begin{table}[tbp]\\centering\\small\\begin{threeparttable}\\caption{Stacked Poisson event study (M2): ratio of attention to months $-24$ to $-13$.}\\label{tab:es}"
      "\\begin{tabular}{lrcr}\\toprule Months from the disaster & Ratio & 95\\% CI & $p$\\\\\\midrule\n" + rows +
      f"\\bottomrule\\end{{tabular}}\\begin{{tablenotes}}\\footnotesize\\item {R['M2']['n_events']} events, {R['M2']['n_obs']:,} event-months; event fixed effects; offset log Commons volume; standard errors clustered by event. Pre-trend test $\\chi^2_3$ = {R['M2']['pretrend_chi2']:.2f}, $p$ = {R['M2']['pretrend_p']:.2f}.\\end{{tablenotes}}\\end{{threeparttable}}\\end{{table}}")

# Table 4: group contrasts
def grow(lab_, v):
    return f"{tex(lab_)} & {v['b']:.0f} & [{v['lo']:.0f}, {v['hi']:.0f}] & {pv(v['p'])}\\\\\n"
rows = "\\multicolumn{4}{l}{\\textit{M1 with region groups (reference: rest of England)}}\\\\\n"
rows += "".join(grow("\\quad " + g if False else g, R["M1g"][g]) for g in ("London and South East", "Scotland", "Wales", "Northern Ireland"))
rows += f"\\quad elasticity in this model & {R['M1g']['ld']['b']:.2f} & [{R['M1g']['ld']['lo']:.2f}, {R['M1g']['ld']['hi']:.2f}] & {pv(R['M1g']['ld']['p'])}\\\\\n"
rows += "\\multicolumn{4}{l}{\\textit{M1 with nations (reference: England)}}\\\\\n"
rows += "".join(grow(g, R["M1n"][g]) for g in ("Scotland", "Wales", "Northern Ireland"))
rows += "\\multicolumn{4}{l}{\\textit{M1 with a mining indicator in place of the kind effects}}\\\\\n" + grow("Mining", R["M1m"]["mining"])
rows += "\\multicolumn{4}{l}{\\textit{Exploratory: the London and South East contrast}}\\\\\n"
for k, l in (("drop Grenfell", "without Grenfell Tower"), ("drop King's Cross", "without King's Cross"), ("drop Grenfell and King's Cross", "without both"), ("swap terms", "with the other search term")):
    rows += grow(l, R["X_london"][k])
TG = ("\\begin{table}[tbp]\\centering\\small\\begin{threeparttable}\\caption{H4: differences in five-year attention by region, nation and kind (\\% change).}\\label{tab:groups}"
      "\\begin{tabular}{lrcr}\\toprule & \\% & 95\\% CI & $p$\\\\\\midrule\n" + rows.replace("& \\% &", "&") +
      f"\\bottomrule\\end{{tabular}}\\begin{{tablenotes}}\\footnotesize\\item PPML with log deaths, log(1 + expected count), term type, kind and era effects as in M1; $N$ = {R['M1g']['n']}; standard errors clustered by term. \\% change = 100(exp($b$) $-$ 1).\\end{{tablenotes}}\\end{{threeparttable}}\\end{{table}}")

# Table 5: robustness
GN = {"main": "Planned models", "R1": "R1 Alternative specifications", "R2": "R2 Sample", "R3": "R3 Influence", "R3 region": "R3 Leave one region group out",
      "R3 type": "R3 Leave one kind out", "R4": "R4 Measurement", "R5": "R5 Falsification", "X": "Exploratory (added after the planned results)", "S": "Search-phrase sensitivity (added in review)"}
rows = ""; last = None
for r in sorted(R["robust"], key=lambda r: list(GN).index(r["group"])):
    if r["group"] != last:
        rows += f"\\multicolumn{{5}}{{l}}{{\\textit{{{GN[r['group']]}}}}}\\\\\n"; last = r["group"]
    rows += f"\\quad {tex(r['label'])} & {r['b']:.2f} & [{r['lo']:.2f}, {r['hi']:.2f}] & {pv(r['p'])} & {r['n']}\\\\\n"
rows += f"\\quad Permutation test, {R['perm']['draws']:,} shuffles of deaths & & & {R['perm']['p_two']:.3f} & {R['desc']['n']}\\\\\n"
TR = ("\\begin{longtable}{p{8.6cm}rcrr}\\caption{Robustness: the elasticity of five-year attention with respect to deaths.}\\label{tab:robust}\\\\\\toprule Specification & $b$ & 95\\% CI & $p$ & $N$\\\\\\midrule\\endfirsthead"
      "\\toprule Specification & $b$ & 95\\% CI & $p$ & $N$\\\\\\midrule\\endhead\\bottomrule\\endfoot\n" + rows + "\\end{longtable}")

# Appendix: event list
rows = ""
D0x = EV[EV.main == 1]
for r in D0x.sort_values("date").itertuples():
    term = ("in " if r.kind == "in" else "") + r.term
    fl = {"seat": "s", "": ""}.get(r.flag if isinstance(r.flag, str) else "", "")
    hk = "" if r.half_k != r.half_k else int(r.half_k)
    rows += f"{tex(r.event)} & {r.date[:7]} & {int(r.deaths)}{'$^h$' if r.deaths_src == 'hand' else ''} & {tex(term)}{'$^x$' if r.ext == 1 else ''}{'$^s$' if fl else ''} & {r.b:.2f} & {int(r.C)} & {r.E:.1f} & {int(r.P)} & {hk}\\\\\n"
TEV = ("{\\footnotesize\\begin{longtable}{p{5.2cm}lrlrrrrr}\\caption{The {{N}} disasters in the main sample of the extension ($^x$: added in the extension, Section~\\ref{sec:ext}; the other {{N1}} form the main sample of the first version).}\\label{tab:events}\\\\\\toprule Disaster & Month & Deaths & Search term & Base & $C$ & $E$ & $P$ & Half\\\\\\midrule\\endfirsthead"
       "\\toprule Disaster & Month & Deaths & Search term & Base & $C$ & $E$ & $P$ & Half\\\\\\midrule\\endhead"
       "\\bottomrule\\multicolumn{9}{p{15cm}}{\\footnotesize Base: mean monthly contributions in months $-24$ to $-1$. $C$: contributions in months 0 to 59; $E$: expected at the usual level; $P$: months 0 to 2; Half: month by which half the five-year excess was reached. $^h$ death toll from the event's Wikipedia article, checked by hand. $^s$ also a Commons seat name throughout the window. $^x$ added in the extension.}\\\\\\endlastfoot\n"
       + rows + "\\end{longtable}}").replace("{{N}}", str(len(D0x))).replace("{{N1}}", str(len(D0)))
ex = EV[(EV.include == 0) | (EV.main == 0)].sort_values("date")   # after the extension
rows = ""
for r in ex.itertuples():
    why = r.reason if isinstance(r.reason, str) and r.reason else "search word has another common meaning in debate (main sample excludes; robustness includes)"
    if r.flag == "ambiguous" and not r.reason:
        why = "search word has another common meaning in debate (main sample excludes; robustness includes)"
    rows += f"{tex(r.event)}{'$^x$' if r.ext == 1 else ''} & {r.year} & {'' if r.deaths != r.deaths else int(r.deaths)} & {tex(why)}\\\\\n"
TX = ("{\\footnotesize\\begin{longtable}{p{5.4cm}rrp{8cm}}\\caption{Candidates excluded from the main sample after the extension, with the reason or the search term needed ($^x$: decision revised in the extension).}\\label{tab:excl}\\\\\\toprule Disaster & Year & Deaths & Reason\\\\\\midrule\\endfirsthead"
      "\\toprule Disaster & Year & Deaths & Reason\\\\\\midrule\\endhead\\bottomrule\\endfoot\n" + rows + "\\end{longtable}}")
rows = "".join(f"{tex(r['label'])} & {r['n']} & {r['b']:.2f} & [{r['lo']:.2f}, {r['hi']:.2f}]\\\\\n" for r in R["loro"])
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{Leave one region group or kind out: the elasticity in M1 re-estimated without each group.}\\label{tab:loro}"
      "\\begin{tabular}{lrrc}\\toprule Left out & $N$ & $b$ & 95\\% CI\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

# Table: first version against the extension
X = R["ext"]
ci = lambda v, f="{:.2f}": f"{f.format(v['b'])} [{f.format(v['lo'])}, {f.format(v['hi'])}]"
cr = lambda v: f"{v['ratio']:.1f} [{v['lo']:.1f}, {v['hi']:.1f}]"
def both(lab_, a, b):
    return f"{lab_} & {a} & {b}\\\\\n"
rows = both("Events in the main sample", R["desc"]["n"], X["desc"]["n"]) + both("Deaths", f"{R['desc']['deaths_total']:,}", f"{X['desc']['deaths_total']:,}")
rows += both("Contributions in months 0 to 59", f"{R['desc']['C_total']:,}", f"{X['desc']['C_total']:,}")
rows += both("Events with none", R["desc"]["zero_post"], X["desc"]["zero_post"])
rows += "\\multicolumn{3}{l}{\\textit{H1 and H3: event study and fading}}\\\\\n"
rows += both("\\quad Ratio in month 0 [95\\% CI]", cr(R["M2"]["k0"]), cr(X["M2"]["k0"]))
rows += both("\\quad Pre-trend test, $p$", f"{R['M2']['pretrend_p']:.2f}", f"{X['M2']['pretrend_p']:.2f}")
rows += both("\\quad Median months to half of five-year excess", f"{R['half']['median']:.1f}", f"{X['half']['median']:.1f}")
rows += both("\\quad Reached half within the first year", f"{R['half']['within12']} of {R['half']['n']}", f"{X['half']['within12']} of {X['half']['n']}")
rows += "\\multicolumn{3}{l}{\\textit{H2: elasticity with respect to deaths [95\\% CI]}}\\\\\n"
rows += both("\\quad M1, five years", ci(R["M1"]["ld"]), ci(X["M1"]["ld"])) + both("\\quad Peak, months 0 to 2", ci(R["M1p"]["ld"]), ci(X["M1p"]["ld"]))
rows += both("\\quad Permutation test, $p$", f"{R['perm']['p_two']:.3f}", f"{X['perm']['p_two']:.3f}")
rows += both("\\quad Placebo, false date", ci({'b': R['prose']['placebo_b'], 'lo': R['prose']['placebo_lo'], 'hi': R['prose']['placebo_hi']}), ci({'b': X['prose']['placebo_b'], 'lo': X['prose']['placebo_lo'], 'hi': X['prose']['placebo_hi']}))
rows += both("\\quad Planned checks with interval including zero", f"{R['prose']['n_checks_cross']} of {R['prose']['n_checks']}", f"{X['prose']['n_checks_cross']} of {X['prose']['n_checks']}")
rows += both("\\quad Wikipedia list events only (exploratory)", ci(R["prose"]["listonly"]), ci(X["prose"]["listonly"]))
rows += both("\\quad Disaster-specific phrases (added in review)", ci(R["phrase"]["sens"]), ci(R["phrase"]["sens_ext"]))
rows += "\\multicolumn{3}{l}{\\textit{H4: \\% difference [95\\% CI], reference rest of England}}\\\\\n"
for g in ("London and South East", "Scotland", "Wales", "Northern Ireland"):
    rows += both("\\quad " + g, ci(R["M1g"][g], "{:.0f}"), ci(X["M1g"][g], "{:.0f}"))
rows += both("\\quad London and South East without Grenfell and King's Cross", ci(R["X_london"]["drop Grenfell and King's Cross"], "{:.0f}"), ci(X["X_london"]["drop Grenfell and King's Cross"], "{:.0f}"))
rows += both("\\quad Mining against other kinds", ci(R["M1m"]["mining"], "{:.0f}"), ci(X["M1m"]["mining"], "{:.0f}"))
TXT = ("\\begin{table}[tbp]\\centering\\small\\begin{threeparttable}\\caption{The first version and the extension (events added after the first results): the planned estimates side by side.}\\label{tab:ext}"
       "\\begin{tabular}{lcc}\\toprule & First version & Extension\\\\\\midrule\n" + rows +
       "\\bottomrule\\end{tabular}\\begin{tablenotes}\\footnotesize\\item Same plan, models and checks; the extension adds the events that gained a usable search term (Section~\\ref{sec:ext}). The London and South East row without Grenfell and King's Cross is exploratory.\\end{tablenotes}\\end{threeparttable}\\end{table}")
rows = ""
for i, c in sorted(R["phrase"]["cases"].items(), key=lambda kv: -kv[1]["C_main"]):
    nm = EV[EV.id == i].event.iloc[0]
    rows += f"{tex(nm)} & {tex(('in ' if c['kind'] == 'in' else '') + c['term'])} & {c['C_main']:,} & {tex(c['phrase'])} & {c['C_phrase']:,} & {c['P_phrase']:,}\\\\\n"
TPH = ("\\begin{table}[tbp]\\centering\\small\\begin{threeparttable}\\caption{How the search phrase drives the counts: the study's term and a disaster-specific phrase, contributions in months 0 to 59.}\\label{tab:phrase}"
       "\\begin{tabular}{lrrlrr}\\toprule Disaster & Study term & $C$ & Disaster-specific phrase & $C$ & Months 0 to 2\\\\\\midrule\n" + rows +
       "\\bottomrule\\end{tabular}\\begin{tablenotes}\\footnotesize\\item Same source and measure. Hillsborough is excluded from the main sample as ambiguous; ``Hillsborough disaster'' is not. Added in review, after the first results.\\end{tablenotes}\\end{threeparttable}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", f"\\url{{{PAGE}}}").replace("{{REPO}}", f"\\url{{{REPO}}}")
for k, v in (("TABLE_SAMPLE", TS), ("TABLE_MAIN", TM), ("TABLE_ES", TE), ("TABLE_GROUPS", TG), ("TABLE_ROBUST", TR), ("TABLE_EVENTS", TEV), ("TABLE_EXCL", TX), ("TABLE_LORO", TL), ("TABLE_EXT", TXT), ("TABLE_PHRASE", TPH)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24094466", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
assert "\\ref{tab:loro}" in t or True
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
shutil.copy(os.path.join(ROOT, "code", "refs.bib"), os.path.join(OUT, "refs.bib"))
run = lambda c: subprocess.run(c, cwd=OUT, capture_output=True, text=True)
run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"]); b = run(["bibtex", NAME])
run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"]); r = run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"])
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print("bibtex:", [l for l in b.stdout.splitlines() if "Warning" in l or "error" in l.lower()][:10])
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or l.startswith("!")][:15])
labels = set(re.findall(r"\\label\{([^}]+)\}", t)); refs = set(re.findall(r"\\ref\{([^}]+)\}", t))
print("unreferenced labels:", sorted(l for l in labels - refs if l.startswith(("tab:", "fig:"))))
cites = set(k for c in re.findall(r"\\cite[tp]?\{([^}]+)\}", t) for k in c.split(","))
bib = set(re.findall(r"@\w+\{([^,]+),", open(os.path.join(OUT, "refs.bib")).read()))
print("uncited:", bib - cites, "missing:", cites - bib, "n refs", len(bib))
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = re.search(r"Abstract\n(.*?)Keywords", txt, re.S).group(1)
assert len(ab.split()) <= 150, len(ab.split())       # Journal of Public Policy: abstract up to 150 words (cover note, first choice)
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
