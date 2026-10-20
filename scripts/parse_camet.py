"""Extract CAMET's per-line tables of new urban rail lines into one CSV.

Usage: python parse_camet.py OUT.csv REPORT.pdf...

CAMET's bulletins have an appendix table (附表2) listing every line or section
that opened that year, with a "*" after the row number for lines with
fully automated operation (FAO, 全自动运行).
The PDFs carry a diagonal watermark (中国城市轨道交通协会)
whose characters leak into cells, so those are stripped.
"""

import csv
import re
import sys

import pdfplumber

WATERMARK = set("中国城市轨道交通协会")
HEADER = ["序号", "城市", "线路名称"]


def clean(cell, numeric=False):
    cell = (cell or "").replace("\n", "")
    if numeric:
        return re.sub(r"[^\d.*]", "", cell)
    return cell.strip()


def clean_name(cell):
    # Watermark characters only leak in as whole stray characters
    # on their own line, so drop lines made up entirely of them.
    lines = (cell or "").split("\n")
    return "".join(line for line in lines if not (line and set(line) <= WATERMARK)).strip()


def clean_mode(cell):
    lines = [line for line in (cell or "").split("\n") if line.strip()]
    return lines[-1].strip() if lines else ""


def rows(path):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or [clean(c) for c in table[0][:3]] != HEADER:
                    continue
                for r in table[1:]:
                    num = clean(r[0], numeric=True)
                    if not re.fullmatch(r"\d+\*?", num):
                        continue
                    date = re.search(r"\d{4}\.\d{2}\.\d{2}", r[4] or "")
                    yield {
                        "report": path.rsplit("/", 1)[-1],
                        "row": num.rstrip("*"),
                        "fao": int(num.endswith("*")),
                        "city": clean_name(r[1]),
                        "line": clean_name(r[2]),
                        "km": clean(r[3], numeric=True),
                        "date": date.group(0).replace(".", "-") if date else "",
                        "mode": clean_mode(r[5]),
                        "stations": clean(r[6], numeric=True),
                        "note": clean_name(r[7]) if len(r) > 7 else "",
                    }


def main():
    out, *reports = sys.argv[1:]
    all_rows = [r for path in reports for r in rows(path)]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        w.writeheader()
        w.writerows(all_rows)


if __name__ == "__main__":
    main()
