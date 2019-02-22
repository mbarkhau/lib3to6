#!/bin/bash

AUTHOR_NAME="Manuel Barkhau"
AUTHOR_EMAIL="mbarkhau@gmail.com"

KEYWORDS="six lib2to3 astor ast"
DESCRIPTION="Compile Python 3.7 code to Python 2.7+"

LICENSE_ID="MIT"

PACKAGE_NAME="lib3to6"
MODULE_NAME="lib3to6"
GIT_REPO_NAMESPACE="mbarkhau"
GIT_REPO_DOMAIN="gitlab.com"

PACKAGE_VERSION="v201902.0030"

DEFAULT_PYTHON_VERSION="python=3.7"
# Note: python2.7 is not supported, but we need the interpreter
#   to be installed so we can test compatibility.
SUPPORTED_PYTHON_VERSIONS="python=3.7 python=2.7 pypy3.5"

IS_PUBLIC=1


## Download and run the actual update script

if [[ $KEYWORDS == "keywords used on pypi" ]]; then
    echo "FAILSAFE! Default bootstrapit config detected.";
    echo "Did you forget to update parameters in your 'bootstrapit.sh' ?"
    exit 1;
fi

PROJECT_DIR=$(dirname "$0");

if ! [[ -f "$PROJECT_DIR/scripts/bootstrapit_update.sh" ]]; then
    mkdir -p "$PROJECT_DIR/scripts/";
    RAW_FILES_URL="https://gitlab.com/mbarkhau/bootstrapit/raw/master";
    curl --silent "$RAW_FILES_URL/scripts/bootstrapit_update.sh" \
        > "$PROJECT_DIR/scripts/bootstrapit_update.sh.tmp";
    mv "$PROJECT_DIR/scripts/bootstrapit_update.sh.tmp" \
        "$PROJECT_DIR/scripts/bootstrapit_update.sh";
fi

source "$PROJECT_DIR/scripts/bootstrapit_update.sh";
