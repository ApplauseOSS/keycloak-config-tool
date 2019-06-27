# Keycloak Configuration Tool

The purpose of this tool is to allow for configuration-based updates to the Keycloak service. The tool will:

* Process the actions configuration
* Decrypt any string values encrypted with the [kms-encryption-toolbox](https://github.com/ApplauseOSS/kms-encryption-toolbox)
* Wait for Keycloak to become available
* Execute the configured actions against Keycloak

## Local Installation

This tool requires that `python3` and `pip3` be installed on your machine for a local installation. Once those tools are installed, simply run the following command to install the tool:
```
pip3 install .
```

This will create an executable named `keycloak-config-tool` in your path.

## Running tests

You need tox in order to run tests. If you don't have it, you can execute 
```
pip3 install tox
``` 

Then you can run tests just by calling
```
tox
```
from the root repository folder.

## Command-line Usage

The tool takes the following command-line flags:

| Name                  | Required? |  Default   | Description                                                                                                        | Example                                                                                                |
|:----------------------|:---------:|:----------:|:-------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------|
| `--keycloak-base-url` |    Yes    | ***NONE*** | The base URL for Keycloak.                                                                                         | `--keycloak-base-url https://keycloak.host/auth/`                                                      |
| `--keycloak-timeout`  |    No     |    180     | The timeout (in seconds) to use when waiting for keycloak to become available.                                     | `--keycloak-timeout 300`                                                                               |
| `--keycloak-username` |    Yes    | ***NONE*** | The username of an admin user on the Keycloak instance.                                                            | `--keycloak-username admin`                                                                            |
| `--keycloak-password` |    Yes    | ***NONE*** | The password for the admin user.                                                                                   | `--keycloak-password password`                                                                         |
| `--deploy-config-dir` |    Yes    | ***NONE*** | The path to the root directory. The tool will expect to find the `src` and `var` directories under this directory. | `--deploy-config-dir ./deploy`                                                                         |
| `--deploy-env`        |    Yes    | ***NONE*** | The deployment environment (use 'local' for local stacks).                                                         | `--deploy-env local`                                                                                   |
| `--config-only`       |    No     | ***NONE*** | If provided, only print out the configuration, and take no further action.                                         | `--config-only`                                                                                        |
| `--encryption-prefix` |    No     |  decrypt:  | Prefix of all encrypted values to be used to determine if any decryption is required.                              | `--encryption-prefix _DECRYPT_:`                                                                       |
| `--aws-profile`       |    No     | ***NONE*** | AWS profile to be used for contacting KMS when decryption is required.                                             | `--aws-profile saml`                                                                                   |

## Docker Usage

The tool is also available as a Docker image for use in `docker-compose` environments. The image repository is located at:

```
applause/keycloak-config-tool
```

The image takes the following environment variables:

| Name                     | Required? |  Default   | Description                                                                                                                                                                                                                                                                                      | Example                                                                                              |
|:-------------------------|:---------:|:----------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------|
| `KEYCLOAK_BASE_URL`      |    Yes    | ***NONE*** | The base URL for Keycloak.                                                                                                                                                                                                                                                                       | `KEYCLOAK_BASE_URL=https://keycloak.host/auth/`                                                      |
| `KEYCLOAK_TIMEOUT`       |    No     |    180     | The timeout (in seconds) to use when waiting for keycloak to become available.                                                                                                                                                                                                                   | `KEYCLOAK_TIMEOUT=300`                                                                               |
| `KEYCLOAK_USERNAME`      |    Yes    | ***NONE*** | The username of an admin user on the Keycloak instance.                                                                                                                                                                                                                                          | `KEYCLOAK_USERNAME=admin`                                                                            |
| `KEYCLOAK_PASSWORD`      |    Yes    | ***NONE*** | The password for the admin user.                                                                                                                                                                                                                                                                 | `KEYCLOAK_PASSWORD=password`                                                                         |
| `DEPLOY_CONFIG_DIR`      |    Yes    | ***NONE*** | The path to the root directory. The tool will expect to find the `src` and `var` directories under this directory. This directory will need to be a accessible as a mounted volume.                                                                                                              | `DEPLOY_CONFIG_DIR=/mnt/deploy`                                                                      |
| `DEPLOY_ENV`             |    Yes    | ***NONE*** | The deployment environment (use 'local' for local stacks).                                                                                                                                                                                                                                       | `DEPLOY_ENV=local`                                                                                   |
| `COMPLETION_SIGNAL_PORT` |    No     | ***NONE*** | For dockerize compatibility. A port to open up a TCP listener on when the tool completes successfully. This will allow integration test docker-compose environments to know when the tool has successfully completed. If no value is provided, the container will simply stop when it completes. | `COMPLETION_SIGNAL_PORT=3456`                                                                        |
| `ENCRYPTION_PREFIX`      |    No     |  decrypt:  | Prefix of all encrypted values to be used to determine if any decryption is required.                                                                                                                                                                                                            | `ENCRYPTION_PREFIX=_DECRYPT_:`                                                                       |
| `AWS_PROFILE`            |    No     | ***NONE*** | AWS profile to be used for contacting KMS when decryption is required.                                                                                                                                                                                                                           | `AWS_PROFILE=saml`                                                                                   |

## Configuration

The tool expects a specific configuration file structure under the directory specified by `--deploy-config-dir`:
```
.
+-- src
|   +-- keycloak.json 
+-- var
    +-- keycloak
        +-- *.var
```

The `keycloak.json` file is contains a JSON array of action configurations (covered later). The var files support a variables file for each environment (e.g., `local.var`) plus a `defaults.var` file. The order of precedence for variables is:

1. Environment variables
2. Variables located in the environment-specific variables file
3. Variables located in the `defaults.var` variables file

Variables are substituted in the `keycloak.json` file using a `#{VAR}` syntax, **NOT a `${VAR}` syntax, as Keycloak API JSON payloads already support that syntax.**

### Actions

Each action supports the following properties:

| Property Name | Required? |  Default   | Description                                                                                                                                                                                             | Example                                                        |
|:--------------|:---------:|:----------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------|
| `name`        |    Yes    | ***NONE*** | The name of the action. This name must be unique.                                                                                                                                                       | `"name": "importTestRealm"`                                    |
| `action`      |    Yes    | ***NONE*** | The type of the action (covered later).                                                                                                                                                                 | `"action": "importRealm"`                                      |
| `description` |    No     | ***NONE*** | The description for the action.                                                                                                                                                                         | `"description": "Create a test user for integration testing."` |
| `ignore`      |    No     |   false    | If `true`, then the action will be ignored. Otherwise, the action will be executed. Defaults to false. Parameterizing this property allows for certain actions to be executed for certain environments. | `"ignore": #{IGNORE_IMPORT_TEST_REALM}`                        |


### Supported Actions

The following actions are supported by the tool.

#### importRealm

Imports a realm into Keycloak via a realm file. **This action can only be run in the `local` environment**.

| Property Name | Required? |  Default   | Description                                                                                           | Example                                     |
|:--------------|:---------:|:----------:|:------------------------------------------------------------------------------------------------------|:--------------------------------------------|
| `realmFile`   |    Yes    | ***NONE*** | The file containing the realm to be imported. This file's path is relative to the configuration file. | `"realmFile": "./keycloak/test-realm.json"` |
| `overwrite`   |    No     |   false    | Whether or not to overwrite the realm if it already exists.                                           | `"overwrite": true`                         |

#### createRole

Creates a role in Keycloak.

| Property Name | Required? |  Default   | Description                                                                                                       | Example               |
|:--------------|:---------:|:----------:|:------------------------------------------------------------------------------------------------------------------|:----------------------|
| `realmName`   |    Yes    | ***NONE*** | The name of the realm.                                                                                            | `"realmName": "test"` |
| `role`        |    Yes    | ***NONE*** | [The Keycloak role representation.](http://www.keycloak.org/docs-api/3.0/rest-api/index.html#_rolerepresentation) | `"role": { ... }`     |

#### createClient

Creates a client in Keycloak. ***NOTE:*** The client secret MUST be a lower-cased UUID.

| Property Name | Required? |  Default   | Description                                                                                                           | Example                    |
|:--------------|:---------:|:----------:|:----------------------------------------------------------------------------------------------------------------------|:---------------------------|
| `realmName`   |    Yes    | ***NONE*** | The name of the realm.                                                                                                | `"realmName": "test"`      |
| `roles`       |    No     |     []     | The roles to apply to the client service account.                                                                     | `"roles": [ "test-role" ]` |
| `client`      |    Yes    | ***NONE*** | [The Keycloak client representation.](http://www.keycloak.org/docs-api/3.0/rest-api/index.html#_clientrepresentation) | `"client": { ... }`        |

#### createUser

Creates a user in Keycloak. ***NOTE:*** The `username` field is not needed. This field will be auto-populated from the `email` field.

| Property Name | Required? |  Default   | Description                                                                                                       | Example                    |
|:--------------|:---------:|:----------:|:------------------------------------------------------------------------------------------------------------------|:---------------------------|
| `realmName`   |    Yes    | ***NONE*** | The name of the realm.                                                                                            | `"realmName": "test"`      |
| `roles`       |    No     |     []     | The roles to apply to the user.                                                                                   | `"roles": [ "test-role" ]` |
| `password`    |    No     | ***NONE*** | The password to apply to the user.                                                                                | `"password": "test123"`    |
| `user`        |    Yes    | ***NONE*** | [The Keycloak user representation.](http://www.keycloak.org/docs-api/3.0/rest-api/index.html#_userrepresentation) | `"user": { ... }`          |

#### custom

Run a custom action. The custom action file must contain a class named `CustomAction`. See [test/data/deploy/src/keycloak/test_custom.py](test/data/deploy/src/keycloak/test_custom.py) for an example.

| Property Name | Required? |  Default   | Description                                                                                          | Example                                    |
|:--------------|:---------:|:----------:|:-----------------------------------------------------------------------------------------------------|:-------------------------------------------|
| `file`        |    Yes    | ***NONE*** | The file containing the custom action class. This file's path is relative to the configuration file. | `"realmFile": "./keycloak/test_custom.py"` |
