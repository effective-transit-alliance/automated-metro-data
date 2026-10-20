"""Build data/urban_rail_openings.csv and its filtered subsets.

Usage: python build_openings.py

Every UrbanRail.net opening since 2016 in data/urbanrail_events.csv is included,
with each field derived from it, unless one of the overrides in data/curation/ says otherwise.
In all of them, a blank field means "use the derived value", and "-" means "leave it blank".
- events.csv: per-event overrides, keyed by UrbanRail.net event ID,
  plus openings UrbanRail.net doesn't list, whose IDs start with "x".
- cities.csv: per-city overrides of the city's name and country.
  The country is otherwise derived from the city's UrbanRail.net link, through countries.csv.
- line_names.csv: per-city renames of the line names parse_urbanrail.py derives.
- lines.csv: per-line overrides of mode, mainline, grade separation, and GoA.
  Lines not listed there get the defaults for their UrbanRail.net mode below.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURATION = ROOT / "data" / "curation"
EVENTS = ROOT / "data" / "urbanrail_events.csv"
FIRST_DATE = "2016-01-01"
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


def read(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def override(value: str, derived: str) -> str:
    """Apply an override field: blank keeps the derived value, and "-" blanks it."""
    if value == "-":
        return ""
    return value or derived


def events() -> list[dict[str, str]]:
    """Every opening, with each field derived and then overridden."""
    countries = {r["code"]: r["country"] for r in read(CURATION / "countries.csv")}
    cities = {r["urbanrail_city"]: r for r in read(CURATION / "cities.csv")}
    renames = {
        (r["city"], r["urbanrail_line"]): r["line"] for r in read(CURATION / "line_names.csv")
    }
    overrides = {r["id"]: r for r in read(CURATION / "events.csv")}
    out = []
    for e in read(EVENTS):
        if e["date"] < FIRST_DATE:
            continue
        o = overrides.pop(e["id"], {})
        c = cities.get(e["city"], {})
        city = override(c.get("city", ""), e["city"])
        derived_line = renames.get((city, e["line"]), e["line"])
        description = override(o.get("description", ""), e["description"])
        row = {
            "id": e["id"],
            "date": override(o.get("date", ""), e["date"]),
            "urbanrail_mode": override(o.get("urbanrail_mode", ""), e["mode"]),
            "city": override(o.get("city", ""), city),
            "country": override(c.get("country", ""), countries.get(e["country_code"], "")),
            "line": override(o.get("line", ""), derived_line),
            "new_build": override(o.get("new_build", ""), "yes" if e["new_flag"] else "no"),
            "include": override(o.get("include", ""), "yes"),
            "km": override(o.get("km", ""), str(float(e["km"])) if e["km"] else ""),
            "description": description,
            "note": override(o.get("note", ""), ""),
        }
        out.append(row)
    unused = sorted(i for i in overrides if not i.startswith("x"))
    if unused:
        sys.exit(f"events.csv rows matching no event: {unused}")
    # Openings UrbanRail.net doesn't list, given in full.
    country_of = {r["city"]: r["country"] for r in out}
    for o in overrides.values():
        out.append({**o, "country": country_of.get(o["city"], "")})
    return out


def main() -> None:
    lines = {(r["city"], r["line"]): r for r in read(CURATION / "lines.csv")}
    used = set()
    out = []
    for e in events():
        if e["include"] != "yes":
            continue
        country = e["country"]
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


def write(path: Path, rows: list[dict[str, str]]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
