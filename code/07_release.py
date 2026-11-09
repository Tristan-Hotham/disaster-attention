"""Step 7: blog post and meta (release/blog), cover note (release/paper), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24094466, https://doi.org/10.5281/zenodo.24094466 and https://blog.tristanhotham.com/2026/10/31/disaster-attention/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Disaster_Attention"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
assert R["cases"]["senghenydd"]["C"] == 1        # "matches 1 contribution"
assert R["ext"]["perm"]["p_two"] < 0.01             # blog: "under 1% of tries"
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "worst", "tragic", "horrific", "shocking"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Does Parliament notice disasters, and whose?",
        "slug": "disaster-attention",
        "excerpt": f"I counted, month by month, how often the House of Commons named the places of {R['desc']['n']} UK disasters between 1910 and 2020. Attention jumps to {R['prose']['m0']:.0f} times its usual level in the month of a disaster and mostly fades within the year. Bigger death tolls bring more attention, but less than in proportion.",
        "seo_description": f"How often did the House of Commons name the places of {R['desc']['n']} UK disasters, 1910 to 2020, and for how long? A data study.",
        "tags": ["data visualisation", "Parliament", "Hansard", "disasters", "UK history", "political attention", "maps"],
        "header_alt": "Title card on cream paper reading 'Does Parliament notice disasters, and whose?' beside a map of the UK with circles for disasters and a small line showing attention rising sharply in the month of a disaster."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# cover note
p = R["prose"]; m1 = R["M1"]["ld"]
cover = f"""# Cover note: Does Parliament Notice Disasters, and Whose?

## Suggested journals (no mandatory author charges; checked 2026)

The manuscript is about {{WORDS}} words before the references, counting tables and captions (the appendix tables follow the references), with 7 figures, 7 tables in the main text and 3 in the appendix. The abstract is {{ABWORDS}} words.

1. **Journal of Public Policy** (Cambridge University Press). Research articles of about 5,000 to 8,000 words of body text, excluding the abstract, references, tables and figures; abstract up to 150 words; the anonymised main document must not exceed 45 pages. Open access is optional, with costs covered by institutional agreements or a waiver on request; no submission fee is mentioned. Fit: very good, as the home of Birkland's 1998 article on focusing events; the abstract is within the 150-word limit; the body is near the upper limit, so the appendix tables should move to supplementary material. Source: Cambridge Core, Journal of Public Policy, "Preparing your materials".
2. **British Politics** (Palgrave Macmillan). Articles of no more than 9,000 words excluding the bibliography; subscription journal with an optional paid open access route (Sherpa Romeo lists the fee only for the published-version open access pathway). Fit: good for a UK parliamentary and historical audience; fits the limit as it stands. Source: Palgrave, British Politics, "Presentation of the paper"; Sherpa Romeo record 8302.
3. **Policy Studies Journal** or **Disasters** (both Wiley, subscription with optional open access) suit the agenda-setting and disaster-studies framing respectively, but their current word limits and charges could not be confirmed online here, so check before submitting.

## Summary for a cover letter (150 words)

{{SUMMARY}}
"""
summary = (f"Disasters are classic focusing events, yet we know little about how much attention legislatures give the places where they happen. "
           f"This article follows {R['desc']['n']} localised UK disasters from 1910 to 2020 through monthly counts of House of Commons contributions naming the place, with a design pre-specified in a written plan. "
           f"Attention jumps to {p['m0']:.0f} times its usual level in the month of a disaster; the median disaster accumulates half of its five-year excess within {R['half']['median']:.1f} months, though events followed by inquiries hold attention for years. "
           f"Attention rises with the death toll only weakly and far less than proportionally (elasticity {m1['b']:.2f}; {R['ext']['M1']['ld']['b']:.2f} once {R['ext']['events']['added_main']} disasters found later are added), and the association is not robust. "
           f"A London premium depends on two events, and there is no clear evidence of neglect of the devolved nations or mining communities. "
           f"It also shows how lists of remembered disasters and search terms shape such conclusions.")
sw = len(summary.split())
assert 130 <= sw <= 160, sw
import subprocess
txt = subprocess.run(["pdftotext", f"{REL}/paper/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
bw = len(body.split()) - len(re.search(r"Abstract\n(.*?)Keywords", txt, re.S).group(1).split())
abw = len(re.search(r"Abstract\n(.*?)Keywords", txt, re.S).group(1).split())
tx = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
pb = tx[tx.index("\\section{Introduction}"):tx.index("\\section*{Data availability}")]
pb = re.sub(r"\\begin\{(table|longtable|figure)\}.*?\\end\{\1\}", "", pb, flags=re.S)
pb = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", "", pb); prose_w = len(re.sub(r"[{}$\\~]", " ", pb).split())
cover = cover.replace("(the appendix tables follow the references)", f"(the appendix tables follow the references); the body text alone, without tables, figures and captions, is about {round(prose_w, -2):,} words")
cover = cover.replace("{WORDS}", f"{round(bw, -2):,}").replace("{ABWORDS}", str(abw)).replace("{SUMMARY}", summary)
for bad in ("\u2014", "\u2013", "DSIT", "DCMS"):
    assert bad not in cover
open(f"{REL}/paper/cover_note.md", "w", encoding="utf-8").write(cover)

# zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("events.csv", "event_months.csv", "models.csv", "models_extension.csv", "results.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$p$", "p").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Does Parliament Notice Disasters, and Whose? Attention in the House of Commons to the Places of UK Disasters, 1910 to 2020",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/disaster-attention/}}.</p><p>Sources: Hansard via the UK Parliament Hansard API (Open Parliament Licence v3.0); English Wikipedia, List of disasters in Great Britain and Ireland by death toll (CC BY-SA 4.0); Wikidata (CC0); town points from Mentioned in the House (doi:10.5281/zenodo.23761431); ONS boundaries (OGL v3.0). Text, figures and data CC BY 4.0 (Wikipedia-derived fields CC BY-SA 4.0); code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["focusing events", "agenda setting", "issue-attention cycle", "disasters", "House of Commons", "Hansard", "political attention", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23761431", "relation": "isDerivedFrom", "resource_type": "publication"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2, keepdash=True)
print("blog words", words, "figures", len(used), "; summary words", sw, "; body words", bw, "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
