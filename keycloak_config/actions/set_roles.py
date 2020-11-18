"""
Client set action.
~~~~~~~~~~~~~~~~~~~~~~~
"""

from .action import Action
from .action import InvalidActionConfigurationException
from .utils import create_role
from .utils import delete_role
from .utils import get_roles
from .utils import if_realm_exists
from .utils import update_role


class SetRolesAction(Action):

    @staticmethod
    def valid_deploy_env(deploy_env):
        """
        Returns True if the provided deployment environment is valid for this action, False otherwise
        :param deploy_env: The target deployment environment.
        :return: True always, as this action is valid for all environments.
        """

        return True

    def __init__(self, name, config_file_dir, action_config_json, json_config_loader, *args, **kwargs):
        """
        Constructor.
        :param name: The action name.
        :param config_file_dir: The directory containing the configuration file
        :param action_config_json: The JSON configuration for this action
        """

        super(SetRolesAction, self).__init__(name, *args, **kwargs)
        self.action_config_json = action_config_json

        if 'realmName' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "realmName"'.format(name))

        if 'file' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "file"'.format(name))

        self.realm_name = action_config_json['realmName']
        self.roles = json_config_loader.load_config(action_config_json['file'])
        self.role_names = [role["name"] for role in self.roles]

    def execute(self, keycloak_client):
        """
        Execute this action. In this case, attempt to set a roles.
        :param keycloak_client: The client to use when interacting with Keycloak
        """

        if not if_realm_exists(self.realm_name, keycloak_client):
            raise Exception('Realm "{0}" not exists'.format(self.realm_name))

        current_roles = get_roles(self.realm_name, keycloak_client)
        current_roles_names = [role["name"] for role in current_roles]

        to_delete = set(current_roles_names) - set(self.role_names)
        to_create = set(self.role_names) - set(current_roles_names)
        to_update = set(self.role_names) - to_create

        for role_name in to_delete:
            curr_role = next(role for role in current_roles if role["name"] == role_name)
            print('==== Deleting role "{0}" in realm "{1}"...'.format(curr_role["name"], self.realm_name))
            delete_role(self.realm_name, curr_role["id"], keycloak_client)

        for role_name in to_create:
            role = next(role for role in self.roles if role["name"] == role_name)
            print('==== Creating role "{0}" in realm "{1}"...'.format(role["name"], self.realm_name))
            create_role(self.realm_name, role, keycloak_client)

        for role_name in to_update:
            curr_role = next(role for role in current_roles if role["name"] == role_name)
            role = next(role for role in self.roles if role["name"] == role_name)
            print('==== Updating role "{0}" in realm "{1}"...'.format(role["name"], self.realm_name))
            update_role(self.realm_name, curr_role["id"], role, keycloak_client)
