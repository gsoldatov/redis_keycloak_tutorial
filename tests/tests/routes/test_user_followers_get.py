"""
GET /users/:username/followers route tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from httpx import AsyncClient

from src.keycloak.admin import KeycloakAdminClient
from src.redis.admin import RedisAdminClient
from tests.data_generators import DataGenerator


async def test_redis_network_error(
        cli_no_kc_and_redis: AsyncClient
):
    # Try to get user's followers
    resp = await cli_no_kc_and_redis.get("/users/username/followers")
    assert resp.status_code == 503


async def test_validation(
    cli_no_kc_and_redis: AsyncClient
):
    # Invalid username
    resp = await cli_no_kc_and_redis.get("/users/a/followers")
    assert resp.status_code == 422

    # Invalid last_viewed
    resp = await cli_no_kc_and_redis.get("/users/username/followers", params={"last_viewed": -1})
    assert resp.status_code == 422


async def test_non_existing_username(
    cli: AsyncClient
):
    resp = await cli.get("/users/username/followers")
    assert resp.status_code == 404


async def test_user_without_followers(
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add a user to Redis
    redis_admin_client.set_user(data_generator.users.redis_user_data())
    
    # Try fetching user followers without offset
    resp = await cli.get("/users/username/followers")
    assert resp.status_code == 404
    
    # Try fetching user followers with offset
    resp = await cli.get("/users/username/followers", params={"last_viewed": 10})
    assert resp.status_code == 404


async def test_user_with_followers(
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    follower_name = lambda i: f"follower_{i:02d}"
    # Add users & followers to Redis
    redis_admin_client.set_user(data_generator.users.redis_user_data(username="username"))
    for i in range(10):
        follower = follower_name(i)
        redis_admin_client.set_user(data_generator.users.redis_user_data(username=follower))
        redis_admin_client.add_user_follower("username", follower)
    
    # Fetch user followers without offset
    resp = await cli.get("/users/username/followers")
    assert resp.status_code == 200
    assert resp.json()["followers"] == [follower_name(i) for i in range(5)]
    
    # Fetch user followers with offset
    resp = await cli.get("/users/username/followers", params={"last_viewed": 5})
    assert resp.status_code == 200
    assert resp.json()["followers"] == [follower_name(i) for i in range(6, 10)]

    # Fetch user followers with offset exceeding number of followers
    resp = await cli.get("/users/username/followers", params={"last_viewed": 10})
    assert resp.status_code == 404


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
