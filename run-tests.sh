#!/usr/bin/env bash

versions=(
    "borglatest-3.9"
    "borglatest-3.10"
    "borglatest-3.11"
    "borglatest-3.12"
    "borglatest-3.13"
)

eval "$(pyenv init -)" >/dev/null 2>&1
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

echo "Automate tests for supported Python versions" > "results.log"

for version in "${versions[@]}"; do
    pyenv activate $version
    pip install -r requirements.txt 1>&2 2>/dev/null
    printf "$version: " 2>&1 | tee -a "results.log"
    if test "$1" = "-v"; then
        python -m unittest discover -v 2>&1 | tee -a "results.log"
    else
        python -m unittest discover 2>&1 | tee -a "results.log"
    fi
    pyenv deactivate
done
