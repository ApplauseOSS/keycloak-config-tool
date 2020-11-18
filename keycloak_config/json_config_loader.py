"""
Deployment Configuration.
~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
import re


class InvalidConfigurationException(Exception):
    pass


class JsonConfigLoader(object):

    def __init__(self, deploy_src_dir, deploy_var_dir, deploy_env, json_loader):
        """
        Constructor.
        :param deploy_config_dir: The base directory for the deployment configuration.
        :param deploy_env: The target deployment environment.
        :param json_loader: An object able to load JSON contents into a Python object.
        """

        self.json_loader = json_loader
        self.deploy_env = deploy_env
        self.deploy_src_dir = deploy_src_dir
        self.deploy_var_dir = deploy_var_dir
        self.deploy_keycloak_var_dir = os.path.join(self.deploy_var_dir, 'keycloak')

        self.variables = self.load_variables()

    def load_variables(self):
        """
        Load the default and environment-specific variable files.
        :return: A dictionary containing all loaded variables.
        """

        default_variables_file = os.path.join(self.deploy_keycloak_var_dir, 'defaults.var')
        default_variables = self.load_variables_file(default_variables_file)

        deploy_env_variables_file = os.path.join(self.deploy_keycloak_var_dir, '{0}.var'.format(self.deploy_env))
        deploy_env_variables = self.load_variables_file(deploy_env_variables_file)

        default_variables.update(deploy_env_variables)
        return default_variables

    @staticmethod
    def load_variables_file(path):
        """
        Load the variable file located at the supplied path.
        :param path: The path of the variable file
        :return: A dictionary containing all loaded variables.
        """

        variables = {}

        if os.path.isfile(path):
            with open(path, 'r') as f:
                for line in f:
                    stripped_line = re.sub(r'#.*$', '', line).strip()

                    if len(line) > 0:
                        tokens = stripped_line.split('=', maxsplit=2)
                        if len(tokens) < 2:
                            raise InvalidConfigurationException('Invalid variable assignment: "{0}"'.format(line))

                        variables[tokens[0].strip()] = tokens[1].strip()

        return variables

    def load_config(self, path):
        config_path = os.path.join(self.deploy_src_dir, path)

        if not os.path.isfile(config_path):
            raise InvalidConfigurationException('File not found: {0}'.format(config_path))

        with open(config_path, 'r') as f:
            raw_config = f.read()

        processed_config = self.process_config_variables(raw_config)
        return self.json_loader.load_json(processed_config)

    def process_config_variables(self, raw_config):
        """
        Process the variables contained in the configuration.
        :return: The processed configuration.
        """

        def replacement(matchobj):
            variable = matchobj.group(1).strip()
            if len(variable) == 0:
                raise InvalidConfigurationException('Empty variable declaration in configuration')
            if variable in os.environ:
                return os.environ[variable]
            if variable in self.variables:
                return self.variables[variable]
            raise InvalidConfigurationException('Unknown variable: {0}'.format(variable))

        return re.sub(r'#\{([^}]+)}', replacement, raw_config)
