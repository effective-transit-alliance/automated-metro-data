"""Parse Wikipedia's list of driverless train systems into a CSV of lines and their GoA.

Usage: python parse_wikipedia.py OUT.csv driverless.html

The list's GoA3 and GoA4 sections each have a table per continent,
with a row per line: its country, system, line, and the date it became driverless.
That date is also given as `since`, in ISO form, to the precision it's given:
"3 July 2022" is 2022-07-03, "June 2018" is 2018-06, and "2014" is 2014.
Cells spanning several rows are repeated into each of them.
Its "Future systems" section isn't included.
"""

import csv
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag

FIELDS = ["GoA", "country", "system", "line", "date", "since"]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]  # fmt: skip
DATE_RE = re.compile(rf"(?:(\d{{1,2}}) )?(?:({'|'.join(MONTHS)}) )?(\d{{4}})")


def since(date: str) -> str:
    """The first date in a "Date" cell, in ISO form, as precise as it's given."""
    m = DATE_RE.search(date)
    if not m:
        return ""
    day, month, year = m.groups()
    if not month:
        return year
    iso = f"{year}-{MONTHS.index(month) + 1:02}"
    return f"{iso}-{int(day):02}" if day else iso


def cell_text(cell: Tag) -> str:
    for sup in cell.find_all("sup"):
        sup.decompose()
    return re.sub(r"\s+", " ", cell.get_text(" ")).strip()


def table_rows(table: Tag) -> list[list[str]]:
    """The table's body rows, with spanning cells repeated into each row they span."""
    rows: list[list[str]] = []
    pending: dict[int, tuple[str, int]] = {}  # column: (text, rows left)
    for tr in table.find_all("tr")[1:]:
        cells = iter(tr.find_all(["td", "th"], recursive=False))
        row: list[str] = []
        col = 0
        while True:
            if col in pending:
                text, left = pending[col]
                row.append(text)
                if left > 1:
                    pending[col] = (text, left - 1)
                else:
                    del pending[col]
                col += 1
                continue
            cell = next(cells, None)
            if cell is None:
                break
            text = cell_text(cell)
            span = int(str(cell.get("rowspan", "1")).strip() or 1)
            if span > 1:
                pending[col] = (text, span - 1)
            row.append(text)
            col += 1
        rows.append(row)
    return rows


def main() -> None:
    out, page = sys.argv[1:]
    soup = BeautifulSoup(Path(page).read_text(), "html.parser")
    goa = ""
    lines = []
    for el in soup.find_all(["h2", "h3", "table"]):
        if el.name in ("h2", "h3"):
            heading = el.get_text(" ", strip=True)
            m = re.match(r"GoA(\d)", heading)
            if el.name == "h3":
                goa = f"GoA{m.group(1)}" if m else ""
            elif not heading.startswith("Grade-of-Automation"):
                goa = ""
            continue
        if not goa or "wikitable" not in (el.get("class") or []):
            continue
        for row in table_rows(el):
            if len(row) >= 4:
                lines.append(dict(zip(FIELDS, [goa, *row[:4], since(row[3])], strict=True)))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(lines)
    print(f"wrote {len(lines)} lines to {out}")


if __name__ == "__main__":
    main()
