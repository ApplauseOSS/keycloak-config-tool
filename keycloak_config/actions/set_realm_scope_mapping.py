"""
Client set action.
~~~~~~~~~~~~~~~~~~~~~~~
"""

from ..build_in_client_scopes import built_in_client_scopes
from .action import Action
from .action import InvalidActionConfigurationException
from .utils import add_realm_scope_mapping
from .utils import delete_realm_scope_mapping
from .utils import get_client_scopes
from .utils import get_realm_scope_mapping
from .utils import get_roles
from .utils import if_realm_exists


class SetRealmScopeMappingAction(Action):

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

        super(SetRealmScopeMappingAction, self).__init__(name, *args, **kwargs)
        self.action_config_json = action_config_json

        if 'realmName' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "realmName"'.format(name))

        if 'file' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "file"'.format(name))

        self.realm_name = action_config_json['realmName']
        self.mappings = json_config_loader.load_config(action_config_json['file'])

    def execute(self, keycloak_client):
        """
        Execute this action. In this case, attempt to set a roles.
        :param keycloak_client: The client to use when interacting with Keycloak
        """

        if not if_realm_exists(self.realm_name, keycloak_client):
            raise Exception('Realm "{0}" not exists'.format(self.realm_name))

        client_scopes = [client_scope for client_scope in get_client_scopes(self.realm_name, keycloak_client)
                         if client_scope["name"] not in built_in_client_scopes]
        roles = get_roles(self.realm_name, keycloak_client)

        for client_scope in client_scopes:
            mapping = next((mapping for mapping in self.mappings if mapping["clientScope"] == client_scope["name"]), None)

            mapped_roles_names = mapping["roles"] if mapping is not None else []
            mapped_roles = [role for role in roles if role["name"] in mapped_roles_names]
            self.set_mapping(client_scope, mapped_roles, keycloak_client)

    def set_mapping(self, client_scope, mapped_roles, keycloak_client):
        curr_mapped_roles = get_realm_scope_mapping(self.realm_name, client_scope["id"], keycloak_client)

        curr_mapped_roles_names = [role["name"] for role in curr_mapped_roles]
        mapped_roles_names = [role["name"] for role in mapped_roles]

        to_remove = set(curr_mapped_roles_names) - set(mapped_roles_names)
        to_add = set(mapped_roles_names) - set(curr_mapped_roles_names)

        if len(to_remove) > 0:
            roles = [role for role in curr_mapped_roles if role["name"] in to_remove]
            print('==== Deleting client scope "{0}" assignment for roles "[{1}]" in realm "{2}"...'
                  .format(client_scope["name"], ', '.join(map(lambda role: role["name"], roles)), self.realm_name))
            delete_realm_scope_mapping(self.realm_name, client_scope["id"], roles, keycloak_client)

        if len(to_add) > 0:
            roles = [role for role in mapped_roles if role["name"] in to_add]
            print('==== Adding client scope "{0}" assignment for roles "[{1}]" in realm "{2}"...'
                  .format(client_scope["name"], ', '.join(map(lambda role: role["name"], roles)), self.realm_name))
            add_realm_scope_mapping(self.realm_name, client_scope["id"], roles, keycloak_client)
