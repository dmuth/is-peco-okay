
# Is PECO Okay?

Text-based low-bandwidth website for real-time information on the Philadelphia Power Grid.
View on the web at [https://www.IsPecoOkay.com/](https://www.ispecookay.com/).

## Development

### Setup

``` bash
# Set up the Python environment from pyproject.toml and uv.lock.
uv sync
```

### Actual Development

``` bash
# Optional: choose where the SQLite database is stored. Defaults to
# ./peco-outages.sqlite3.
export SQLITE_DATABASE_PATH="$HOME/.local/share/peco-outages.sqlite3"

# Run the FastAPI application locally. API endpoints are available at
# http://127.0.0.1:8000/peco and http://127.0.0.1:8000/peco/recent.
uv run uvicorn api.main:app --reload

# Fetch the latest data and store it in SQLite.
while true
do
    uv run python -m api.cron
    sleep 60
done

# Delete expired records from SQLite.
uv run python -m api.purge

# Test endpoints
curl localhost:8000/peco/
curl localhost:8000/peco/recent
```

The SQLite database stores each record's UTC collection time in a `timestamp`
column and assigns an auto-incrementing `id`. Main status records are removed
after seven days by the purge command; raw archive records are retained.

Schedule the collector and cleanup commands with the host's scheduler.

### Working with Web Content

The HTML, Javascript, and CSS is static, and we use [Hugo](https://gohugo.io/) for template processing.
To launch Hugo for local testing on [http://localhost:1313/](http://localhost:1313/):

``` bash
# Dev config and endpoints:
./bin/hugo-server.sh dev

# Prod config and endpoints:
./bin/hugo-server.sh prod

# To build the website in hugo/public/
cd hugo
hugo --cleanDestinationDir --config hugo-prod.toml
```

## Static Site Deployment

``` bash
# Build the site and sync it to S3, then invalidate the CloudFront cache.
./bin/deploy-content-dev.sh
./bin/deploy-content-prod.sh
```
