# Automated Metro Data

What share of the new metro lines opened worldwide in the last decade
are automated above GoA2?

This repo collects every new urban rail line opened since 2016-01-01
that is fully grade-separated and not part of the mainline railway,
tags each one with its grade of automation (GoA),
and computes the automated share.

## Scope

A line is counted if it is:

- **New-build**: an entirely new line, not an extension of an existing one.
  A line that opens in stages is counted once, at its first opening.
- **Fully grade-separated**: metro, grade-separated light rail, monorail,
  and automated people movers count; trams and street-running light rail do not.
- **Non-mainline**: lines built to railway standards are mainline and don't count,
  such as S-Bahn, RER, commuter rail, and China's 市域(郊)铁路 (suburban railways,
  designed under the railway standard TB 10624).
  Suburban lines built to urban rail standards, like a metro, do count,
  such as China's 市域快轨 (suburban rapid rail).
  In China, the two are told apart by the line's official category, top speed,
  and who built it;
  Shanghai's Airport Link Line and Ningbo Line 12 are the 市域(郊)铁路 among the new lines.
- **Opened between 2016-01-01 and today**.

Lines are counted **by line**, not by km,
though the length at first opening is kept where known.

### The full openings list

To decide which openings are new lines, every opening has to be classified anyway,
so [`data/urban_rail_openings.csv`](data/urban_rail_openings.csv) lists **every** urban rail opening since 2016-01-01
that UrbanRail.net records (metro, light rail, tram, monorail, people mover,
and purpose-built suburban rail), one row per opened line or section,
sorted by opening date.
Besides the date, country, city, line, length, and GoA,
each row records:

- `mode`: what the line calls itself (metro, light rail, tram, monorail, commuter rail, and so on).
- `mainline`: whether it runs on or as part of the mainline railway.
- `grade_separated`: whether it is fully grade-separated.
- `new_build`: whether it is an entirely new line (yes) or an extension or in-fill (no).

The headline share is a filter of this list:
`new_build`, `grade_separated`, and not `mainline`.
For easier reading, those openings are also in [`data/metro_like_openings.csv`](data/metro_like_openings.csv),
and the automated ones among them in [`data/automated_metro_like_openings.csv`](data/automated_metro_like_openings.csv).
Mainline openings that UrbanRail.net doesn't track, such as high-speed and intercity lines,
are out of scope.

### What counts as automated

A line counts as automated if its GoA is above GoA2:

- **GoA4**: unattended train operation (UTO),
  including lines built for it that start out with staff on board.
  That covers Chinese lines designated as fully automated operation (FAO) by CAMET,
  which often open with a driver or attendant on board.
- **GoA3**: driverless, with an attendant on board who doesn't drive.
- **GoA2.5**: not an official grade, but used here for lines
  built for UTO, with GoA4-capable trains and signalling (and usually platform screen doors),
  that run with a driver in the cab who closes the doors and starts each departure.
  This is the norm for new Indian metro lines
  (Mumbai Lines 2A, 7, 3, 2B, and 9, Bengaluru's Yellow Line, Bhopal, Indore,
  Navi Mumbai Line 1, and Delhi's Grey Line).

Lines with only CBTC signalling, without those UTO features, are GoA2 and not counted.
Lines converted to UTO long after opening, such as Guangzhou Line 7
(opened 2016, FAO from December 2024), keep the GoA they opened with.

## Findings

![Share of new metro lines that are automated, by year](charts/automated_share_by_year_2016_to_2026.svg)

Of the **361 new lines** opened from 2016-01-01 through 2026-09-29
that are new-build, fully grade-separated, and not mainline,
**135 (37%) are automated** above GoA2.
They're listed in [`data/metro_like_openings.csv`](data/metro_like_openings.csv)
and [`data/automated_metro_like_openings.csv`](data/automated_metro_like_openings.csv).

- **The share has risen sharply.**
  It was 19% (32 of 168) for lines opened in 2016–2020,
  53% (103 of 193) in 2021–2026,
  and 65% (55 of 85) in 2024–2026.
- **China drove the rise.**
  China opened 234 of the 361 lines.
  Its automated share went from 6% (6 of 107) in 2016–2020
  to 65% (33 of 51) in 2024–2026,
  as fully automated operation became the default for new Chinese metro lines.
- **Elsewhere the share has been steadier and higher.**
  Outside China, 51% of new lines (65 of 127) are automated,
  and 56% (53 of 94) excluding India.
  In India, 12 of 33 new lines (36%) are automated:
  Delhi's Magenta and Pink lines at GoA4,
  and ten lines at GoA2.5.
- Almost all of the rest are GoA4;
  the only GoA3 line is Jakarta's Jabodebek LRT.

The same, split into mainland China and everywhere else
(including Hong Kong and Macau, which CAMET doesn't cover):

![Share of new metro lines in mainland China that are automated, by year](charts/automated_share_by_year_china_2016_to_2026.svg)

![Share of new metro lines outside mainland China that are automated, by year](charts/automated_share_by_year_ex_china_2016_to_2026.svg)

Each chart also has a `2016_to_2025` version with full years only,
in which 121 of 340 new lines (36%) are automated worldwide.
Every chart also has a km version (`automated_km_share_*`),
counting the km of every grade-separated, non-mainline opening,
new lines and extensions alike, each extension taking its line's GoA:
3,378 of 11,583 km (29%) opened in 2016–2026 are automated worldwide,
23% in mainland China and 45% elsewhere.
The km share is lower than the line share because extensions,
mostly of older lines built before automation was common, add many non-automated km.
108 openings of unknown length (35 new lines and 73 extensions,
listed in [`data/unknown_length_openings.csv`](data/unknown_length_openings.csv)) are left out.
The numbers per year are in `data/automated*_share_by_year*.csv`,
named like the charts.

### Caveats

- **2026 is a partial year,** through UrbanRail.net's last entry (2026-09-29),
  and is skewed toward lines opened outside China.
  Chinese cities rush to open lines before the year ends,
  so 25–64% of each year's new Chinese lines open in December;
  none of 2026's December openings are in yet.
  With only 10 Chinese lines so far,
  a few non-automated ones (Changchun Lines 5 and 7, Nanjing Line 6,
  and two suburban lines) pull its share down to 50%,
  against 79% in 2025.
  The GoA of Chinese lines opened since July 2026 also comes from news coverage of their openings,
  since CAMET's next per-line table (around January 2027) isn't out yet.
- **The line list is only as complete as UrbanRail.net.**
  China's lines were cross-checked against CAMET's per-year counts
  and per-line tables (2023 onward),
  which added one missing line (the Hangzhou–Haining intercity).
  Lines elsewhere were not cross-checked against a second source.
- **What counts as a new line is a judgment call** in edge cases,
  such as separately run branches (Shenzhen Line 6 Branch, Thessaloniki Line 2),
  lines that took over an existing service (Xi'an Line 14),
  and conversions of existing railways (Aarhus, Rotterdam's Hoekse Lijn), which are not counted.
  Each such call is explained in the `note` column.
- **The GoA of each automated line has a stated basis** (`GoA_basis`).
  For mainland China it is CAMET's FAO designation,
  whose tables list every FAO line opened since 2021,
  so lines missing from them are not automated,
  except lines built for FAO that CAMET designated later
  (Guangzhou Line 18, designated in 2023)
  and the Pingshan SkyShuttle, an automated people mover.
  CAMET doesn't list FAO lines for 2016–2020,
  but its FAO km totals match eight pre-2021 lines,
  six of them opened since 2016,
  including the Daxing Airport Express.
  The seven Chinese lines opened in the second half of 2026 aren't in a CAMET table yet;
  their GoA comes from news coverage of their openings.
  Every counted line has a source in `GoA_source`.
  Outside China, automated lines cite Wikipedia's
  [list of driverless train systems](https://en.wikipedia.org/wiki/List_of_driverless_train_systems)
  or, where it gives one, the source it cites, or an operator or news report.
  Lines missing from that list are tagged GoA2, citing the list;
  for those, GoA1 vs. GoA2 is unverified.
  Openings that aren't counted (extensions, trams, mainline)
  mostly keep the default GoA for their mode,
  marked "mode default; unverified".

## Sources

- [UrbanRail.net](https://www.urbanrail.net/news.htm):
  a year-by-year log of every opening worldwide,
  which flags entirely new lines.
- [CAMET](https://www.camet.org.cn/) (China Urban Rail Transit Association) reports:
  its bulletins' appendix table (附表2) lists every new line in mainland China
  and marks the FAO ones,
  and its annual reports list the new FAO lines for 2021 and 2022.
- News coverage of openings, for GoA where CAMET has nothing yet.
- [UITP Statistics Brief on metro automation](https://cms.uitp.org/wp/wp-content/uploads/2020/06/Statistics-Brief-Metro-automation_final_web03.pdf) (2019).

## Layout

- [`data/urban_rail_openings.csv`](data/urban_rail_openings.csv): the full openings list, sorted by date.
- [`data/metro_like_openings.csv`](data/metro_like_openings.csv): the openings that are new-build, fully grade-separated, and not mainline,
  the new lines the line-count charts count.
- [`data/automated_metro_like_openings.csv`](data/automated_metro_like_openings.csv): those of them that are automated above GoA2.
- `data/automated*_share_by_year*.csv`: the numbers behind the charts.
- `charts/automated*_share_by_year*.svg`: the charts,
  by line count or by km (`_km`),
  worldwide, for mainland China (`_china`), and for everywhere else (`_ex_china`),
  each for 2016–2025 (`_2016_to_2025`) and 2016–2026 (`_2016_to_2026`).
- [`data/curation/`](data/curation/): the hand-kept tables the openings list is built from:
  [`events.csv`](data/curation/events.csv) (each UrbanRail.net opening, reviewed),
  [`cities.csv`](data/curation/cities.csv) (city and country names),
  and [`lines.csv`](data/curation/lines.csv) (per-line mode, mainline, grade separation, and GoA).
- [`data/urbanrail_events.csv`](data/urbanrail_events.csv) and [`data/camet_new_lines.csv`](data/camet_new_lines.csv): parsed source data.
- [`data/camet_text/`](data/camet_text/): the text of the CAMET report pages relied on,
  such as the new-line tables and FAO sections.
- [`data/raw/urbanrail/`](data/raw/urbanrail/): the downloaded UrbanRail.net pages.
  The CAMET reports, about 30 MB, are downloaded into `data/raw/camet/` but not committed;
  [`scripts/download_camet.sh`](scripts/download_camet.sh) falls back to archived copies
  and checks them against [`data/camet_sha256sums.txt`](data/camet_sha256sums.txt).
- [`scripts/`](scripts/): download, parse, build, and chart scripts.

## Rebuilding

```sh
./scripts/download_urbanrail.sh
./scripts/download_camet.sh
uv run python scripts/parse_urbanrail.py data/urbanrail_events.csv data/raw/urbanrail/*.htm
uv run python scripts/parse_camet.py data/camet_new_lines.csv data/raw/camet/camet-*.pdf
uv run python scripts/extract_camet_text.py
uv run python scripts/build_openings.py
uv run python scripts/plot_share.py
```

Re-parsing UrbanRail.net keeps each event's ID,
so the reviews in [`data/curation/events.csv`](data/curation/events.csv) still apply;
new events need reviewing and adding there.

CI reruns every step but `download_urbanrail.sh` on each push and pull request
and fails if any output differs from what's committed.
It also downloads UrbanRail.net's current pages, at most once a day,
and warns if they have events that are new or edited since the committed ones.
It also runs `ruff`, `ty`, `pyrefly`, and `shellcheck`,
which `uv run pre-commit install` sets up to run before each commit, too.

## License

The code in [`scripts/`](scripts/) is under the [MIT License](LICENSE).
The data in [`data/`](data/) and the charts in [`charts/`](charts/)
are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The exceptions are the downloaded UrbanRail.net pages in [`data/raw/urbanrail/`](data/raw/urbanrail/)
and the CAMET report text in [`data/camet_text/`](data/camet_text/),
which belong to their original owners and are not covered by either license.
