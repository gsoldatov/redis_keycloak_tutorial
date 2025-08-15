import json

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


    async def validate_token(self, token: dict):
        pass
        # await self.client.a_decode_token()
        # await self.client.a_introspect()
