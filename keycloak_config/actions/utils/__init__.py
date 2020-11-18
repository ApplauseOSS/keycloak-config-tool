"""
User utilities.
~~~~~~~~~~~~~~~
"""
import re
import requests

# Roles that should not be processed.
RESERVED_ROLES = ['offline_access', 'uma_authorization']


class InvalidUserResponse(Exception):
    pass


class InvalidRoleResponse(Exception):
    pass


class InvalidResponse(Exception):
    pass


def get_role_by_name(realm_name, role_name, keycloak_client):
    """
    Gets a role representation.
    :param realm_name: The realm of the role
    :param role_name: the role name
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The role representation
    """

    path = '/admin/realms/{0}/roles/{1}'.format(realm_name, role_name)
    get_response = keycloak_client.get(path)

    if get_response.status_code == requests.codes.ok:
        return get_response.json()

    if get_response.status_code == requests.codes.not_found:
        return None

    raise InvalidRoleResponse('Unexpected role get response ({0})'.format(get_response.status_code))


def role_names_to_roles(realm_name, role_names, keycloak_client):
    """
    Convert a list of role names into role representations.
    :param realm_name: The realm of the roles
    :param role_names: The name of the roles
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The role representations
    """

    roles = []
    for role_name in role_names:
        role = get_role_by_name(realm_name, role_name, keycloak_client)
        if not role:
            raise InvalidRoleResponse('Unknown role: {0}'.format(role_name))
        roles.append(role)
    return roles


def get_user(realm_name, user_id, keycloak_client):
    """
    Get a user representation.
    :param realm_name: The realm of the user
    :param user_id: the user UUID
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The user configuration
    """

    path = '/admin/realms/{0}/users/{1}'.format(realm_name, user_id)
    get_response = keycloak_client.get(path)

    if get_response.status_code == requests.codes.ok:
        return get_response.json()

    if get_response.status_code == requests.codes.not_found:
        return None

    raise InvalidUserResponse('Unexpected user get response ({0})'.format(get_response.status_code))


def get_user_by_email(realm_name, email, keycloak_client):
    """
    Get a user representation by email.
    :param realm_name: The realm of the user
    :param email: the email of the user
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The user configuration
    """

    path = '/admin/realms/{0}/users'.format(realm_name)
    get_response = keycloak_client.get(path)

    if get_response.status_code == requests.codes.ok:
        for user_data in get_response.json():
            if user_data.get('email', None) == email:
                return user_data
        return None

    if get_response.status_code == requests.codes.not_found:
        return None

    raise InvalidUserResponse('Unexpected user get response ({0})'.format(get_response.status_code))


def update_user(realm_name, user_id, user_config, keycloak_client):
    """
    Update a user.
    :param realm_name: The realm of the user
    :param user_id: the user UUID
    :param user_config: The user configuration
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/users/{1}'.format(realm_name, user_id)
    update_response = keycloak_client.put(path, json=user_config)

    if update_response.status_code == requests.codes.no_content:
        return

    raise InvalidUserResponse('Unexpected user update response ({0})'.format(update_response.status_code))


def get_user_roles(realm_name, user_id, keycloak_client):
    """
    Get the roles associated with a user.
    :param realm_name: The realm of the user
    :param user_id: The UUID of the user
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The roles of the user
    """
    path = '/admin/realms/{0}/users/{1}/role-mappings/realm'.format(realm_name, user_id)
    get_response = keycloak_client.get(path)

    if get_response.status_code == requests.codes.ok:
        return get_response.json()

    if get_response.status_code == requests.codes.not_found:
        return None

    raise InvalidRoleResponse('Unexpected user role get response ({0})'.format(get_response.status_code))


def add_user_roles(realm_name, user_id, roles, keycloak_client):
    """
    Add roles to the user.
    :param realm_name: The realm of the user
    :param user_id: the user UUID
    :param roles: The roles to add to the user
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/users/{1}/role-mappings/realm'.format(realm_name, user_id)
    update_response = keycloak_client.post(path, json=roles)

    if update_response.status_code == requests.codes.no_content:
        return

    raise InvalidUserResponse('Unexpected user role update response ({0})'.format(update_response.status_code))


def delete_user_roles(realm_name, user_id, roles, keycloak_client):
    """
    Add roles to the user.
    :param realm_name: The realm of the user
    :param user_id: the user UUID
    :param roles: The roles to delete from the user
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/users/{1}/role-mappings/realm'.format(realm_name, user_id)
    update_response = keycloak_client.delete(path, json=roles)

    if update_response.status_code == requests.codes.no_content:
        return

    raise InvalidUserResponse('Unexpected user role deletion response ({0})'.format(update_response.status_code))


def process_user_roles(realm_name, user_id, existing_roles, new_role_names, keycloak_client):
    """
    Process the roles for a given user.
    :param realm_name: The realm of the user.
    :param user_id: The UUID of the user.
    :param existing_roles: The existing roles of the user
    :param new_role_names: The new role names for the user
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    existing_role_names = []
    for existing_role in existing_roles:
        existing_role_names.append(existing_role['name'])

    update_role_names = []
    for new_role_name in new_role_names:
        if new_role_name not in existing_role_names:
            update_role_names.append(new_role_name)

    if len(update_role_names):
        update_roles = role_names_to_roles(realm_name, update_role_names, keycloak_client)
        add_user_roles(realm_name, user_id, update_roles, keycloak_client)

    delete_roles = []
    for existing_role in existing_roles:
        if existing_role['name'] not in new_role_names and existing_role['name'] not in RESERVED_ROLES:
            delete_roles.append(existing_role)

    if len(delete_roles):
        delete_user_roles(realm_name, user_id, delete_roles, keycloak_client)


def create_realm(realm, keycloak_client):
    """
    Creates realm representation.
    :param realm: The realm representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms'
    response = keycloak_client.post(path, json=realm)

    if response.status_code == requests.codes.created:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def if_realm_exists(realm_name, keycloak_client):
    """
    Gets a client scopes representation.
    :param realm_name: The realm name
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: Boolean
    """

    path = '/admin/realms/{0}'.format(realm_name)
    response = keycloak_client.get(path)

    if response.status_code == requests.codes.ok:
        return True

    if response.status_code == requests.codes.not_found:
        return False

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def get_client_scopes(realm_name, keycloak_client):
    """
    Gets a client scopes representation.
    :param realm_name: The realm name
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The list of client scopes representation
    """

    path = '/admin/realms/{0}/client-scopes'.format(realm_name)
    response = keycloak_client.get(path)

    if response.status_code == requests.codes.ok:
        return response.json()

    if response.status_code == requests.codes.not_found:
        return None

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def create_client_scope(realm_name, client_scope, keycloak_client):
    """
    Creates a client scope representation.
    :param realm_name: The realm name
    :param client_scope: The client scope representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/client-scopes'.format(realm_name)
    response = keycloak_client.post(path, json=client_scope)

    if response.status_code == requests.codes.created:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def update_client_scope(realm_name, client_scope_id, client_scope, keycloak_client):
    """
    Updates a client scope representation.
    :param realm_name: The realm name
    :param client_scope_id: The client scope id
    :param client_scope: The client scope representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/client-scopes/{1}'.format(realm_name, client_scope_id)
    response = keycloak_client.put(path, json=client_scope)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def delete_client_scope(realm_name, client_scope_id, keycloak_client):
    """
    Deletes a client scope representation.
    :param realm_name: The realm name
    :param client_scope_id: The client scope id
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/client-scopes/{1}'.format(realm_name, client_scope_id)
    response = keycloak_client.delete(path)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def get_clients(realm_name, keycloak_client):
    """
    Get all clients representation.
    :param realm_name: The realm name
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The list of clients representation
    """

    path = '/admin/realms/{0}/clients'.format(realm_name)
    response = keycloak_client.get(path)

    if response.status_code == requests.codes.ok:
        return response.json()

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def find_client(realm_name, client_id, keycloak_client):
    """
    Find client representation by id.
    :param realm_name: The realm name
    :param client_id: The client's id (NOT clientId)
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The client representation
    """

    path = '/admin/realms/{0}/clients/{1}'.format(realm_name, client_id)
    response = keycloak_client.get(path)

    if response.status_code == requests.codes.ok:
        return response.json()

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def create_client(realm_name, client, keycloak_client):
    """
    Creates client representation.
    :param realm_name: The realm name
    :param client: The client representation
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The role representation
    """

    path = '/admin/realms/{0}/clients'.format(realm_name)
    response = keycloak_client.post(path, json=client)

    if response.status_code == requests.codes.created:
        created_id = re.sub(r'.*' + path + '/', '', response.headers["Location"])
        return created_id

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def update_client(realm_name, client_id, client, keycloak_client):
    """
    Updates client representation.
    :param realm_name: The realm name
    :param client_id: The client's id (NOT clientId)
    :param client: The client representation
    :param keycloak_client: The client to use when interacting with Keycloak
    :return: The role representation
    """

    path = '/admin/realms/{0}/clients/{1}'.format(realm_name, client_id)
    response = keycloak_client.put(path, json=client)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def delete_default_client_scope(realm_name, client_id, client_scope_id, keycloak_client):
    """
    Deletes a default client scope from client representation.
    :param realm_name: The realm name
    :param client_id: The client's id (NOT clientId)
    :param client_scope_id: The client scope id
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/clients/{1}/default-client-scopes/{2}'.format(realm_name, client_id, client_scope_id)
    response = keycloak_client.delete(path)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def add_default_client_scope(realm_name, client_id, client_scope_id, keycloak_client):
    """
    Adds a default client scope from client representation.
    :param realm_name: The realm name
    :param client_id: The client's id (NOT clientId)
    :param client_scope_id: The client scope id
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/clients/{1}/default-client-scopes/{2}'.format(realm_name, client_id, client_scope_id)
    response = keycloak_client.put(path)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def delete_optional_client_scope(realm_name, client_id, client_scope_id, keycloak_client):
    """
    Deletes a optional client scope from client representation.
    :param realm_name: The realm name
    :param client_id: The client's id (NOT clientId)
    :param client_scope_id: The client scope id
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/clients/{1}/optional-client-scopes/{2}'.format(realm_name, client_id, client_scope_id)
    response = keycloak_client.delete(path)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def add_optional_client_scope(realm_name, client_id, client_scope_id, keycloak_client):
    """
    Adds a optional client scope from client representation.
    :param realm_name: The realm name
    :param client_id: The client's id (NOT clientId)
    :param client_scope_id: The client scope id
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/clients/{1}/optional-client-scopes/{2}'.format(realm_name, client_id, client_scope_id)
    response = keycloak_client.put(path)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def get_roles(realm_name, keycloak_client):
    """
   Get all roles representation.
   :param realm_name: The realm name
   :param keycloak_client: The client to use when interacting with Keycloak
   :return: The list of roles representation
   """

    path = '/admin/realms/{0}/roles'.format(realm_name)
    response = keycloak_client.get(path)

    if response.status_code == requests.codes.ok:
        return response.json()

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def delete_role(realm_name, role_id, keycloak_client):
    """
    Deletes a role representation.
    :param realm_name: The realm name
    :param role_id: The role id
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/roles-by-id/{1}'.format(realm_name, role_id)
    response = keycloak_client.delete(path)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def create_role(realm_name, role, keycloak_client):
    """
    Creates a role representation.
    :param realm_name: The realm name
    :param role: List of roles representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/roles'.format(realm_name)
    response = keycloak_client.post(path, json=role)

    if response.status_code == requests.codes.created:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def update_role(realm_name, role_id, role, keycloak_client):
    """
    Updates a role representation.
    :param realm_name: The realm name
    :param role_id: The role id
    :param role: role representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/roles-by-id/{1}'.format(realm_name, role_id)
    response = keycloak_client.put(path, json=role)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def get_realm_scope_mapping(realm_name, client_scope_id, keycloak_client):
    """
   Get roles with assigned client scope.
   :param realm_name: The realm name
   :param client_scope_id: The client scope id
   :param keycloak_client: The client to use when interacting with Keycloak
   :return: The list of role representation
   """

    path = '/admin/realms/{0}/client-scopes/{1}/scope-mappings/realm'.format(realm_name, client_scope_id)
    response = keycloak_client.get(path)

    if response.status_code == requests.codes.ok:
        return response.json()

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def delete_realm_scope_mapping(realm_name, client_scope_id, roles, keycloak_client):
    """
    Deletes a default client scope from client representation.
    :param realm_name: The realm name
    :param client_scope_id: The client scope id
    :param roles: List of roles representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/client-scopes/{1}/scope-mappings/realm'.format(realm_name, client_scope_id)
    response = keycloak_client.delete(path, json=roles)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))


def add_realm_scope_mapping(realm_name, client_scope_id, roles, keycloak_client):
    """
    Adds a default client scope from client representation.
    :param realm_name: The realm name
    :param client_scope_id: The client scope id
    :param roles: List of roles representation
    :param keycloak_client: The client to use when interacting with Keycloak
    """

    path = '/admin/realms/{0}/client-scopes/{1}/scope-mappings/realm'.format(realm_name, client_scope_id)
    response = keycloak_client.post(path, json=roles)

    if response.status_code == requests.codes.no_content:
        return

    raise InvalidResponse('Unexpected response ({0})'.format(response.status_code))
