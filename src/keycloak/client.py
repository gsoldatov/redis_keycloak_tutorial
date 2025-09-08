import json

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError, \
    KeycloakConnectionError

from config import KeycloakConfig
from src.app.models import UserCredentials
from src.exceptions import NetworkException, AuthException


class KeycloakClient:
    def __init__(self, kc_config: KeycloakConfig):
        self.kc_config = kc_config
        self.client = KeycloakOpenID(
            server_url=kc_config.keycloak_url,
            realm_name=kc_config.app_realm_name,
            client_id=kc_config.app_client_id,
            client_secret_key=kc_config.app_client_secret
        )
    
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
