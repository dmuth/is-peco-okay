
# PECO API Endpoint

## Development

### Setup

- `serverless plugin install -n serverless-python-requirements` - Installs a module which will pull Python dependencies from `requirements.txt` for deployment.
- `serverless plugin install -n serverless-offline` - Installs the offline plugin which emulates AWS Lambda and API gateway to further speed up development


### Actual Development

- `sls invoke local -f hello` - Run your function locally and print results to stdout.
- `sls offline` - Run a webserver


## Deployment

- `sls deploy` - Deploy your Serverless app to Lambda, and print out an API endpoint
- `sls info` - Print info on your deployment
- `curl https://xxxxxxx.execute-api.us-east-1.amazonaws.com/` - Query your endpoint



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
