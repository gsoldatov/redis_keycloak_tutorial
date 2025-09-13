from functools import wraps
import json

from keycloak import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError, \
    KeycloakConnectionError

from config import KeycloakConfig
from src.app.models import UserCredentials, UserRegistrationCredentials
from src.exceptions import NetworkException, AuthException


def ensure_admin_token(fn):
    """
    Decorator, which ensures that the admin client has a valid token
    before it executes a command (since it can't be obtained on the app realm)
    """
    @wraps(fn)
    async def inner(self: "KeycloakClient", *args, **kwargs):
        try:
            self.admin_client.change_current_realm("master")
            await self.admin_client.connection.a__refresh_if_required()
            self.admin_client.change_current_realm(self.kc_config.app_realm_name)

            return await fn(self, *args, **kwargs)
        except KeycloakConnectionError as e:
            raise NetworkException from e

    return inner


class KeycloakClient:
    def __init__(self, kc_config: KeycloakConfig):
        self.kc_config = kc_config
        self._app_client_id: str | None = None

        self.client = KeycloakOpenID(
            server_url=kc_config.keycloak_url,
            realm_name=kc_config.app_realm_name,
            client_id=kc_config.app_client_id,
            client_secret_key=kc_config.app_client_secret
        )
        self.admin_client = KeycloakAdmin(
            server_url=kc_config.keycloak_url,
            username=kc_config.admin_username,
            password=kc_config.admin_password,
            realm_name=kc_config.app_realm_name
        )
    
    @ensure_admin_token
    async def register(self, credentials: UserRegistrationCredentials) -> str:
        try:
            user_id = await self.admin_client.a_create_user({
                "username": credentials.username,
                "enabled": True,
                "credentials": [{
                    "type": "password",
                    "value": credentials.password,
                    "temporary": False
                }],

                # Additional attributes, which are required for account setup
                "firstName": credentials.first_name,
                "lastName": credentials.last_name,
                "email": credentials.email,
                "emailVerified": True
            })
            
            # Assign default roles
            app_client_id = await self._get_app_client_id()
            existing_roles = await self.admin_client.a_get_client_roles(app_client_id)
            roles_to_assign = [r for r in existing_roles if r["name"] in ["can-post"]]
            await self.admin_client.a_assign_client_role(user_id, app_client_id, roles_to_assign)

            return user_id
        
        except (KeycloakPostError, ) as e:
            raise AuthException from e
        except (KeycloakConnectionError,) as e:
            raise NetworkException from e
    
    async def login(self, credentials: UserCredentials) -> dict:
        try:
            return await self.client.a_token(credentials.username, credentials.password)
        except (KeycloakAuthenticationError, KeycloakPostError) as e:
            # KeyCloakPostError can occur if account is not fully set up
            raise AuthException from e
        except (KeycloakConnectionError,) as e:
            raise NetworkException from e
    
    async def logout(self, refresh_token: str):
        try:
            await self.client.a_logout(refresh_token)
        except (KeycloakConnectionError,) as e:
            raise NetworkException from e
        except KeycloakPostError as e:
            try:
                error_json = json.loads(e.error_message)
                if error_json.get("error", None) == "invalid_grant":
                    pass    # ignore invalid refresh tokens
                else:
                    raise
            except:
                raise e

    async def introspect_token(self, access_token: str) -> dict:
        """ Introspects the `access_token` and returns the introspection results. """
        try:
            return await self.client.a_introspect(access_token)
        except KeycloakConnectionError as e:
            raise NetworkException from e

    async def refresh_token(self, refresh_token: str) -> dict:
        """ Refreshes access token using `refresh_token`. Returns new tokens. """
        try:
            return await self.client.a_refresh_token(refresh_token)
        except (KeycloakConnectionError,) as e:
            raise NetworkException from e
        except (KeycloakAuthenticationError, KeycloakPostError) as e:
            raise AuthException from e

    async def decode_token(self, access_token: str) -> dict:
        """ Decodes the access token and returns its contents. """
        try:
            return await self.client.a_decode_token(access_token)
        except KeycloakConnectionError as e:
            raise NetworkException from e
        except (KeycloakAuthenticationError, KeycloakPostError) as e:
            raise AuthException from e
    
    @ensure_admin_token
    async def _get_app_client_id(self) -> str:
        """ Fetches, caches and returns an internal UUID of app client. """
        if self._app_client_id is None:
            self._app_client_id = await self.admin_client.a_get_client_id(self.kc_config.app_client_id)
        if self._app_client_id is None: raise Exception("Failed to retrieve app client ID.")
        return self._app_client_id
