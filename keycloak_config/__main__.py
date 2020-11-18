"""
Keycloak Configuration Tool.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from .actions_engine import ActionsEngine
from .encryption import EncryptionHelper
from .json import JsonLoader
from .json_config_loader import JsonConfigLoader
from .keycloak_client import KeycloakClient

import click
import os
import sys

# `prog` & `version` will be auto detected by clicked based on setup.py
VERSION_MESSAGE = '%(prog)s version %(version)s Applause AQI Inc. 2017. All rights reserved.'


@click.command()
@click.option(
    '--keycloak-base-url',
    type=click.STRING,
    required=True,
    help='The base URL for the Keycloak service'
)
@click.option(
    '--keycloak-timeout',
    type=click.INT,
    default=180,
    help='The timeout to use while waiting for Keycloak to become available'
)
@click.option(
    '--keycloak-username',
    type=click.STRING,
    required=True,
    help='The Keycloak administrator username'
)
@click.option(
    '--keycloak-password',
    type=click.STRING,
    required=True,
    help='The Keycloak administrator password'
)
@click.option(
    '--deploy-config-dir',
    type=click.Path(exists=True),
    required=True,
    help='The path to the deployment configuration directory'
)
@click.option(
    '--deploy-env',
    type=click.STRING,
    required=True,
    help='The target deployment environment'
)
@click.option(
    '--config-only',
    is_flag=True,
    help='If supplied, the configuration is displayed, and no action is taken'
)
@click.option(
    '--encryption-prefix',
    type=click.STRING,
    help='Prefix of all encrypted values to be used to determine if any decryption is required'
)
@click.option(
    '--aws-profile',
    type=click.STRING,
    help='AWS profile to be used for contacting KMS when decryption is required'
)
def main(
        keycloak_base_url,
        keycloak_timeout,
        keycloak_username,
        keycloak_password,
        deploy_config_dir,
        deploy_env,
        config_only,
        encryption_prefix,
        aws_profile
):
    # 'Unbuffer' stdout
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    deploy_src_dir = os.path.join(deploy_config_dir, 'src')
    deploy_var_dir = os.path.join(deploy_config_dir, 'var')

    encryption_helper = EncryptionHelper(encryption_prefix, aws_profile)
    json_loader = JsonLoader(encryption_helper)
    json_config_loader = JsonConfigLoader(deploy_src_dir, deploy_var_dir, deploy_env, json_loader)
    actions_config = json_config_loader.load_config('keycloak.json')

    if config_only:
        print(actions_config)
        return

    actions_engine = ActionsEngine(deploy_env, deploy_src_dir, actions_config, json_config_loader)

    if actions_engine.is_empty():
        print("==== There are no actions to execute.")
    else:
        client = KeycloakClient(keycloak_base_url)
        if client.wait_for_availability(keycloak_timeout) and \
                client.initialize_session(keycloak_username, keycloak_password):
            actions_engine.execute(client)
