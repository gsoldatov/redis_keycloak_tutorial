from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.app.dependencies import get_keycloak_client, get_redis_client, \
    get_bearer_token, get_token_cache
from src.app.models import UserRegistrationCredentials, UserCredentials
from src.app.tokens import TokenCache
from src.keycloak.client import KeycloakClient
from src.redis.client import RedisClient


auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register")
async def register(
    credentials: UserRegistrationCredentials,
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)],
    redis_client: Annotated[RedisClient, Depends(get_redis_client)]
):
    # Add a Keycloak user
    user_id = await keycloak_client.register(credentials)
    
    # Add user credentials to Redis
    # NOTE: possible failure to add a user to Redis after it's
    # created in Keycloak is not handled
    await redis_client.set_user(user_id, credentials)

    # Return a response
    raise HTTPException(status_code=201)


@auth_router.post("/login")
async def login(
    credentials: UserCredentials,
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)],
    token_cache: Annotated[TokenCache, Depends(get_token_cache)]
):
    tokens = await keycloak_client.login(credentials)
    await token_cache.add(tokens)
    return {"access_token": tokens["access_token"]}


@auth_router.post("/logout")
async def logout(
    access_token: Annotated[str, Depends(get_bearer_token)],
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)],
    token_cache: Annotated[TokenCache, Depends(get_token_cache)]
):
    if access_token is None:
        raise HTTPException(status_code=403, detail="Missing bearer token.")

    refresh_token = await token_cache.get(access_token)
    if refresh_token is None:
        raise HTTPException(status_code=204)

    await keycloak_client.logout(refresh_token)
    await token_cache.pop(access_token)
    raise HTTPException(status_code=204)
