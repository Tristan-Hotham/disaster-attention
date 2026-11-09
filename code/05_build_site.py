"""Step 5: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24094466, https://doi.org/10.5281/zenodo.24094466 and https://blog.tristanhotham.com/2026/10/31/disaster-attention/ stay as placeholders for the publisher."""
import time
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
S = jload(f"{DATA}/site.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", time.strftime("%Y%m%d"))
tb = "".join(f'<label><input type="checkbox" data-t="{g}" checked> {g}</label>' for g in ("Mining", "Transport", "Fire or explosion", "Crowd crush", "Bombing or shooting", "Other"))
t = t.replace("{{TYPEBOXES}}", tb)
ev = sorted([e for e in S["events"] if e["m"] == 1], key=lambda e: e["d"])
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;")
rows = "".join(f'<tr><td><a href="#mapWrap" data-go="{e["id"]}">{esc(e["n"])}</a>{" *" if e["x"] else ""}</td><td class="r">{e["y"]}</td><td class="r">{e["dt"]:,}</td>'
               f'<td>{esc(("in " if e["kd"] == "in" else "") + e["t"])}</td><td class="r">{e["b"]:.2f}</td><td class="r">{e["C"]:,}</td></tr>\n' for e in ev)
t = t.replace("{{TABLE}}", rows)
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "worst", "tragic", "horrific"):
    assert bad not in vis, bad
ids = {e["id"] for e in S["events"]}
for g in re.findall(r'data-go="([^"]+)"', t):
    assert g in ids, g
assert t.count("site-nav.js") == 1 and t.index("site-nav.js") > t.index("mfs-script")
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
js = open(os.path.join(ROOT, "js", "page.js"), encoding="utf-8").read()
assert "—" not in js and "–" not in js
print("index.html", len(t) // 1024, "KB")
