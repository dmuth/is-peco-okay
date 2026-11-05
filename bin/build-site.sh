#!/bin/bash
#
# Build the static website with Hugo.
#

set -e

if test "$#" -ne 1 || { test "$1" != "test" && test "$1" != "dev" && test "$1" != "prod"; }
then
    echo "Usage: $0 ( test | dev | prod )" >&2
    exit 1
fi

ENV="$1"
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

pushd "$SCRIPT_DIR/../hugo" > /dev/null
hugo --cleanDestinationDir --config "hugo-${ENV}.toml"
popd > /dev/null
