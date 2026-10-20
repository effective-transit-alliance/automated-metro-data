"""Chart the share of new lines that are automated (above GoA2), by year.

Usage: uv run python scripts/plot_share.py

Reads data/urban_rail_openings.csv and, for each region
(worldwide, mainland China, and outside mainland China), writes:
- data/automated{measure}_share_by_year{suffix}_{range}.csv: the numbers behind the chart.
- charts/automated{measure}_share_by_year{suffix}_{range}.svg: a bar chart of the share per year.
- charts/automated{measure}_share_by_year{suffix}_{range}.png: the same at 2x, for apps without SVG support.
  These aren't committed.
The measure is either the count of new lines (no {measure} part)
or km (`_km`) of all openings, new lines and extensions alike;
openings without a known length are left out of the km charts.
Each comes in two ranges: 2016_to_2025 (full years only)
and 2016_to_2026 (including the current, partial year).

A line counts if it is new-build, fully grade-separated, and not mainline.
"""

import csv
from collections import Counter
from html import escape
from pathlib import Path

import resvg_py

ROOT = Path(__file__).resolve().parent.parent
OPENINGS = ROOT / "data" / "urban_rail_openings.csv"

# File-name suffix: (description for the chart, which countries count).
# Hong Kong and Macau are outside CAMET's statistics, so they count as outside China.
REGIONS = {
    "": ("worldwide", lambda country: True),
    "_china": ("in mainland China", lambda country: country == "China"),
    "_ex_china": ("outside mainland China", lambda country: country != "China"),
}

# Layout, in px.
WIDTH = 760
HEIGHT = 436
LEFT = 56
RIGHT = 16
TOP = 72
BOTTOM = 80
BAR_GAP = 0.3


def counted(r, by_km):
    """Whether an opening counts: new lines by count, or any new km by length.

    Counting by km includes extensions, which take their line's GoA,
    but not in-fill stations, which add no length.
    """
    if r["grade_separated"] != "yes" or r["mainline"] != "no":
        return False
    if by_km:
        return "in-fill" not in r["note"]
    return r["new_build"] == "yes"


def tally(in_region, last_year, by_km):
    total = Counter()
    automated = Counter()
    unknown_km = 0
    last_date = ""
    with open(OPENINGS, newline="") as f:
        for r in csv.DictReader(f):
            if not counted(r, by_km) or not in_region(r["country"]):
                continue
            year = r["opening_date"][:4]
            if year > last_year:
                continue
            last_date = max(last_date, r["opening_date"])
            if by_km and not r["km"]:
                unknown_km += 1
                continue
            weight = float(r["km"]) if by_km else 1
            total[year] += weight
            automated[year] += weight if r["automated"] == "yes" else 0
    years = sorted(total)
    return [(y, total[y], automated[y]) for y in years], last_date, unknown_km


def latest_opening():
    with open(OPENINGS, newline="") as f:
        return max(r["opening_date"] for r in csv.DictReader(f))


def write_table(rows, table, unit):
    with open(table, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", f"new_{unit}", f"automated_{unit}", "automated_share"])
        for year, n, a in rows:
            w.writerow([year, fmt(n), fmt(a), f"{a / n:.3f}"])


def fmt(x):
    """Format a line count or a length in km."""
    return f"{x:.0f}" if x == int(x) or x >= 10 else f"{x:.1f}"


def bar_path(x, y, w, h, r):
    """A bar with rounded top corners, square at the baseline."""
    r = min(r, w / 2, h)
    return (
        f"M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h:.1f} Z"
    )


def write_svg(rows, last_date, svg, region, unit, unknown_km):
    plot_w = WIDTH - LEFT - RIGHT
    plot_h = HEIGHT - TOP - BOTTOM
    step = plot_w / len(rows)
    bar_w = step * (1 - BAR_GAP)
    n_all = sum(n for _, n, _ in rows)
    a_all = sum(a for _, _, a in rows)
    first_year = rows[0][0]
    last_year = rows[-1][0]
    # Only the year of the latest opening of any kind can be incomplete.
    partial_year = latest_opening()[:4]

    def y_of(share):
        return TOP + plot_h * (1 - share)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="t d" '
        'font-family="system-ui, -apple-system, Segoe UI, DejaVu Sans, sans-serif">',
        f'<title id="t">Share of new metro lines {region} that are automated (&gt; GoA2), by year</title>',
        f'<desc id="d">{fmt(a_all)}/{fmt(n_all)} new grade-separated, non-mainline urban rail lines '
        f"opened in 2016 to {last_date} are automated.</desc>",
        "<style>",
        ".bg{fill:#fcfcfb}.bar{fill:#2a78d6}.bar.partial{fill-opacity:.55}",
        ".grid{stroke:#e4e3df;stroke-width:1}.axis{stroke:#a3a29c;stroke-width:1}",
        ".t1{fill:#0b0b0b}.t2{fill:#52514e}",
        "@media (prefers-color-scheme: dark){",
        ".bg{fill:#1a1a19}.bar{fill:#3987e5}.grid{stroke:#2e2e2c}.axis{stroke:#5d5c57}",
        ".t1{fill:#ffffff}.t2{fill:#c3c2b7}}",
        "</style>",
        f'<rect class="bg" width="{WIDTH}" height="{HEIGHT}" rx="8"/>',
        f'<text class="t1" x="{LEFT}" y="28" font-size="17" font-weight="600">'
        f"Automated share of new metro {'km' if unit == 'km' else 'lines'}, {region}</text>",
        f'<text class="t2" x="{LEFT}" y="50" font-size="13">'
        f"&gt; GoA2; {'grade-separated, non-mainline openings' if unit == 'km' else 'new-build, grade-separated, non-mainline lines'}; "
        f"{fmt(a_all)}/{fmt(n_all)}{' km' if unit == 'km' else ''} "
        f"({a_all / n_all:.0%}) in {first_year} to {last_year}</text>",
    ]
    for share in (0, 0.25, 0.5, 0.75):
        y = y_of(share)
        cls = "axis" if share == 0 else "grid"
        out.append(f'<line class="{cls}" x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(
            f'<text class="t2" x="{LEFT - 8}" y="{y + 4:.1f}" font-size="12" '
            f'text-anchor="end">{share:.0%}</text>'
        )
    for i, (year, n, a) in enumerate(rows):
        share = a / n
        x = LEFT + i * step + (step - bar_w) / 2
        y = y_of(share)
        cx = x + bar_w / 2
        partial = year == partial_year
        label = f"{year}: {fmt(a)}/{fmt(n)} new {unit} automated ({share:.0%})"
        if partial:
            label += f", through {last_date}"
        out.append(f"<g><title>{escape(label)}</title>")
        # A hit target taller than the bar, for the native tooltip.
        out.append(
            f'<rect x="{LEFT + i * step:.1f}" y="{TOP}" width="{step:.1f}" '
            f'height="{plot_h}" fill="transparent"/>'
        )
        cls = "bar partial" if partial else "bar"
        out.append(f'<path class="{cls}" d="{bar_path(x, y, bar_w, y_of(0) - y, 4)}"/>')
        out.append(
            f'<text class="t1" x="{cx:.1f}" y="{y - 6:.1f}" font-size="12" '
            f'text-anchor="middle">{share:.0%}</text>'
        )
        out.append("</g>")
        year_label = f"{year}*" if partial else year
        out.append(
            f'<text class="t1" x="{cx:.1f}" y="{y_of(0) + 18:.1f}" font-size="12" '
            f'text-anchor="middle">{year_label}</text>'
        )
        out.append(
            f'<text class="t2" x="{cx:.1f}" y="{y_of(0) + 34:.1f}" font-size="11" '
            f'text-anchor="middle">{fmt(a)}/{fmt(n)}</text>'
        )
    footer = [f"Below each year: automated/new {unit}."]
    if unit == "km":
        footer[0] += f" New lines and extensions; {unknown_km} openings of unknown length left out."
    footer.append(
        (f"* {partial_year} through {last_date}. " if last_year == partial_year else "")
        + "Sources: UrbanRail.net, CAMET."
    )
    for i, line in enumerate(footer):
        out.append(
            f'<text class="t2" x="{LEFT}" y="{HEIGHT - 24 + 14 * i}" font-size="11">{line}</text>'
        )
    out.append("</svg>")
    svg.parent.mkdir(exist_ok=True)
    svg.write_text("\n".join(out) + "\n")


def write_png(svg):
    png = svg.with_suffix(".png")
    # Twice the SVG's size, so it stays sharp on high-DPI screens.
    png.write_bytes(bytes(resvg_py.svg_to_bytes(svg_path=str(svg), zoom=2)))


def main():
    for last_year in ("2025", "2026"):
        span = f"2016_to_{last_year}"
        for suffix, (region, in_region) in REGIONS.items():
            for by_km in (False, True):
                unit = "km" if by_km else "lines"
                rows, last_date, unknown_km = tally(in_region, last_year, by_km)
                measure = "_km" if by_km else ""
                name = f"automated{measure}_share_by_year{suffix}_{span}"
                write_table(rows, ROOT / "data" / f"{name}.csv", unit)
                svg = ROOT / "charts" / f"{name}.svg"
                write_svg(rows, last_date, svg, region, unit, unknown_km)
                write_png(svg)
                n = sum(n for _, n, _ in rows)
                a = sum(a for _, _, a in rows)
                print(f"{name}: {fmt(a)}/{fmt(n)} {a / n:.0%}")


if __name__ == "__main__":
    main()
