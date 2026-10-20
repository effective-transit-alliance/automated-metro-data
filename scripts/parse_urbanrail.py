"""Parse UrbanRail.net yearly "news" pages into a CSV of opening events.

Usage: python parse_urbanrail.py OUT.csv news2016.htm news2017.htm ...

Each opening on those pages is a <p> with a mode icon (metro, light rail, ...),
a date, a city link, the line and its termini, the length, and an optional
"NEW LINE!" flag for openings of entirely new lines.
"""

import csv
import difflib
import hashlib
import html
import re
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

# fmt: off
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
# fmt: on
# Older pages leave out the year, which then comes from the page name.
DATE_RE = re.compile(r"^(\d{1,2})\s*([A-Za-z]+)\.?\s*(\d{4})?\s*--\s*(.*)$")
KM_RE = re.compile(r"\(([~\d.,]+)\s*km")


MARK = "\x00"
SEG_RE = re.compile(r"(.+?\(\s*~?[\d.,]+\s*km[^)]*\))\s*(NEW\s+[A-Z]+!)?\s*", re.S)


def segments(desc: str) -> list[tuple[str, str]]:
    """Split an entry that lists several lines (each with its own length)."""
    out: list[tuple[str, str]] = []
    pos = 0
    for m in SEG_RE.finditer(desc):
        seg = re.sub(r"^[\s;,&+|\-\u2013]+", "", m.group(1)).strip()
        out.append((seg, m.group(2) or ""))
        pos = m.end()
    tail = desc[pos:].strip()
    if tail or not out:
        flag = re.search(r"NEW\s+[A-Z]+!", tail)
        tail = re.sub(r"NEW\s+[A-Z]+!", "", tail).strip()
        if tail:
            out.append((tail, flag.group(0) if flag else ""))
        elif flag and out:
            out[-1] = (out[-1][0], flag.group(0))
    return out


def parse(path: str) -> Iterator[dict[str, str]]:
    page_year = re.findall(r"\d{4}", path)[-1]
    raw = Path(path).read_bytes().decode("cp1252", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    # The HTML nests <p> tags unpredictably, so work on flat text instead,
    # with each mode icon turned into a marker that starts a new entry.
    for img in soup.find_all("img", src=re.compile("minilogo")):
        img.replace_with(f"{MARK}{str(img['src']).split('-minilogo')[0]}{MARK}")
    for a in soup.find_all("a", href=re.compile(r"^[a-z]{2}/[a-z]{2}/.*\.htm")):
        a.replace_with(f"{a.get_text(' ')}{MARK}{a['href']}{MARK}")
    text = re.sub(r"\s+", " ", html.unescape(soup.get_text(" ")))
    chunks = text.split(MARK)
    for i in range(1, len(chunks) - 1, 2):
        mode = chunks[i]
        body = chunks[i + 1]
        href = ""
        # A city link splits the entry: body, href, rest.
        if i + 3 < len(chunks) and chunks[i + 2].endswith(".htm"):
            href = chunks[i + 2]
            body = body + chunks[i + 3]
        if mode not in {"metro", "light-rail", "monorail", "people-mover", "s-bahn", "tram"}:
            continue
        m = DATE_RE.match(body.strip())
        if not m:
            continue
        day, mon, year, rest = m.groups()
        year = year or page_year
        month = MONTHS.get(mon.lower()[:4]) or MONTHS.get(mon.lower()[:3])
        if month is None:
            continue
        opened = datetime(int(year), month, int(day)).date()
        parts = href.split("/")
        # Some entries leave out the space after the second "--", as in "Dakar --[TER]".
        city, _, desc = rest.partition(" --")
        desc = desc.strip()
        desc = re.sub(r">\s*More info at", " ", desc)
        desc = re.split(r"\.{3,}|All dates shown|More openings in", desc)[0].strip()
        for seg, flag in segments(desc):
            km = KM_RE.search(seg)
            yield {
                "date": opened.isoformat(),
                "mode": mode,
                "region": parts[0] if len(parts) > 2 else "",
                "country_code": parts[1] if len(parts) > 2 else "",
                "city": city.strip(),
                "description": seg,
                "km": km.group(1).replace(",", ".").lstrip("~") if km else "",
                "new_flag": flag.replace("  ", " "),
                "city_page": href,
            }


def new_id(r: dict[str, str]) -> str:
    key = f"{r['date']}|{r['city']}|{r['description']}".encode()
    return hashlib.sha1(key).hexdigest()[:8]


def similarity(a: dict[str, str], b: dict[str, str]) -> float:
    def norm(r: dict[str, str]) -> str:
        return re.sub(r"\W", "", r["description"]).lower()

    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def assign_ids(rows: list[dict[str, str]], previous: list[dict[str, str]]) -> None:
    """Give each event its ID from the previous parse, if it was in it, or else a new one.

    UrbanRail.net sometimes rewrites entries (e.g. "Line 2 X" to "[2] X"),
    so events are matched on their date and city, which it doesn't rewrite,
    then on length and how similar their descriptions are.
    That keeps the IDs that data/curation/events.csv refers to.
    """
    groups: dict[tuple[str, str], tuple[list[dict[str, str]], list[dict[str, str]]]] = {}
    for r in rows:
        groups.setdefault((r["date"], r["city"]), ([], []))[0].append(r)
    for p in previous:
        groups.setdefault((p["date"], p["city"]), ([], []))[1].append(p)
    edited = 0
    gone: list[dict[str, str]] = []
    for new, old in groups.values():
        # Best matches first: same length, then the most similar description.
        pairs = sorted(
            (
                (r["km"] == p["km"], similarity(r, p), i, j)
                for i, r in enumerate(new)
                for j, p in enumerate(old)
            ),
            reverse=True,
        )
        matched_new: set[int] = set()
        matched_old: set[int] = set()
        for _, _, i, j in pairs:
            if i in matched_new or j in matched_old:
                continue
            matched_new.add(i)
            matched_old.add(j)
            new[i]["id"] = old[j]["id"]
            edited += new[i]["description"] != old[j]["description"]
        gone += [p for j, p in enumerate(old) if j not in matched_old]
    ids = {p["id"] for p in previous}
    added = [r for r in rows if "id" not in r]
    for r in added:
        r["id"] = new_id(r)
        assert r["id"] not in ids, f"ID {r['id']} is already taken"
        ids.add(r["id"])
    print(f"{edited} events edited upstream kept their IDs", file=sys.stderr)
    for label, events in (("new", added), ("gone", gone)):
        for r in events:
            print(
                f"{label}: {r['id']} {r['date']} {r['city']}: {r['description']}", file=sys.stderr
            )


def main() -> None:
    out, *pages = sys.argv[1:]
    # Leave out openings announced for after the pages were downloaded,
    # so re-parsing the same pages always gives the same events.
    downloaded = (Path(pages[0]).parent / "downloaded.txt").read_text().strip()
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for page in pages:
        for r in parse(page):
            if r["date"] > downloaded:
                continue
            key = (r["date"], r["city"], re.sub(r"\W", "", r["description"]).lower())
            # Pages overlap at year boundaries; keep a flagged copy if any.
            if key not in by_key or (r["new_flag"] and not by_key[key]["new_flag"]):
                by_key[key] = r
    rows = sorted(by_key.values(), key=lambda r: (r["date"], r["city"]))
    # Match against the previous parse, if any, so the IDs stay stable.
    previous: list[dict[str, str]] = []
    if Path(out).exists():
        with open(out, newline="") as f:
            previous = list(csv.DictReader(f))
    assign_ids(rows, previous)
    with open(out, "w", newline="") as f:
        fields = ["id"] + [k for k in rows[0] if k != "id"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
