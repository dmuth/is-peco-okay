#!/bin/bash
#
# A little wrapper to run Hugo in Server mode.
#

# Errors are fatal
set -e


function print_syntax() {
    echo "! "
    echo "! Syntax: $0 ( test | dev | prod )"
    echo "! "
    exit 1
} # End of print_syntax()


ENV=""
if test ! "$1"
then
    print_syntax

elif test "$1" == "-h" -o "$1" == "--help"
then
    print_syntax

elif test "$1" == "test"
then
    ENV=$1

elif test "$1" == "dev"
then
    ENV=$1

elif test "$1" == "prod"
then
    ENV=$1

else
    print_syntax

fi

# Change to our Hugo directory
pushd $(dirname $0)/../hugo > /dev/null

hugo server --cleanDestinationDir --config hugo-${ENV}.toml

