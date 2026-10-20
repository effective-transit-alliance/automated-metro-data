#!/usr/bin/env bash
# Download UrbanRail.net's yearly lists of new openings since 2009 into data/raw/urbanrail/,
# or into the directory given as the first argument.
set -euo pipefail

main() {
    local root
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    local out="${1:-${root}/data/raw/urbanrail}"
    local first_year=2009
    local last_year
    last_year="$(date +%Y)"
    mkdir -p "${out}"
    local year
    for ((year = first_year; year < last_year; year++)); do
        local page="news${year}.htm"
        # 2009 and 2010 share one page.
        if ((year == 2009 || year == 2010)); then
            page="news2009-2010.htm"
        fi
        curl -fsSL -o "${out}/${page}" "https://www.urbanrail.net/${page}"
    done
    # The current year lives on the main news page.
    curl -fsSL -o "${out}/news${last_year}.htm" "https://www.urbanrail.net/news.htm"
    # For scripts/parse_urbanrail.py, to leave out openings announced for later.
    date +%F > "${out}/downloaded.txt"
}

main "$@"
