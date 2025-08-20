from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.app.dependencies import get_keycloak_client, get_bearer_token, get_token_cache, validate_token_role
from src.exceptions import AuthException, NetworkException
from src.app.models import UserCredentials
from src.app.tokens import TokenCache
from src.keycloak.client import KeycloakClient


router = APIRouter()


@router.post("/login")
async def login(
    credentials: UserCredentials,
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)],
    token_cache: Annotated[TokenCache, Depends(get_token_cache)]
):
    try:
        tokens = await keycloak_client.login(credentials.username, credentials.password)
        token_cache.add(tokens)
        return {"access_token": tokens["access_token"]}
    except AuthException:
        raise HTTPException(status_code=401)
    except NetworkException:
        raise HTTPException(status_code=503)


@router.post("/logout")
async def logout(
    access_token: Annotated[str, Depends(get_bearer_token)],
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)],
    token_cache: Annotated[TokenCache, Depends(get_token_cache)]
):
    if access_token is None:
        raise HTTPException(status_code=403, detail="Missing bearer token.")

    refresh_token = token_cache.get(access_token)
    if refresh_token is None:
        raise HTTPException(status_code=204)

    try:
        await keycloak_client.logout(refresh_token)
        token_cache.pop(access_token)
        raise HTTPException(status_code=204)
    except NetworkException:
        raise HTTPException(status_code=503)


@router.get("/protected/first")
async def protected_first(
    valid_token: Annotated[None, Depends(validate_token_role("role-1"))]
):
    return {"value": 1}


@router.get("/protected/second")
async def protected_second(
    valid_token: Annotated[None, Depends(validate_token_role("role-2"))]
):
    return {"value": 2}
