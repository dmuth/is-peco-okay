#!/bin/bash
#
# Our main deployment script
#

# Errors are fatal
set -e

# Are we working on dev or prod?
ENV=""

#
# Print our syntax and exit.
#
function print_syntax() {

    echo "! "
    echo "! Syntax: $0 ( dev | prod )"
    echo "! "
    exit 1

} # End of print_syntax()


#
# Parse our args.
#
function parse_args() {

    if test ! "$1"
    then
        print_syntax

    elif test "$1" == "-h" -o "$1" == "--help"
    then
        print_syntax

    elif test "$1" == "dev"
    then
        ENV="dev"

    elif test "$1" == "prod"
    then
        ENV="prod"

    else
        print_syntax

    fi

} # End of parse_args()


function build_html() {
    echo "# Building HTML..."
    pushd hugo > /dev/null
    hugo --cleanDestinationDir --config hugo-${ENV}.toml 
    popd > /dev/null
} # End of build_html()


function s3sync() {
    echo "# Syncing up to S3 bucket..."
    sls s3sync --stage ${ENV}
} # End of s3sync()


function invalidate_cloudfront_cache() {

    echo "# Invalidating Cloudfront Cache..."

    if test "${ENV}" == "dev"
    then
        HOSTNAME="dev.ispecookay.com"

    elif test "${ENV}" == "prod"
    then
        HOSTNAME="www.ispecookay.com"

    fi

    ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Aliases.Items[?contains(@, '${HOSTNAME}')]]" \
        | jq -r .[].Id)

    if test ! "${ID}"
    then
        echo "! No CloudFront distribution ID found, something has gone wrong.  Aborting!"
        exit 1
    fi

    echo "# Found Cloudfront distribution ID: ${ID}"

    echo "# Invalidating cache... "
    aws cloudfront create-invalidation --distribution-id E2DQ0IJFCF2BWB --paths "/*"

    echo "# Getting current invalidations..."
    echo
    ./bin/get-cloudfront-cache-invalidations.sh ${ID}
    echo

    echo "# "
    echo "# To keep track of invalidation status so you know when complete, run this command:"
    echo "# ./bin/get-cloudfront-cache-invalidations.sh ${ID}"
    echo "# "

} # End of invalidate_cloudfront_cache()


parse_args $@

# Change to the parent directory of this script
pushd $(dirname $0)/.. > /dev/null

echo "# Deploying to environment: ${ENV}..."

build_html
s3sync
invalidate_cloudfront_cache

echo "# Done!"

