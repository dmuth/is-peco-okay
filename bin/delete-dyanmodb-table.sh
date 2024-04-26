#!/bin/bash
#
# Delete our DynanoDB table on test or dev environments.
#

# Errors are fatal
set -e

function print_syntax() {

    echo "! "
    echo "! Syntax: $0 ( test | dev )"
    echo "! "
    exit 1

} # End of print_syntax()

if test ! "$1" 
then
    print_syntax
fi

ENV=$1
TABLE="peco-outages-${ENV}"

if test "${ENV}" == "prod"
then
    echo "! Nope!  I'm not letting you delete the prod table.  Gotta do that by hand."
    exit 1
fi

echo "# Table: ${TABLE}"

echo "# Removing deletion protection..."
aws dynamodb update-table --table-name "${TABLE}" \
    --no-deletion-protection-enabled > /dev/null

echo "# Deleting table ${TABLE}..."
aws dynamodb delete-table --table-name "${TABLE}"

echo "# "
echo "# "
echo "# Table deleted!  Now when you go to do your next deploy, Serverless/CloudFormation"
echo "# WILL throw an error because it will think the DynamoDB table still exists."
echo "# "
echo "# You will need to change the name to a teporary name, run a deploy, change it back,"
echo "# and run another deploy.  If that sounds like an awful bug, that's because it is."
echo "# "
echo "# "

echo "# OK: Done!"


