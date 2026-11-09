"""Shared paths, constants and helpers for the disaster-attention study ("Does Parliament notice disasters, and whose?").

Inputs (read in place, never modified):
  RAW/hansard_monthly.json   UK Parliament Hansard API timeline statistics, House of Commons, contribution type Spoken,
                             counts per month 1909-01 to 2026-10 (Open Parliament Licence v3.0). "inp": contributions
                             containing "in <place>" for the 1,661 places of Mentioned in the House; "plain":
                             contributions containing the phrase anywhere, for by-election seat names and about 74
                             disaster-site names. Months absent = 0. Counts are contributions, not word occurrences.
  RAW/wiki_lists.json        wikitext of "List of disasters in Great Britain and Ireland by death toll" (English
                             Wikipedia, CC BY-SA 4.0): every disaster with 40 or more deaths.
  RAW/disasters_wd.tsv       Wikidata (CC0): items that are instances of subclasses of disaster in the UK, with date,
                             coordinates and number of deaths (P1120) where recorded.
  HP/places.csv              Mentioned in the House (Hotham 2026, doi:10.5281/zenodo.23761431): the 1,661 place terms
                             with coordinates, nation, population and ambiguity flags.
  GEO/uk_topo.json           ONS countries and regions of the UK (Open Government Licence v3.0): nation and region of
                             each event point.
  RAW/hansard_monthly_extra.json  the same Hansard source and format, "plain" only: 51 further phrases harvested after the
                             first results (event-site names for candidates that lacked a term, and disaster-specific
                             phrases such as "Grenfell Tower" for a sensitivity check). Merged into "plain" by hansard().
  code/events.csv            the curated event list (one row per event; inclusion rules in NOTES.md).
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("DA_RAW", "/home/claude/newdata/raw_new12")
HP = os.environ.get("DA_HP", "/home/claude/src6/hansard-places/data")
GEO = os.environ.get("DA_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("DA_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("DA_SCRATCH", "/home/claude/scratch/disaster-attention")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "disaster-attention"
TITLE = "Does Parliament notice disasters, and whose?"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

FIRST, LAST = (1909, 1), (2026, 10)     # first and last month of the Hansard series
PRE, POST = 24, 60                      # event window: 24 months before, 60 after (k = 0..59)
MINPRE = 12                             # at least 12 months of data before the event
CITY = 30.0                             # pre-event baseline (contributions a month) at or above which a city term is too broad
SEAT_FREE = None

TYPEGRP = {"mining": "Mining", "rail": "Transport", "air": "Transport", "sea": "Transport", "fire": "Fire or explosion",
           "explosion": "Fire or explosion", "crowd": "Crowd crush", "violence": "Bombing or shooting",
           "flood": "Other", "health": "Other", "other": "Other"}
TYPELAB = {"mining": "Mining", "rail": "Rail", "air": "Air", "sea": "Sea and river", "fire": "Fire", "explosion": "Explosion",
           "crowd": "Crowd crush", "violence": "Bombing or shooting", "flood": "Flood", "health": "Disease outbreak", "other": "Other"}
ERAS = [(1909, 1938, "1909 to 1938"), (1939, 1945, "1939 to 1945"), (1946, 1969, "1946 to 1969"), (1970, 1989, "1970 to 1989"),
        (1990, 2021, "1990 to 2021")]
# the other term for each event where one exists (robustness R4 swap): (term, kind)
ALT = {"pretoria": ("Westhoughton", "in"), "wellington": ("Whitehaven", "in"), "quintinshill": ("Gretna", "plain"),
       "faversham": ("Faversham", "plain"), "glencinema": ("Paisley", "plain"), "croydon": ("Croydon", "plain"),
       "huddersfield": ("Huddersfield", "plain"), "williampit": ("Whitehaven", "plain"), "stockport": ("Stockport", "plain"),
       "bloodysunday": ("Derry", "plain"), "golborne": ("Golborne", "plain"), "penlee": ("Mousehole", "plain"),
       "hungerford": ("Hungerford", "plain"), "lockerbie": ("Lockerbie", "plain"), "dunblane": ("Dunblane", "plain"),
       "omagh": ("Omagh", "plain"), "hatfield": ("Hatfield", "plain"), "greatheck": ("Selby", "plain"),
       "pottersbar": ("Potters Bar", "plain"), "cumbria": ("Cumbria", "plain"), "amesbury": ("Amesbury", "plain"),
       "carmont": ("Stonehaven", "plain"), "bradford": ("Bradford", "in"), "thirsk": ("Thirsk", "plain"),
       "marine": ("Ebbw Vale", "plain"), "staines": ("Staines", "plain"), "freckleton": ("Freckleton", "plain"),
       "newry": ("Newry", "plain"), "grays": ("Grays", "plain"), "birmingham": ("Birmingham", "plain"),
       "arena": ("Manchester", "in"), "ibrox": ("Glasgow", "in"), "hillsborough": ("Sheffield", "in"),
       "lynmouth": ("Lynton", "in"), "morecambe": ("Morecambe", "in"), "enniskillen": ("Enniskillen", "plain")}


def hansard():
    """hansard_monthly.json with the extra plain phrases of hansard_monthly_extra.json merged in (identical where both have a term)"""
    H = jload(os.path.join(RAW, "hansard_monthly.json"))
    X = jload(os.path.join(RAW, "hansard_monthly_extra.json"))
    for t, s in X["plain"].items():
        if t.startswith("in ") and t[3:] in H["inp"]:
            assert H["inp"][t[3:]] == s, t
        if t in H["plain"]:
            assert H["plain"][t] == s, t
        H["plain"][t] = s
    return H


# the extension (events added after the first results, code/events.csv ext = 1): which sample a model run uses
SAMPLE = os.environ.get("DA_SAMPLE", "v1")
assert SAMPLE in ("v1", "ext")
# disaster-specific phrases (sensitivity of counts to the search phrase; added in review, after the first results)
PHRASE = {"aberfan": "Aberfan disaster", "gresford": "Gresford disaster", "hillsborough": "Hillsborough disaster", "grenfell": "Grenfell Tower",
          "kingscross": "King's Cross fire", "moorgate": "Moorgate disaster", "clapham": "Clapham rail", "lockerbie": "Lockerbie"}


def mi(y, m):
    return y * 12 + (m - 1)


def ym(t):
    return f"{t // 12}-{t % 12 + 1:02d}"


T0, T1 = mi(*FIRST), mi(*LAST)


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    raise ValueError(f)


def era(y):
    for a, b, lab in ERAS:
        if a <= y <= b:
            return lab
    return None


def topo_polys(obj):
    """decode a quantised TopoJSON object of the ONS file into {name: shapely geometry}"""
    from shapely.geometry import Polygon, MultiPolygon
    t = jload(os.path.join(GEO, "uk_topo.json"))
    sx, sy = t["transform"]["scale"]; tx, ty = t["transform"]["translate"]
    arcs = []
    for a in t["arcs"]:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(ix):
        pts = []
        for i in ix:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        return pts
    out = {}
    for g in t["objects"][obj]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        ps = [Polygon(ring(p[0]), [ring(h) for h in p[1:]]).buffer(0) for p in polys]
        out[g["properties"]["areanm"]] = MultiPolygon([q for p in ps for q in (p.geoms if hasattr(p, "geoms") else [p])])
    return out
