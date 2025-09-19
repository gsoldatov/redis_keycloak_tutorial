from functools import wraps
from time import sleep
from typing import Self, Any

from keycloak import KeycloakAdmin
import httpx

from config import KeycloakConfig


ALL_ROLES = ["role-1", "role-2", "can-post"]
""" Full list of Keycloak app client roles. """


def reset_keycloak_app_realm(kc_config: KeycloakConfig):
    """
    Deletes existing app realm, creates a new one 
    and adds app client & roles into it.
    """
    with KeycloakAdminClient(kc_config) as keycloak_admin_client:
        keycloak_admin_client.delete_app_realm()

        keycloak_admin_client.create_app_realm()
        keycloak_admin_client.create_app_client()
        keycloak_admin_client.add_client_role("role-1")
        keycloak_admin_client.add_client_role("role-2")
        keycloak_admin_client.add_client_role("can-post")


def reset_keycloak_app_realm_users(kc_config: KeycloakConfig):
    """ Creates or replaces test users in the app realm. """
    with KeycloakAdminClient(kc_config) as keycloak_admin_client:
        keycloak_admin_client.delete_users(["first_user", "second_user", "superuser"])
        user_1_id = keycloak_admin_client.add_user("first_user", "password", ["role-1"])
        user_2_id = keycloak_admin_client.add_user("second_user", "password", ["role-2"])
        superuser_id = keycloak_admin_client.add_user("superuser", "password", ALL_ROLES)


def in_app_realm(fn):
    """
    Decorator for KeycloakAdminClient methods, which ensures,
    that app realm is selected as current realm when a method is called.
    """
    @wraps(fn)
    def inner(self: "KeycloakAdminClient", *args, **kwargs) -> Any:
        current_realm = self.admin.get_current_realm()

        # Ensure admin tokens are issued, while master realm is selected
        # (connecting to app realm before tokens are obtained results in auth failure (due to invalid user credentials))
        if self.admin.connection.token is None:
            self.admin.change_current_realm("master")
            self.admin.connection._refresh_if_required()

        self.admin.change_current_realm(self.kc_config.app_realm_name)
        result = fn(self, *args, **kwargs)
        self.admin.change_current_realm(current_realm)
        return result
    
    return inner


class KeycloakAdminClient:
    def __init__(self, kc_config: KeycloakConfig):
        self.kc_config = kc_config
        self.admin = KeycloakAdmin(
            server_url=kc_config.keycloak_url,
            username=kc_config.admin_username,
            password=kc_config.admin_password,
            realm_name="master"
        )
        self._app_client_id: str | None = None
    
    def wait_for_server(self) -> None:
        """
        Waits for Keycloak server healthcheck endpoint to be successfully called.
        Throws if maximum amount of endpoint calls is exceeded
        """
        retries = -1

        while retries < self.kc_config.max_healthcheck_retries:
            try:
                result = httpx.get(url=self.kc_config.keycloak_healthcheck_url, timeout=self.kc_config.healthcheck_retry_timeout)
                if result.status_code == 200: return
                else: retries += 1
            except (TimeoutError, httpx.RemoteProtocolError) as e:
                # httpx.RemoteProtocolError is thrown, while container is being prepared;
                # this exception is handled separately with an explicit sleep during the retry timeout
                if isinstance(e, httpx.RemoteProtocolError):
                    sleep(self.kc_config.healthcheck_retry_timeout)
                retries += 1
            
        raise TimeoutError("Failed to await for Keycloak server to be ready.")
    
    def __enter__(self) -> Self:
        self.wait_for_server()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        pass
    
    @property
    def app_client_id(self) -> str:
        """ Fetches, caches and returns an internal UUID of app client. """
        if self._app_client_id is None:
            self._app_client_id = self.admin.get_client_id(self.kc_config.app_client_id)
        
        if self._app_client_id is None: raise Exception("Failed to retrieve app client ID.")
        return self._app_client_id

    def create_app_realm(self) -> None:
        """ Creates app realm. """
        self.admin.create_realm({
            "realm": self.kc_config.app_realm_name,
            "enabled": True
        }, skip_exists=True)
    
    def delete_app_realm(self) -> None:
        """ Deletes app realm. """
        try:
            self.admin.delete_realm(self.kc_config.app_realm_name)
        except Exception:   # Ignore 404
            pass
    
    @in_app_realm
    def create_app_client(self) -> None:
        """ Creates app client in the app realm and configures it. """
        self.admin.create_client({
            "clientId": self.kc_config.app_client_id,
            "enabled": True,
            "protocol": "openid-connect",

            "publicClient": False,
            "clientAuthenticatorType": "client-secret",
            "secret": self.kc_config.app_client_secret,
            "serviceAccountsEnabled": False,

            "standardFlowEnabled": False,
            "directAccessGrantsEnabled": True,
        })
    
    @in_app_realm
    def get_app_client(self) -> dict:
        """ Returns current settings of the app client. """
        return self.admin.get_client(self.app_client_id)
    
    @in_app_realm
    def update_app_client(self, new_props: dict) -> None:
        """ Updates app client with `new_props`. """
        self.admin.update_client(self.app_client_id, new_props)
    
    @in_app_realm
    def delete_app_client(self) -> None:
        """Deletes app client in the app realm."""
        self.admin.delete_client(self.app_client_id)

    @in_app_realm
    def add_client_role(self, name: str) -> None:
        """Adds a client role with the given `name` to the app client in the app realm."""
        self.admin.create_client_role(
            self.app_client_id, {
            "name": name,
            "description": "",
            "composite": False,
            "clientRole": True,
        })
    
    @in_app_realm
    def delete_client_role(self, role_name: str) -> None:
        """Deletes a client role with the given `role_name` for the app client in the app realm."""
        self.admin.delete_client_role(self.app_client_id, role_name)

    @in_app_realm
    def add_user(
        self,
        username: str = "username",
        password: str = "password",
        app_client_roles: list[str] | None = ALL_ROLES,
        email: str | None = None,
        enabled: bool = True
    ) -> str:
        """
        Creates a user in the app realm with the given attributes.
        Assigns client roles to the user.
        Returns the user ID.
        """
        email = email if email is not None else f"{username}@example.com"
        user_id = self.admin.create_user({
            "username": username,
            "enabled": enabled,
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }],

            # Additional attributes, which are required for account setup
            "firstName": f"{username} first name",
            "lastName": f"{username} last name",
            "email": email,
            "emailVerified": True
        })

        if app_client_roles:
            self.assign_client_roles(user_id, app_client_roles)
        
        return user_id

    @in_app_realm
    def assign_client_roles(self, user_id: str, roles: list[str]) -> None:
        """
        Assigns the given client 'roles' to the specified `user_id`.
        Roles must exist in the app client.
        """
        # Retrieve role representations to pass into the assignment API call
        existing_roles = self.admin.get_client_roles(self.app_client_id)
        roles_to_assign = [r for r in existing_roles if r["name"] in roles]
        
        if roles_to_assign:
            self.admin.assign_client_role(user_id, self.app_client_id, roles_to_assign)

    @in_app_realm
    def get_users(self) -> list[dict]:
        """ Returns all existing users in the app realm. """
        return self.admin.get_users()
    
    @in_app_realm
    def delete_user(self, user_id: str) -> None:
        """ Deletes a user with the given `user_id` in the app realm. """
        self.admin.delete_user(user_id)
    
    @in_app_realm
    def delete_users(self, usernames: list[str]) -> None:
        """ Deletes users with provided `usernames`, if they exist. """
        for username in usernames:
            users = self.admin.get_users({"username": username})
            if users:
                self.admin.delete_user(users[0]["id"])

    @in_app_realm
    def delete_all_users(self) -> None:
        """ Deletes all users in the app realm. """
        for user in self.admin.get_users():
            self.admin.delete_user(user["id"])
    
    @in_app_realm
    def get_user_sessions(self, user_id: str) -> list[dict]:
        return self.admin.get_sessions(user_id)
    
    @in_app_realm
    def delete_user_sessions(self, user_id: str) -> None:
        """ Invalidates all session of a user with `user_id`. """
        self.admin.user_logout(user_id)
