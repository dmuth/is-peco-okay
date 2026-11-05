#!/bin/bash
#
# Build the static website with Hugo.
#

set -e

if test "$#" -ne 0
then
    echo "Usage: $0" >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

pushd "$SCRIPT_DIR/../hugo" > /dev/null
hugo --cleanDestinationDir
popd > /dev/null
