
# Is PECO Okay?

Text-based low-bandwidth website for real-time information on the Philadelphia Power Grid.
View on the web at [https://www.IsPecoOkay.com/](https://www.ispecookay.com/).

## Development

### Setup

- `serverless plugin install -n serverless-python-requirements` - Installs a module which will pull Python dependencies from `requirements.txt` for deployment.
- Install any other plugins in the `plugins:` section in `serverless.yml` as-needed.


### Actual Development

- `sls invoke local -f peco` - Run your function locally and print results to stdout.
- `sls invoke local -f peco_recent` - Run your function locally and print results to stdout.
- `sls invoke local -f peco_recent --data '{ "queryStringParameters": {"num": 18}}'`
  - Run the function locally with some query params (e.g. `/peco/recent?num=18`)
- `sls offline --reloadHandler` - Run a webserver.  Endpoints will be printed out.  Python files will be hot-reloaded.
- `bin/cron-status.sh ( test | dev | prod ) ( status | disable | enable )` 
  - Can be used to disable the script run via cron if we want to save money in testing.


### Working with Web Content

The HTML, Javascript, and CSS is static, and we use [Hugo](https://gohugo.io/) for template processing.
To launch Hugo for local testing on [http://localhost:1313/](http://localhost:1313/):

- Dev config and endpoints:
  - `./bin/hugo-server.sh dev`
- Prod config and endpoints:
  - `./bin/hugo-server.sh prod`
- To build the website in `hugo/public/`
  - `cd hugo`
  - `hugo --cleanDestinationDir --config hugo-prod.toml`


## Deployment

- Code
  - `sls deploy` - Deploy your Serverless app to Lambda, and print out an API endpoint
    - Deploy just a function with: `sls deploy -f peco`
      - Note that a successful deploy can show a red checkmark (✔), which is confusing but legit.
    - Deploy to prod with `sls deploy --stage prod`.
- Content
  - `./bin/deploy-content-dev.sh` - Generates static content, deploys to S3, and invaldates CloudFront cache.
  - `./bin/deploy-content-prod.sh` - Generates static content, deploys to S3, and invaldates CloudFront cache.
  - Just Static Content
    - `sls s3sync` - Sync up just static content to an S3 bucket
    - `sls s3sync --stage prod` - Deploy to the prod bucket
- Info
  - `sls info` - Print info on your deployment
- Testing
  - `curl https://xxxxxxx.execute-api.us-east-1.amazonaws.com/` - Query your endpoint
- Debugging
  - `sls logs -f peco` - Tail the log for a function.  Note that logs can take 10ish seconds to show up.


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


