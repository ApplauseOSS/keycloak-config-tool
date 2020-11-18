"""
Realm creation action.
~~~~~~~~~~~~~~~~~~~~~~~
"""

from .action import Action
from .action import InvalidActionConfigurationException
from .utils import create_realm
from .utils import if_realm_exists


class CreateRealmIfNotExistsAction(Action):

    @staticmethod
    def valid_deploy_env(deploy_env):
        """
        Returns True if the provided deployment environment is valid for this action, False otherwise
        :param deploy_env: The target deployment environment.
        :return: True always, as this action is valid for all environments.
        """

        return True

    def __init__(self, name, config_file_dir, action_config_json, *args, **kwargs):
        """
        Constructor.
        :param name: The action name.
        :param config_file_dir: The directory containing the configuration file
        :param action_config_json: The JSON configuration for this action
        """

        super(CreateRealmIfNotExistsAction, self).__init__(name, *args, **kwargs)
        self.action_config_json = action_config_json

        if 'realmName' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "realmName"'.format(name))

        self.realm_name = action_config_json['realmName']

    def execute(self, keycloak_client):
        """
        Execute this action. In this case, attempt to set a client scopes.
        :param keycloak_client: The client to use when interacting with Keycloak
        """

        if not if_realm_exists(self.realm_name, keycloak_client):
            payload = {
                "enabled": True,
                "id": self.realm_name,
                "realm": self.realm_name
            }

            print('==== Creating realm "{0}"...'.format(self.realm_name))
            create_realm(payload, keycloak_client)
        else:
            print('==== Realm "{0}" exists'.format(self.realm_name))
