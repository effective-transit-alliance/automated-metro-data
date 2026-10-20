#!/usr/bin/env bash
# Download Wikipedia's list of driverless train systems into data/raw/wikipedia/,
# or into the directory given as the first argument.
#
# It's the default source for the GoA of lines outside mainland China.
set -euo pipefail

main() {
    local root
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    local out="${1:-${root}/data/raw/wikipedia}"
    mkdir -p "${out}"
    # The rendered article, without the site's navigation around it.
    curl -fsSL -A "automated-metro-data (https://github.com/effective-transit-alliance/automated-metro-data)" \
        -o "${out}/list_of_driverless_train_systems.html" \
        "https://en.wikipedia.org/w/index.php?title=List_of_driverless_train_systems&action=render"
}

main "$@"
