"""
GET /posts/:post_id route tests.
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
    # Try to fetch a post
    resp = await cli_no_redis.get("/posts/1")
    assert resp.status_code == 503


async def test_validation(
    cli_no_redis: AsyncClient
):
    # post_id validation
    resp = await cli_no_redis.get("/posts/0")
    assert resp.status_code == 422


async def test_non_existing_post(
    cli: AsyncClient
):
    resp = await cli.get("/posts/1")
    assert resp.status_code == 404


async def test_existing_post(
    data_generator: DataGenerator,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add a post to Redis
    post = data_generator.posts.post()
    redis_admin_client.add_post(post)

    # Get an existing post
    resp = await cli.get(f"/posts/{post.post_id}")
    assert resp.status_code == 200

    # Check post data
    response_post = resp.json()["post"]
    assert response_post["post_id"] == post.post_id
    assert response_post["author"] == post.author
    assert response_post["content"] == post.content
    assert datetime.fromisoformat(response_post["created_at"]) == post.created_at


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
