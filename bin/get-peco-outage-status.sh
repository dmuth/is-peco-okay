#!/bin/bash
#
# This script grabs data from the endpoints that PECO's Outage Map 
# located at https://www.peco.com/outages/experiencing-an-outage/outage-map
# queries.  Just a faster way of finding out how many outages we have. :-)
#

# Errors are fatal
set -e

URL_FRAGMENT=$(curl -s https://kubra.io/stormcenter/api/v1/stormcenters/39e6d9f3-fdea-4539-848f-b8631945da6f/views/789577bd-d2c6-42b8-af4b-b51ae6f52b6c/currentState | jq -r .data.interval_generation_data)

URL="https://kubra.io/${URL_FRAGMENT}/public/summary-1/data.json"

#curl -s $URL | jq .summaryFileData
curl -s $URL | jq '{ date: .summaryFileData.date_generated, outages: .summaryFileData.totals }'

