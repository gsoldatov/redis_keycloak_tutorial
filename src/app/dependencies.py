from fastapi import Request

from config import Config
from src.app.tokens import TokenCache
from src.keycloak.client import KeycloakClient


def get_keycloak_client(request: Request):
    config: Config = request.app.state.config
    return KeycloakClient(config.keycloak)


def get_token_cache(request: Request):
    token_cache: TokenCache = request.app.state.token_cache
    return token_cache


def get_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]  # Remove 'Bearer ' prefix
