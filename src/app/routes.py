from fastapi import APIRouter, Depends, Response, HTTPException
from typing import Annotated

from src.app.dependencies import get_keycloak_client
from src.app.models import UserCredentials
from src.exceptions import AuthException, NetworkException
from src.keycloak.client import KeycloakClient


router = APIRouter()


@router.post("/login")
async def login(
    credentials: UserCredentials,
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)]
):
    try:
        token = await keycloak_client.login(credentials.username, credentials.password)
        return {"token": token}
    except AuthException:
        raise HTTPException(status_code=401)
    except NetworkException:
        raise HTTPException(status_code=503)


@router.post("/logout")
async def logout(
    token: str,
    keycloak_client: Annotated[KeycloakClient, Depends(get_keycloak_client)]
):
    pass
    # # TODO get token from bearer header, perform logout & handle exceptions (network, invalid token)
    # try:
    #     # await keycloak_client.logout()
    #     return Response(status_code=204)
    # except AuthException:
    #     raise HTTPException(status_code=401)
    # except NetworkException:
    #     raise HTTPException(status_code=503)


@router.get("/protected/1")
async def protected_first():
    pass


@router.get("/protected/2")
async def protected_second():
    pass
