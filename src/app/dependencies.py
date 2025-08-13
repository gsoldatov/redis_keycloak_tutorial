from fastapi import Request

from config import Config
from src.keycloak.client import KeycloakClient


def get_keycloak_client(request: Request):
    config: Config = request.app.state.config
    yield KeycloakClient(config.keycloak)


def bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]  # Remove 'Bearer ' prefix
