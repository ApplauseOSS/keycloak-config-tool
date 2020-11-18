"""
Role creation action.
~~~~~~~~~~~~~~~~~~~~~~~
"""

from ..build_in_client_scopes import built_in_client_scopes
from .action import Action
from .action import InvalidActionConfigurationException
from .utils import create_client_scope
from .utils import delete_client_scope
from .utils import delete_default_client_scope
from .utils import delete_optional_client_scope
from .utils import delete_realm_scope_mapping
from .utils import get_client_scopes
from .utils import get_clients
from .utils import get_realm_scope_mapping
from .utils import if_realm_exists
from .utils import update_client_scope


class SetClientScopesAction(Action):

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

        super(SetClientScopesAction, self).__init__(name, *args, **kwargs)
        self.action_config_json = action_config_json

        if 'realmName' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "realmName"'.format(name))

        if 'file' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "file"'.format(name))

        self.realm_name = action_config_json['realmName']
        self.client_scopes = json_config_loader.load_config(action_config_json['file'])
        self.client_scopes_names = [scope["name"] for scope in self.client_scopes]

    def execute(self, keycloak_client):
        """
        Execute this action. In this case, attempt to set a client scopes.
        :param keycloak_client: The client to use when interacting with Keycloak
        """

        if not if_realm_exists(self.realm_name, keycloak_client):
            raise Exception('Realm "{0}" not exists'.format(self.realm_name))

        current_client_scopes = [client_scope for client_scope in get_client_scopes(self.realm_name, keycloak_client)
                                 if client_scope["name"] not in built_in_client_scopes]
        current_client_scopes_names = [client_scope["name"] for client_scope in current_client_scopes]

        to_remove = set(current_client_scopes_names) - set(self.client_scopes_names)
        to_create = set(self.client_scopes_names) - set(current_client_scopes_names)
        to_update = set(self.client_scopes_names) - to_create

        for scope_name in to_remove:
            client_scope = next(scope for scope in current_client_scopes if scope["name"] == scope_name)

            clients = get_clients(self.realm_name, keycloak_client)
            clients_with_default_client_scope = [client for client in clients if scope_name in client["defaultClientScopes"]]
            clients_with_optional_client_scope = [client for client in clients if scope_name in client["optionalClientScopes"]]

            for client in clients_with_default_client_scope:
                print('==== Deleting default client scope "{0}" for client "{1}" in realm "{2}"...'.format(client_scope["name"],
                                                                                                           client["clientId"],
                                                                                                           self.realm_name))
                delete_default_client_scope(self.realm_name, client["id"], client_scope["id"], keycloak_client)

            for client in clients_with_optional_client_scope:
                print('==== Deleting optional client scope "{0}" for client "{1}" in realm "{2}"...'.format(client_scope["name"],
                                                                                                            client["clientId"],
                                                                                                            self.realm_name))
                delete_optional_client_scope(self.realm_name, client["id"], client_scope["id"], keycloak_client)

            roles_with_scope = get_realm_scope_mapping(self.realm_name, client_scope["id"], keycloak_client)
            if len(roles_with_scope) > 0:
                print('==== Deleting client scope "{0}" assignment for roles "[{1}]" in realm "{2}"...'
                      .format(client_scope["name"], ','.join(map(lambda role: role["name"], roles_with_scope)), self.realm_name))
                delete_realm_scope_mapping(self.realm_name, client_scope["id"], roles_with_scope, keycloak_client)

            print('==== Deleting client scope "{0}" in realm "{1}"...'.format(client_scope["name"], self.realm_name))
            delete_client_scope(self.realm_name, client_scope["id"], keycloak_client)

        for scope_name in to_create:
            client_scope = next(scope for scope in self.client_scopes if scope["name"] == scope_name)
            print('==== Creating client scope "{0}" in realm "{1}"...'.format(client_scope["name"], self.realm_name))
            payload = {
                "protocol": "openid-connect",
                "attributes": {
                    "include.in.token.scope": "true",
                    "display.on.consent.screen": "true",
                }
            }
            payload.update(client_scope)
            create_client_scope(self.realm_name, payload, keycloak_client)

        for scope_name in to_update:
            scope_id = next(scope["id"] for scope in current_client_scopes if scope["name"] == scope_name)
            client_scope = next(scope for scope in self.client_scopes if scope["name"] == scope_name)
            print('==== Updating client scope "{0}" in realm "{1}"...'.format(client_scope["name"], self.realm_name))
            update_client_scope(self.realm_name, scope_id, client_scope, keycloak_client)
