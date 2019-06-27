import requests


class CustomAction(object):

    def __init__(self, name, config_file_dir, action_config_json, invalid_action_configuration_exception_class):
        self.name = name

        if 'realmName' not in action_config_json:
            raise invalid_action_configuration_exception_class('Configuration "{0}" missing property "realmName"'.format(name))

        self.realm_name = action_config_json['realmName']

    def execute(self, keycloak_client, action_execution_exception_class):
        get_response = keycloak_client.get('/admin/realms/{0}/users'.format(self.realm_name))
        if get_response.status_code == requests.codes.ok:
            print(get_response.text)
        else:
            raise action_execution_exception_class('Unexpected response for user get request ({0})'.format(get_response.status_code))
