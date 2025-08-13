from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError, \
    KeycloakConnectionError

from config import KeycloakConfig
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
    
    async def login(self, username: str, password: str) -> dict:
        try:
            return await self.client.a_token(username, password)
        except (KeycloakAuthenticationError, KeycloakPostError) as e:
            # KeyCloakPostError can occur if account is not fully set up
            raise AuthException from e
        except (KeycloakConnectionError,) as e:
            raise NetworkException from e
    
    async def logout(self, token: dict):
        await self.client.a_logout(token["refresh_token"])

    async def validate_token(self, token: dict):
        pass
        # await self.client.a_introspect()
