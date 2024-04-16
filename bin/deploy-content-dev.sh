#!/bin/bash
#
# Wrapper to deploy dev content.
#

# Errors are fatal
set -e

pushd $(dirname $0) > /dev/null

./deploy-content.sh dev

