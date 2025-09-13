"""
/auth/register route tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from httpx import AsyncClient

from src.keycloak.admin import KeycloakAdminClient
from src.redis.admin import RedisAdminClient
from tests.data_generators import DataGenerator


async def test_keycloak_network_error(
    cli_no_kc_and_redis: AsyncClient,
    data_generator: DataGenerator
):
    # Try to log in, while Keycloak "is unavailable"
    # (by using an app with a wrong Keycloak port)
    body = data_generator.auth.get_auth_register_request_body()
    resp = await cli_no_kc_and_redis.post("/auth/register", json=body)
    assert resp.status_code == 503


async def test_redis_network_error(
    cli_no_redis: AsyncClient,
    data_generator: DataGenerator
):
    # Try to log in, while Redis "is unavailable"
    # (by using an app with a wrong Redis port)
    body = data_generator.auth.get_auth_register_request_body()
    resp = await cli_no_redis.post("/auth/register", json=body)
    assert resp.status_code == 503


async def test_validation(
    cli_no_kc_and_redis: AsyncClient,
    data_generator: DataGenerator
):
    # Check if validator is called (full validation tests are inside `validation` dir)
    body = data_generator.auth.get_auth_register_request_body(username="")
    resp = await cli_no_kc_and_redis.post("/auth/register", json=body)
    assert resp.status_code == 422


async def test_existing_email(
    cli: AsyncClient,
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    redis_admin_client: RedisAdminClient
):
    # Add an existing user
    email = "existing@example.com"
    keycloak_admin_client.add_user(username="first_user", email=email)

    # Try adding a user with the existing email
    body = data_generator.auth.get_auth_register_request_body(username="second_user", email=email)
    resp = await cli.post("/auth/register", json=body)
    assert resp.status_code == 400

    # Check if Keycloak has a single user
    keycloak_users = keycloak_admin_client.get_users()
    assert len(keycloak_users) == 1
    assert keycloak_users[0]["username"] == "first_user"

    # Check if Redis does not have a user
    assert redis_admin_client.get_user("second_user") is None


async def test_existing_username(
    cli: AsyncClient,
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    redis_admin_client: RedisAdminClient
):
    # Add an existing user
    username = "existing"
    keycloak_admin_client.add_user(username=username, email="first@example.com")

    # Try adding a user with the existing username
    body = data_generator.auth.get_auth_register_request_body(username=username, email="second@exmaple.com")
    resp = await cli.post("/auth/register", json=body)
    assert resp.status_code == 400

    # Check if Keycloak has a single user
    keycloak_users = keycloak_admin_client.get_users()
    assert len(keycloak_users) == 1
    assert keycloak_users[0]["username"] == username

    # Check if Redis does not have a user
    assert redis_admin_client.get_user(username) is None


async def test_successful_registration(
    cli: AsyncClient,
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    redis_admin_client: RedisAdminClient
):
    # Add a new user
    body = data_generator.auth.get_auth_register_request_body()
    resp = await cli.post("/auth/register", json=body)
    assert resp.status_code == 201

    # Check if Keycloak has a new user
    keycloak_users = keycloak_admin_client.get_users()
    assert len(keycloak_users) == 1
    assert keycloak_users[0]["username"] == body["username"]

    # Check if Redis has user data
    redis_user_data = redis_admin_client.get_user(body["username"])
    assert redis_user_data is not None
    assert redis_user_data.username == body["username"]
    assert redis_user_data.first_name == body["first_name"]
    assert redis_user_data.last_name == body["last_name"]


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
