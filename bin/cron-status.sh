#!/bin/bash
#
# Check, disable, or enable the schedule for our cron functions.
# This can be used to turn off the function in our test or dev deployments if we want.
#

# Errors are fatal
set -e

function print_syntax() {

    echo "! "
    echo "! Syntax: $0 ( test | dev | prod ) ( status | disable | enable )"
    echo "! "
    exit 1

} # End of print_syntax()

if test ! "$2" 
then
    print_syntax
fi

ENV=$1
CMD=$2
FUNCTION="peco-api-${ENV}-cron"

echo "# Function: ${FUNCTION}"
echo "# Operation: ${CMD}"

echo "# Looking up ARN..."
ARN=$(aws lambda list-functions --query "Functions[?FunctionName=='${FUNCTION}'].FunctionArn" --output text)
if test ! "${ARN}"
then
    echo "! Could not find ARN for function ${FUNCTION}!"
    exit 1
fi

echo "# ARN is ${ARN}!"

echo "# Looking up rule..."
RULE=$(aws events list-rule-names-by-target --target-arn "${ARN}" --output text | awk '{ print $2 }')
if test ! "${RULE}"
then
    echo "! Could not find rule for ARN ${ARN}!"
    exit 1
fi

echo "# Rule name is: ${RULE}"

if test "${CMD}" == "status"
then
    SCHEDULE=$(aws events describe-rule --name "${RULE}" --output json | jq -r '.ScheduleExpression')
    STATE=$(aws events describe-rule --name "${RULE}" --output json | jq -r .State)
    echo "# Schedule: ${SCHEDULE}, State: ${STATE}"

elif test "${CMD}" == "disable"
then
    echo "# Disabling rule ${RULE}..."
    aws events disable-rule --name "${RULE}"
    echo "# Done!"

elif test "${CMD}" == "enable"
then
    echo "# Enabling rule ${RULE}..."
    aws events enable-rule --name "${RULE}"
    echo "# Done!"

else
    echo "! Unknown command: ${CMD}"

fi

echo "# OK: Done!"

