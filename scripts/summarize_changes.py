"""Summarize how a rebuild changed data/urban_rail_openings.csv, in Markdown.

Usage: python summarize_changes.py OLD.csv NEW.csv

Lists the openings added and removed, the GoA changes to the rest,
and how the headline counts changed, for the refresh bot's pull requests.
Openings are matched by their UrbanRail.net ID,
or by date, city, and description for the ones it doesn't list.
"""

import csv
import sys
from pathlib import Path

Row = dict[str, str]


def read(path: Path) -> dict[tuple[str, ...], Row]:
    with open(path, newline="") as f:
        return {key(r): r for r in csv.DictReader(f)}


def key(r: Row) -> tuple[str, ...]:
    if r["urbanrail_id"]:
        return (r["urbanrail_id"],)
    return (r["opening_date"], r["city"], r["description"])


def describe(r: Row) -> str:
    new = ", new line" if r["new_build"] == "yes" else ""
    return f"{r['opening_date']} {r['city']} {r['line']} ({r['GoA']}{new}): {r['description']}"


def counts(rows: dict[tuple[str, ...], Row]) -> tuple[int, int, float, float]:
    """New metro-like lines and the automated ones, and the km of all openings and automated km."""
    metro_like = [
        r for r in rows.values() if r["grade_separated"] == "yes" and r["mainline"] == "no"
    ]
    lines = [r for r in metro_like if r["new_build"] == "yes"]
    km = [r for r in metro_like if r["km"]]
    return (
        len(lines),
        sum(r["automated"] == "yes" for r in lines),
        sum(float(r["km"]) for r in km),
        sum(float(r["km"]) for r in km if r["automated"] == "yes"),
    )


def main() -> None:
    old = read(Path(sys.argv[1]))
    new = read(Path(sys.argv[2]))
    sections = {
        "New openings": [describe(new[k]) for k in new if k not in old],
        "Removed openings": [describe(old[k]) for k in old if k not in new],
        "GoA changes": [
            f"{describe(new[k])}: was {old[k]['GoA']} ({old[k]['GoA_basis']}), "
            f"now {new[k]['GoA_basis']}"
            for k in new
            if k in old and old[k]["GoA"] != new[k]["GoA"]
        ],
    }
    for title, items in sections.items():
        print(f"## {title}\n")
        print("\n".join(f"- {i}" for i in items) if items else "None.")
        print()
    old_lines, old_automated, old_km, old_automated_km = counts(old)
    new_lines, new_automated, new_km, new_automated_km = counts(new)
    print("## Headline numbers\n")
    print(f"- Automated new lines: {old_automated} of {old_lines} → {new_automated} of {new_lines}")
    print(
        f"- Automated km: {old_automated_km:,.0f} of {old_km:,.0f}"
        f" → {new_automated_km:,.0f} of {new_km:,.0f}"
    )


if __name__ == "__main__":
    main()
