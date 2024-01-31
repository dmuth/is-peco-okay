
# PECO API Endpoint

## Development

### Setup

- `serverless plugin install -n serverless-python-requirements` - Installs a module which will pull Python dependencies from `requirements.txt` for deployment.
- `serverless plugin install -n serverless-offline` - Installs the offline plugin which emulates AWS Lambda and API gateway to further speed up development


### Actual Development

- `sls invoke local -f hello` - Run your function locally and print results to stdout.
- `sls offline --reloadHandler` - Run a webserver.  Endpoints will be printed out.  Python files will be hot-reloaded.


## Deployment

- `sls deploy` - Deploy your Serverless app to Lambda, and print out an API endpoint
  - Deploy just a function with: `sls deploy -f peco`
    - Note that a successful deploy can show a red checkmark (✔), which is confusing but legit.
- `sls info` - Print info on your deployment
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

Also, if you're on a Mac, you may run into issues with cross-compiling.  In that case, you'll need to use a `virtualenv` while using Serverless.
  - `brew install pipx`
  - `pipx install virtualenv`
  - `./bin/activate` - Activate your VirtualEnv
  - `deactivate` - Deactivate your VirtualEnv













Alternatively, it is also possible to emulate API Gateway and Lambda locally by using `serverless-offline` plugin. In order to do that, execute the following command:

```bash
serverless plugin install -n serverless-offline
```

It will add the `serverless-offline` plugin to `devDependencies` in `package.json` file as well as will add it to `plugins` in `serverless.yml`.

After installation, you can start local emulation with:

```
serverless offline
```

To learn more about the capabilities of `serverless-offline`, please refer to its [GitHub repository](https://github.com/dherault/serverless-offline).

### Bundling dependencies

In case you would like to include 3rd party dependencies, you will need to use a plugin called `serverless-python-requirements`. You can set it up by running the following command:

```bash
serverless plugin install -n serverless-python-requirements
```

Running the above will automatically add `serverless-python-requirements` to `plugins` section in your `serverless.yml` file and add it as a `devDependency` to `package.json` file. The `package.json` file will be automatically created if it doesn't exist beforehand. Now you will be able to add your dependencies to `requirements.txt` file (`Pipfile` and `pyproject.toml` is also supported but requires additional configuration) and they will be automatically injected to Lambda package during build process. For more details about the plugin's configuration, please refer to [official documentation](https://github.com/UnitedIncome/serverless-python-requirements).
