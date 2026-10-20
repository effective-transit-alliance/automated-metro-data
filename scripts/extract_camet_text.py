"""Extract the text of the CAMET report pages this project relies on into data/camet_text/.

Usage: python extract_camet_text.py

This is so they can be read and searched without the PDFs.
The pages are the bulletins' summaries and new-line tables (附表2),
and the annual reports' tables of new lines and sections on
fully automated operation (FAO, 全自动运行), including FAO km totals.
Run scripts/download_camet.sh first.
"""

import re
import textwrap
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "raw" / "camet"
OUT = ROOT / "data" / "camet_text"

PAGES = {
    "annual-2015": [27],
    "annual-2016": [8, 9, 10, 11, 41],
    "annual-2018": [45],
    "annual-2019": [56],
    "annual-2021": [3, 12, 61],
    "annual-2022": [5, 15, 74],
    "annual-2024": [5, 14, 15],
    "camet-2023": [1, 3, 5, 10, 11, 12],
    "camet-2024": [1, 2, 3, 4, 11, 12, 13, 14],
    "camet-2025": [1, 2, 3, 4, 10, 11, 12, 13, 14],
    "camet-2026h1": [1, 2, 3, 9],
}


def page_text(page: Page) -> str:
    # The watermark is the only text that's rotated (diagonally, by its text matrix),
    # so drop it before it can leak stray characters into the real text.
    unrotated = page.filter(
        lambda obj: obj["object_type"] != "char" or obj["matrix"][1:3] == (0, 0)
    )
    lines = [line.rstrip() for line in unrotated.extract_text(layout=True).splitlines()]
    # Collapse runs of blank lines, and drop the page's left margin.
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip("\n")
    return textwrap.dedent(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, pages in PAGES.items():
        out = [
            f"# {name}.pdf: selected pages, extracted by scripts/extract_camet_text.py",
            "# In the new-line tables, a * after the row number marks an FAO line.",
        ]
        with pdfplumber.open(IN / f"{name}.pdf") as pdf:
            for n in pages:
                out += ["", f"## Page {n}", "", page_text(pdf.pages[n - 1])]
        (OUT / f"{name}.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
