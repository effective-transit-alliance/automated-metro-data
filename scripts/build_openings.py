"""Build data/urban_rail_openings.csv and its filtered subsets from the curation files.

Usage: python build_openings.py

Inputs, all in data/curation/:
- events.csv: one row per UrbanRail.net opening (plus a few added rows),
  with the hand-reviewed line name, new-build flag, and include flag.
- cities.csv: UrbanRail.net city names to clean city and country names.
- lines.csv: per-line overrides of mode, mainline, grade separation, and GoA.
  Lines not listed there get the defaults for their UrbanRail.net mode below.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURATION = ROOT / "data" / "curation"
OUT = ROOT / "data" / "urban_rail_openings.csv"
UNKNOWN_LENGTH = ROOT / "data" / "unknown_length_openings.csv"
METRO_LIKE = ROOT / "data" / "metro_like_openings.csv"
AUTOMATED_METRO_LIKE = ROOT / "data" / "automated_metro_like_openings.csv"

# (mode, mainline, grade_separated, GoA) for each UrbanRail.net mode icon.
# Trams run on sight (GoA0); other lines default to the most common level.
DEFAULTS = {
    "metro": ("metro", "no", "yes", "GoA2"),
    "light-rail": ("light rail", "no", "no", "GoA1"),
    "tram": ("tram", "no", "no", "GoA0"),
    "monorail": ("monorail", "no", "yes", "GoA2"),
    "people-mover": ("people mover", "no", "yes", "GoA4"),
    "s-bahn": ("commuter rail", "yes", "no", "GoA1"),
}
# China's suburban lines (市域快轨) are metro-standard, not mainline.
CHINA_SUBURBAN = ("suburban metro", "no", "yes", "GoA2")
DEFAULT_BASIS = "mode default; unverified"
# CAMET lists every FAO line opened since 2021, and its FAO totals
# leave no room for unlisted ones before that.
CAMET_SOURCE = "https://www.camet.org.cn/xytj/tjxx/ (reports in data/raw/camet/)"
CHINA_NOT_FAO = "CAMET: not FAO (inferred from its FAO tables and totals)"

FIELDS = [
    "opening_date",
    "country",
    "city",
    "line",
    "mode",
    "km",
    "mainline",
    "grade_separated",
    "new_build",
    "GoA",
    "automated",
    "GoA_basis",
    "GoA_source",
    "description",
    "note",
    "urbanrail_id",
]


def read(name):
    with open(CURATION / name, newline="") as f:
        return list(csv.DictReader(f))


def main():
    cities = {}
    for r in read("cities.csv"):
        cities[r["city"]] = r["country"]
    lines = {(r["city"], r["line"]): r for r in read("lines.csv")}
    used = set()
    out = []
    for e in read("events.csv"):
        if e["include"] != "yes":
            continue
        country = cities[e["city"]]
        mode, mainline, graded, goa = DEFAULTS[e["urbanrail_mode"]]
        if e["urbanrail_mode"] == "s-bahn" and country == "China":
            mode, mainline, graded, goa = CHINA_SUBURBAN
        basis = DEFAULT_BASIS
        source = ""
        if country == "China" and e["urbanrail_mode"] != "tram":
            basis = CHINA_NOT_FAO
            source = CAMET_SOURCE
        override = lines.get((e["city"], e["line"]))
        if override:
            used.add((e["city"], e["line"]))
            mode = override["mode"] or mode
            mainline = override["mainline"] or mainline
            graded = override["grade_separated"] or graded
            if override["GoA"] or override["GoA_basis"]:
                goa = override["GoA"]
                basis = override["GoA_basis"]
                source = override["GoA_source"] or (
                    CAMET_SOURCE if basis.startswith("CAMET") else ""
                )
        automated = "" if goa == "" else ("yes" if float(goa.removeprefix("GoA")) > 2 else "no")
        out.append(
            {
                "opening_date": e["date"],
                "country": country,
                "city": e["city"],
                "line": e["line"],
                "mode": mode,
                "km": e["km"],
                "mainline": mainline,
                "grade_separated": graded,
                "new_build": e["new_build"],
                "GoA": goa,
                "automated": automated,
                "GoA_basis": basis,
                "GoA_source": source,
                "description": e["description"],
                "note": e["note"],
                "urbanrail_id": "" if e["id"].startswith("x") else e["id"],
            }
        )
    unused = sorted(set(lines) - used)
    if unused:
        sys.exit(f"lines.csv rows matching no event: {unused}")
    out.sort(key=lambda r: (r["opening_date"], r["country"], r["city"], r["line"]))
    write(OUT, out)
    # The new lines the line-count charts count, and the automated ones among them.
    metro_like = [
        r
        for r in out
        if r["new_build"] == "yes" and r["grade_separated"] == "yes" and r["mainline"] == "no"
    ]
    write(METRO_LIKE, metro_like)
    write(AUTOMATED_METRO_LIKE, [r for r in metro_like if r["automated"] == "yes"])
    # Openings the km charts leave out for lack of a length.
    unknown = [
        r
        for r in out
        if r["grade_separated"] == "yes"
        and r["mainline"] == "no"
        and not r["km"]
        and "in-fill" not in r["note"]
    ]
    fields = ["opening_date", "country", "city", "line", "new_build", "GoA", "description"]
    with open(UNKNOWN_LENGTH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(unknown)
    print(f"wrote {len(unknown)} rows to {UNKNOWN_LENGTH.relative_to(ROOT)}")


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
