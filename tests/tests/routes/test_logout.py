"""
/auth/logout route tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from fastapi import FastAPI
from httpx import AsyncClient

from src.keycloak.setup import KeycloakManager
from tests.data_generators import DataGenerator


async def test_network_error(
    app_no_kc_and_redis: FastAPI,
    cli_no_kc_and_redis: AsyncClient,
    data_generator: DataGenerator
):
    # Add a mock access/refresh token pair
    tokens = {"access_token": "some access token", "refresh_token": "some refresh token"}
    app_no_kc_and_redis.state.token_cache.add(tokens)

    # Try to log out, while Keycloak "is unavailable"
    # (by using an app with a wrong Keycloak port)
    headers = data_generator.auth.get_bearer_header(tokens["access_token"])
    resp = await cli_no_kc_and_redis.post("/auth/logout", headers=headers)
    assert resp.status_code == 503


async def test_missing_authorization_header(
    cli_no_kc_and_redis: AsyncClient
):
    resp = await cli_no_kc_and_redis.post("/auth/logout")
    assert resp.status_code == 403


async def test_invalid_authorization_header_format(
    cli_no_kc_and_redis: AsyncClient
):
    headers = {"Authorization": "incorrect bearer token"}
    resp = await cli_no_kc_and_redis.post("/auth/logout", headers=headers)
    assert resp.status_code == 403


async def test_non_existing_in_cache_token(
    cli_no_redis: AsyncClient,
    data_generator: DataGenerator
):
    headers = data_generator.auth.get_bearer_header("token, which does not exist in cache")
    logout_resp = await cli_no_redis.post("/auth/logout", headers=headers)
    assert logout_resp.status_code == 204
    

async def test_expired_token(
    app_no_redis: FastAPI,
    cli_no_redis: AsyncClient,
    data_generator: DataGenerator,
    keycloak_manager: KeycloakManager
):
    # Add a user to Keycloak
    user_id = keycloak_manager.add_user("username", "password", [])

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli_no_redis.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Expire token
    keycloak_manager.delete_user_sessions(user_id)
    assert len(keycloak_manager.get_user_sessions(user_id)) == 0

    # Try to log out
    headers = data_generator.auth.get_bearer_header(access_token)
    logout_resp = await cli_no_redis.post("/auth/logout", headers=headers)
    assert logout_resp.status_code == 204

    # Check if token was removed from cache
    assert not app_no_redis.state.token_cache.contains(access_token)


async def test_successful_logout(
    app_no_redis: FastAPI,
    cli_no_redis: AsyncClient,
    data_generator: DataGenerator,
    keycloak_manager: KeycloakManager
):
    # Add a user to Keycloak
    user_id = keycloak_manager.add_user("username", "password", [])

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli_no_redis.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Try to log out
    headers = data_generator.auth.get_bearer_header(access_token)
    logout_resp = await cli_no_redis.post("/auth/logout", headers=headers)
    assert logout_resp.status_code == 204

    # Check if token was removed from cache
    assert not app_no_redis.state.token_cache.contains(access_token)

    # Check if a session was removed from Keycloak
    assert len(keycloak_manager.get_user_sessions(user_id)) == 0


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
