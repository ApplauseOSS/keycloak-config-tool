"""
Client set action.
~~~~~~~~~~~~~~~~~~~~~~~
"""

from .action import Action
from .action import InvalidActionConfigurationException
from .utils import add_default_client_scope
from .utils import add_optional_client_scope
from .utils import create_client
from .utils import delete_default_client_scope
from .utils import delete_optional_client_scope
from .utils import find_client
from .utils import get_client_scopes
from .utils import get_clients
from .utils import if_realm_exists
from .utils import update_client


class SetClientsAction(Action):

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

        super(SetClientsAction, self).__init__(name, *args, **kwargs)
        self.action_config_json = action_config_json

        if 'realmName' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "realmName"'.format(name))

        if 'file' not in action_config_json:
            raise InvalidActionConfigurationException('Configuration "{0}" missing property "file"'.format(name))

        self.realm_name = action_config_json['realmName']
        self.clients = json_config_loader.load_config(action_config_json['file'])
        self.clients_client_ids = [scope["clientId"] for scope in self.clients]

    def execute(self, keycloak_client):
        """
        Execute this action. In this case, attempt to set a clients.
        :param keycloak_client: The client to use when interacting with Keycloak
        """

        if not if_realm_exists(self.realm_name, keycloak_client):
            raise Exception('Realm "{0}" not exists'.format(self.realm_name))

        current_clients = get_clients(self.realm_name, keycloak_client)
        current_clients_client_ids = [client["clientId"] for client in current_clients]

        to_create = set(self.clients_client_ids) - set(current_clients_client_ids)
        to_update = set(self.clients_client_ids) - to_create

        for client_id in to_create:
            client = next(client for client in self.clients if client["clientId"] == client_id)
            print('==== Creating client "{0}" in realm "{1}"...'.format(client["clientId"], self.realm_name))
            client_payload = {
                "clientId": client["clientId"],
                "enabled": client["enabled"] if "enabled" in client else True,
                "protocol": client["protocol"] if "protocol" in client else "openid-connect",
                "attributes": client["attributes"] if "attributes" in client else {},
                "redirectUris": client["redirectUris"] if "redirectUris" in client else [],
            }
            created_client_id = create_client(self.realm_name, client_payload, keycloak_client)
            curr_client = find_client(self.realm_name, created_client_id, keycloak_client)
            self.update_client(curr_client, client, keycloak_client)

        for client_id in to_update:
            curr_client = next(client for client in current_clients if client["clientId"] == client_id)
            client = next(client for client in self.clients if client["clientId"] == client_id)
            print('==== Updating client "{0}" in realm "{1}"...'.format(client["clientId"], self.realm_name))
            self.update_client(curr_client, client, keycloak_client)

    def update_client(self, curr_client, client, keycloak_client):
        update_client(self.realm_name, curr_client["id"], client, keycloak_client)
        self.update_default_and_optional_client_scopes(curr_client, client, keycloak_client)

    def update_default_and_optional_client_scopes(self, curr_client, client, keycloak_client):
        client_scopes = get_client_scopes(self.realm_name, keycloak_client)
        default_client_scopes = client["defaultClientScopes"] if "defaultClientScopes" in client else []
        optional_client_scopes = client["optionalClientScopes"] if "optionalClientScopes" in client else []

        to_remove = {
            "defaultClientScopes": set(curr_client["defaultClientScopes"]) - set(default_client_scopes),
            "optionalClientScopes": set(curr_client["optionalClientScopes"]) - set(optional_client_scopes)
        }
        to_create = {
            "defaultClientScopes": set(default_client_scopes) - set(curr_client["defaultClientScopes"]),
            "optionalClientScopes": set(optional_client_scopes) - set(curr_client["optionalClientScopes"])
        }

        for client_scope_name in to_remove["defaultClientScopes"]:
            print('==== Deleting default client scope "{0}" from client "{1}" in realm "{2}"...'.format(client_scope_name,
                                                                                                        curr_client["clientId"],
                                                                                                        self.realm_name))
            client_scope = self.find_client_scope_by_name(client_scopes, client_scope_name)
            delete_default_client_scope(self.realm_name, curr_client["id"], client_scope["id"], keycloak_client)

        for client_scope_name in to_remove["optionalClientScopes"]:
            print('==== Deleting optional client scope "{0}" from client "{1}" in realm "{2}"...'.format(client_scope_name,
                                                                                                         curr_client["clientId"],
                                                                                                         self.realm_name))
            client_scope = self.find_client_scope_by_name(client_scopes, client_scope_name)
            delete_optional_client_scope(self.realm_name, curr_client["id"], client_scope["id"], keycloak_client)

        for client_scope_name in to_create["defaultClientScopes"]:
            print('==== Adding default client scope "{0}" from client "{1}" in realm "{2}"...'.format(client_scope_name,
                                                                                                      curr_client["clientId"],
                                                                                                      self.realm_name))
            client_scope = self.find_client_scope_by_name(client_scopes, client_scope_name)
            add_default_client_scope(self.realm_name, curr_client["id"], client_scope["id"], keycloak_client)

        for client_scope_name in to_create["optionalClientScopes"]:
            print('==== Adding optional client scope "{0}" from client "{1}" in realm "{2}"...'.format(client_scope_name,
                                                                                                       curr_client["clientId"],
                                                                                                       self.realm_name))
            client_scope = self.find_client_scope_by_name(client_scopes, client_scope_name)
            add_optional_client_scope(self.realm_name, curr_client["id"], client_scope["id"], keycloak_client)

    @staticmethod
    def find_client_scope_by_name(client_scopes, client_scope_name):
        client_scope = next((client_scope for client_scope in client_scopes if client_scope["name"] == client_scope_name), None)
        if client_scope is None:
            raise Exception('Client scope "{0} not exists'.format(client_scope_name))

        return client_scope
