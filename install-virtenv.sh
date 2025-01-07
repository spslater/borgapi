#!/usr/bin/env bash

if ! command -v pyenv &> /dev/null; then
    echo "pyenv not installed" && exit 1
fi

eval "$(pyenv init -)" >/dev/null 2>&1
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

function update() {
    pyenv activate "$1"
    python -m pip install --upgrade pip
    python -m pip install ruff~=0.9.1
    if [ -e "requirements.txt" ]; then
        python -m pip install -r requirements.txt --upgrade
    fi
    pyenv deactivate
}

## PYTHON 3.9 ##
if test -n $(pyenv versions | grep "borglatest-3.9"); then
    pyenv uninstall "borglatest-3.9"
fi
pyenv virtualenv "3.9.21"  "borglatest-3.9"
update "borglatest-3.9"

## PYTHON 3.10 ##
if test -n $(pyenv versions | grep "borglatest-3.10"); then
    pyenv uninstall "borglatest-3.10"
fi
pyenv virtualenv "3.10.16" "borglatest-3.10"
update "borglatest-3.10"

## PYTHON 3.11 ##
if test -n $(pyenv versions | grep "borglatest-3.11"); then
    pyenv uninstall "borglatest-3.11"
fi
pyenv virtualenv "3.11.2"  "borglatest-3.11"
update "borglatest-3.11"

## PYTHON 3.12 ##
if test -n $(pyenv versions | grep "borglatest-3.12"); then
    pyenv uninstall "borglatest-3.12"
fi
pyenv virtualenv "3.12.8"  "borglatest-3.12"
update "borglatest-3.12"

## PYTHON 3.13 ##
if test -n $(pyenv versions | grep "borglatest-3.13"); then
    pyenv uninstall "borglatest-3.13"
fi
pyenv virtualenv "3.13.1"  "borglatest-3.13"
update "borglatest-3.13"
