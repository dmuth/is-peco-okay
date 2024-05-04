#!/bin/bash
#
# Deploy content to both dev and prod.  Only use this for minor updates.
#

# Errors are fatal
set -e

# Change to the directory of this script
pushd $(dirname $0)


./deploy-content-dev.sh

./deploy-content-prod.sh


