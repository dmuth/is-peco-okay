
# Is PECO Okay?

Text-based low-bandwidth website for real-time information on the Philadelphia Power Grid.
View on the web at [https://www.IsPecoOkay.com/](https://www.ispecookay.com/).

## Development

### Setup

``` bash
# Install any other plugins in the `plugins:` section in `serverless.yml` as-needed.
serverless plugin install -n serverless-python-requirements

# Set up our environment
rm -rfv .venv
uv venv --python 3.10 --seed
source .venv/bin/activate
uv pip install -r requirements.txt
uv export --format requirements-txt -o requirements.txt
```

### Actual Development

``` bash
# List functions for a tsage
sls info --stage dev

# 
# Run functions locally
#
sls invoke local -f peco 
sls invoke local -f peco_recent
sls invoke local -f peco_recent --data '{ "queryStringParameters": {"num": 18}}'

# Run functions off of dev
sls invoke --stage dev -f peco_recent

# Run functions off of prod
sls invoke --stage prod -f peco_recent

# Run a webserver.  Endpoints will be printed out.  Python files will be hot-reloaded.
sls offline --reloadHandler

# Can be used to disable the script run via cron if we want to save money in testing.
bin/cron-status.sh ( test | dev | prod ) ( status | disable | enable )
```


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

## Deployment

Stages:
- `test`
- `dev`
- `prod`

``` bash

# Deploy your Serverless app to Lambda, and print out an API endpoint
sls deploy

# Deploy just a function with: 
# Note that a successful deploy can show a red checkmark (✔), which is confusing but legit.
sls deploy -f peco

# Deploy a single function to dev
sls deploy function --stage test -f peco_recent

#  Deploy to dev with 
sls deploy --stage dev

# Generates static content, deploys to S3, and invaldates CloudFront cache.
./bin/deploy-content-dev.sh
 
# Generates static content, deploys to S3, and invaldates CloudFront cache.
./bin/deploy-content-prod.sh

# Just Static Content
# Sync up just static content to an S3 bucket
sls s3sync

# Deploy to the prod bucket
sls s3sync --stage prod

# Print info on your deployment
sls info

# Query your endpoint
curl https://xxxxxxx.execute-api.us-east-1.amazonaws.com/

# Tail the log for a function.  Note that logs can take 10ish seconds to show up.
sls logs -f peco
```


## Troubleshooting

### Modules from requirements.txt aren't being loaded on AWS!

Make sure you have the following in `serverless.yml`:

```
plugins:
  - serverless-python-requirements
```

Install that plugin with:
```bash
serverless plugin install -n serverless-python-requirements
```

Also, if you're on a Mac, you may run into issues with cross-compiling.  In that case, you'll need to use a `virtualenv` while using Serverless.
  - `brew install pipx`
  - `pipx install virtualenv`
  - `./bin/activate` - Activate your VirtualEnv
  - `deactivate` - Deactivate your VirtualEnv


