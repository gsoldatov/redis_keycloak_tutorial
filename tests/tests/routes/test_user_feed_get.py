"""
GET /users/:username/feed route tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from datetime import datetime
from httpx import AsyncClient

from src.redis.admin import RedisAdminClient
from tests.data_generators import DataGenerator


async def test_redis_network_error(
    cli_no_redis: AsyncClient
):
    # Try to get user's posts
    resp = await cli_no_redis.get("/users/username/feed")
    assert resp.status_code == 503


async def test_validation(
    cli_no_redis: AsyncClient
):
    # Username validation
    resp = await cli_no_redis.get("/users/a/feed")
    assert resp.status_code == 422

    # Last viewed validation
    resp = await cli_no_redis.get("/users/username/feed", params={"last_viewed": -1})
    assert resp.status_code == 422


async def test_feed_of_a_non_existing_user(
    cli: AsyncClient
):
    # Get feed posts without offset
    resp = await cli.get("/users/username/feed")
    assert resp.status_code == 404

    # Get feed posts with offset
    resp = await cli.get("/users/username/feed", params={"last_viewed": 5})
    assert resp.status_code == 404


async def test_user_feed_without_posts(
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add a user
    redis_admin_client.set_user(data_generator.users.redis_user_data())

    # Get feed posts without offset
    resp = await cli.get("/users/username/feed")
    assert resp.status_code == 404

    # Get feed posts with offset
    resp = await cli.get("/users/username/feed", params={"last_viewed": 5})
    assert resp.status_code == 404


async def test_user_feed_with_posts(
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add users
    username, followed = "username", "followed"
    for username_ in (username, followed):
        redis_admin_client.set_user(data_generator.users.redis_user_data(username=username_))
    
    # Follow user
    redis_admin_client.add_user_follower(followed, username)

    # Add followed user's posts
    posts = [data_generator.posts.post(post_id=i, author=followed) for i in range(1, 11)]
    for post in posts:
        redis_admin_client.add_post(post)
    
    # Get feed posts without offset
    resp = await cli.get(f"/users/{username}/feed")
    assert resp.status_code == 200

    response_posts = resp.json()["posts"]
    assert [post["post_id"] for post in response_posts] == [10, 9, 8, 7, 6]

    # Check response post attributes
    post = posts[-1]
    assert post.post_id == response_posts[0]["post_id"]
    assert post.author == response_posts[0]["author"]
    assert post.content == response_posts[0]["content"]
    assert post.created_at == datetime.fromisoformat(response_posts[0]["created_at"])

    # Get feed posts with offset
    resp = await cli.get(f"/users/{username}/feed", params={"last_viewed": 5})
    assert resp.status_code == 200
    response_posts = resp.json()["posts"]
    assert [post["post_id"] for post in response_posts] == [4, 3, 2, 1]

    # Get feed posts with offset > number of posts
    resp = await cli.get(f"/users/{username}/feed", params={"last_viewed": 10})
    assert resp.status_code == 404


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
