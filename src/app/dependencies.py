from fastapi import Request, Depends
from redis.asyncio import Redis
from typing import Annotated

from config import Config
from src.app.tokens import TokenCache
from src.keycloak.client import KeycloakClient
from src.redis.client import RedisClient
from src.exceptions import UnauthorizedOperationException, ForbiddenOperationException


def get_keycloak_client(request: Request):
    config: Config = request.app.state.config
    return KeycloakClient(config.keycloak)


def get_redis_client(request: Request):
    redis: Redis = request.app.state.redis
    return RedisClient(redis)


def get_token_cache(request: Request):
    token_cache: TokenCache = request.app.state.token_cache
    return token_cache


def get_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]  # Remove 'Bearer ' prefix


async def get_refreshed_token(
    access_token: Annotated[str | None, Depends(get_bearer_token)],
    token_cache: Annotated[TokenCache, Depends(get_token_cache)],
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)]
) -> str:
    """
    Introspects `access_token` sent via bearer header. Attempts to refresh it and update token cache, if it's invalid.
    Returns the current version of the access token or raises 401, if such version could not be introspected/refreshed.
    """
    if access_token is None:
        raise UnauthorizedOperationException("Missing bearer token.")

    # Validate token
    token_info = await keycloak_client.introspect_token(access_token)
    if token_info.get("active", False):
        return access_token
    
    # Token is invalid/expired, try to refresh
    refresh_token = token_cache.pop(access_token)
    if refresh_token is None:
        raise UnauthorizedOperationException("Invalid or expired token.")

    # Refresh token
    new_tokens = await keycloak_client.refresh_token(refresh_token)
    token_cache.add(new_tokens)
    return new_tokens["access_token"]


async def get_decoded_token(
    access_token: Annotated[str, Depends(get_refreshed_token)],
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)]
) -> dict:
    """ Gets decoded access_token sent via request headers. """
    return await keycloak_client.decode_token(access_token, validate=False)


def validate_token_role(role: str):
    """
    Ensures that the current access_token (sent via request or refreshed)
    contains the specified realm `role`.
    """
    async def inner(
        request: Request,
        access_token: Annotated[str, Depends(get_refreshed_token)],
        keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)]
    ) -> None:
        config: Config = request.app.state.config

        token_data = await keycloak_client.decode_token(access_token, validate=False)
        resource_roles = token_data\
            .get("resource_access", {})\
            .get(config.keycloak.app_client_id, {})\
            .get("roles", [])
        
        if role not in resource_roles:
            raise ForbiddenOperationException("Operation is not allowed.")
    
    return inner
