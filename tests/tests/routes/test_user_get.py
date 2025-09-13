"""
GET /users/:username route tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from httpx import AsyncClient

from src.redis.admin import RedisAdminClient
from tests.data_generators import DataGenerator


async def test_network_error(
    cli_no_kc_and_redis: AsyncClient,
):
    resp = await cli_no_kc_and_redis.get("/users/username")
    assert resp.status_code == 503


async def test_username_validation(cli: AsyncClient):
    resp = await cli.get(f"/users/{'a' * 7}")
    assert resp.status_code == 422


async def test_non_existing_username(
    cli: AsyncClient,
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient
):
    # Add an existing user
    redis_admin_client.set_user(data_generator.users.redis_user_data(username="existing"))

    # Query a non-existing user
    resp = await cli.get(f"/users/non_existing")
    assert resp.status_code == 404


async def test_existing_username(
    cli: AsyncClient,
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient
):
    # Add existing users
    existing_user = data_generator.users.redis_user_data(username="existing")
    redis_admin_client.set_user(existing_user)
    redis_admin_client.set_user(data_generator.users.redis_user_data(username="another_existing"))

    # Query a non-existing user
    resp = await cli.get(f"/users/{existing_user.username}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("username", None) == existing_user.username
    assert data.get("first_name", None) == existing_user.first_name
    assert data.get("last_name", None) == existing_user.last_name
    assert data.get("user_id", None) == None


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
