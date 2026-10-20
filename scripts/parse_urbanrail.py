"""Parse UrbanRail.net yearly "news" pages into a CSV of opening events.

Usage: python parse_urbanrail.py OUT.csv news2016.htm news2017.htm ...

Each opening on those pages is a <p> with a mode icon (metro, light rail, ...),
a date, a city link, the line and its termini, the length, and an optional
"NEW LINE!" flag for openings of entirely new lines.
"""

import csv
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
        city, _, desc = rest.partition(" -- ")
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
    for r in rows:
        # A stable ID for hand-kept overrides to refer to.
        id_key = f"{r['date']}|{r['city']}|{r['description']}".encode()
        r["id"] = hashlib.sha1(id_key).hexdigest()[:8]
    with open(out, "w", newline="") as f:
        fields = ["id"] + [k for k in rows[0] if k != "id"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
