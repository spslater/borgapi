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
    python -m pip install black pylint isort build twine
    if [ -e "requirements.txt" ]; then
        python -m pip install -r requirements.txt --upgrade
    fi
    pyenv deactivate
}

## PYTHON 3.8 ##
if test -n $(pyenv versions | grep "borglatest-3.8"); then
    pyenv uninstall "borglatest-3.8"
fi
pyenv virtualenv "3.8.16"  "borglatest-3.8"
update "borglatest-3.8"

## PYTHON 3.9 ##
if test -n $(pyenv versions | grep "borglatest-3.9"); then
    pyenv uninstall "borglatest-3.9"
fi
pyenv virtualenv "3.9.16"  "borglatest-3.9"
update "borglatest-3.9"

## PYTHON 3.10 ##
if test -n $(pyenv versions | grep "borglatest-3.10"); then
    pyenv uninstall "borglatest-3.10"
fi
pyenv virtualenv "3.10.10" "borglatest-3.10"
update "borglatest-3.10"

## PYTHON 3.11 ##
if test -n $(pyenv versions | grep "borglatest-3.11"); then
    pyenv uninstall "borglatest-3.11"
fi
pyenv virtualenv "3.11.2"  "borglatest-3.11"
update "borglatest-3.11"


