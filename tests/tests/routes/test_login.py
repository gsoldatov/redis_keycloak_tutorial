"""
/auth/login route tests.
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
    cli_no_kc_and_redis: AsyncClient,
    data_generator: DataGenerator
):
    # Try to log in, while Keycloak "is unavailable"
    # (by using an app with a wrong Keycloak port)
    body = data_generator.auth.get_login_credentials_request_body()
    resp = await cli_no_kc_and_redis.post("/auth/login", json=body)
    assert resp.status_code == 503


async def test_disabled_user(
    cli_no_redis: AsyncClient,
    data_generator: DataGenerator,
    keycloak_manager: KeycloakManager
):
    # Add a disabled user to Keycloak
    user_id = keycloak_manager.add_user("username", "password", [], enabled=False)

    # Try to log in as a diabled user
    body = data_generator.auth.get_login_credentials_request_body()
    resp = await cli_no_redis.post("/auth/login", json=body)
    assert resp.status_code == 401

    # Check if a session was not created
    assert len(keycloak_manager.get_user_sessions(user_id)) == 0


async def test_invalid_credentials(
    cli_no_redis: AsyncClient,
    data_generator: DataGenerator,
    keycloak_manager: KeycloakManager
):
    # Add a user to Keycloak
    user_id = keycloak_manager.add_user("username", "password", [])

    # Try to log in with incorrect credentials
    for attr, value in [("username", "incorrect"), ("password", "incorrect")]:
        body = data_generator.auth.get_login_credentials_request_body()
        body[attr] = value
        resp = await cli_no_redis.post("/auth/login", json=body)
        assert resp.status_code == 401

    # Check if a session was not created
    assert len(keycloak_manager.get_user_sessions(user_id)) == 0


async def test_successful_login(
    cli_no_redis: AsyncClient,
    app_no_redis: FastAPI,
    data_generator: DataGenerator,
    keycloak_manager: KeycloakManager
):
    # Add a user to Keycloak
    user_id = keycloak_manager.add_user("username", "password", [])

    # Try to log in
    body = data_generator.auth.get_login_credentials_request_body()
    resp = await cli_no_redis.post("/auth/login", json=body)
    assert resp.status_code == 200
    data = resp.json()
    access_token = data["access_token"]

    # Check if a session was created
    assert len(keycloak_manager.get_user_sessions(user_id)) == 1

    # Check if access/refresh token was cached
    assert app_no_redis.state.token_cache.contains(access_token)


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
