"""
POST /users/:username/posts route tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from datetime import datetime, timezone, timedelta
from httpx import AsyncClient

from src.keycloak.admin import KeycloakAdminClient
from src.redis.admin import RedisAdminClient
from tests.data_generators import DataGenerator


async def test_keycloak_network_error(
    data_generator: DataGenerator,
    cli_no_kc_and_redis: AsyncClient
):
    headers = data_generator.auth.get_bearer_header_with_invalid_token()
    body = data_generator.posts.new_post_request_body()
    resp = await cli_no_kc_and_redis.post("/users/username/posts", json=body, headers=headers)
    assert resp.status_code == 503


async def test_redis_network_error(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    cli_no_redis: AsyncClient
):
    # Add a user to Keycloak
    user_id = keycloak_admin_client.add_user()

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli_no_redis.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Try to add a post
    headers = data_generator.auth.get_bearer_header(access_token)
    body = data_generator.posts.new_post_request_body()
    resp = await cli_no_redis.post("/users/username/posts", json=body, headers=headers)

    assert resp.status_code == 503


async def test_validation(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    cli_no_redis: AsyncClient
):
    # Add a user to Keycloak
    user_id = keycloak_admin_client.add_user()

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli_no_redis.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Post validation
    headers = data_generator.auth.get_bearer_header(access_token)
    body = data_generator.posts.new_post_request_body()
    body["content"] = ""
    resp = await cli_no_redis.post("/users/username/posts", json=body, headers=headers)
    assert resp.status_code == 422

    # Username validation
    body = data_generator.posts.new_post_request_body()
    resp = await cli_no_redis.post("/users/a/posts", json=body, headers=headers)
    assert resp.status_code == 422


async def test_invalid_token(
    data_generator: DataGenerator,
    cli_no_redis: AsyncClient
):
    headers = data_generator.auth.get_bearer_header_with_invalid_token()
    body = data_generator.posts.new_post_request_body()
    resp = await cli_no_redis.post("/users/username/posts", json=body, headers=headers)
    assert resp.status_code == 401


async def test_token_without_can_post_role(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    cli_no_redis: AsyncClient
):
    # Add a user without can-post role to Keycloak
    keycloak_admin_client.add_user(app_client_roles=[])

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli_no_redis.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Try to add a post
    headers = data_generator.auth.get_bearer_header(access_token)
    body = data_generator.posts.new_post_request_body()
    resp = await cli_no_redis.post("/users/username/posts", json=body, headers=headers)
    assert resp.status_code == 403


async def test_token_of_another_user(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    cli: AsyncClient
):
    # Add users to Keycloak
    keycloak_admin_client.add_user(username="first_user")
    keycloak_admin_client.add_user(username="second_user")

    # Log in as first user
    body = data_generator.auth.get_auth_login_request_body(username="first_user")
    login_resp = await cli.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Try to add a post for the second user
    headers = data_generator.auth.get_bearer_header(access_token)
    body = data_generator.posts.new_post_request_body()
    resp = await cli.post("/users/second_user/posts", json=body, headers=headers)

    assert resp.status_code == 403


async def test_add_posts_response_and_posts_data(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add a user
    keycloak_admin_client.add_user()
    redis_admin_client.set_user(data_generator.users.redis_user_data())

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Add new posts
    for i in range(1, 4):
        headers = data_generator.auth.get_bearer_header(access_token)
        content = f"post {i}"
        body = data_generator.posts.new_post_request_body(content=content)
        resp = await cli.post("/users/username/posts", json=body, headers=headers)
        
        assert resp.status_code == 201
        
        # Check response & db post data
        response_post = resp.json()["post"]
        db_post = redis_admin_client.get_posts([i])[0]

        assert response_post["post_id"] == db_post.post_id == i
        assert response_post["content"] == db_post.content == content
        assert response_post["author"] == db_post.author == "username"
        
        now = datetime.now(tz=timezone.utc)
        response_created_at = datetime.fromisoformat(response_post["created_at"])
        assert now - timedelta(seconds=1) < response_created_at < now + timedelta(seconds=1)
        assert db_post.created_at == response_created_at
    
    # Check next_post_id
    assert redis_admin_client.get_next_post_id() == 3


async def test_add_posts_author_post_ids(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add a user
    keycloak_admin_client.add_user()
    redis_admin_client.set_user(data_generator.users.redis_user_data())

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Add new posts
    for i in range(1, 4):
        headers = data_generator.auth.get_bearer_header(access_token)
        content = f"post {i}"
        body = data_generator.posts.new_post_request_body(content=content)
        resp = await cli.post("/users/username/posts", json=body, headers=headers)
        
        assert resp.status_code == 201
    
    # Check if user posts have correct post IDs
    assert redis_admin_client.get_user_post_ids("username") == [3, 2, 1]


async def test_add_posts_followers_feeds(
    data_generator: DataGenerator,
    keycloak_admin_client: KeycloakAdminClient,
    redis_admin_client: RedisAdminClient,
    cli: AsyncClient
):
    # Add users
    first_followed, second_followed = "first_followed", "second_followed"
    first_follower, second_follower = "first_follower", "second_follower"
    for username in (first_followed, second_followed, first_follower, second_follower):
        keycloak_admin_client.add_user(username=username)
        redis_admin_client.set_user(data_generator.users.redis_user_data(username=username))
    
    # Add followers
    redis_admin_client.add_user_follower(first_followed, first_follower)
    redis_admin_client.add_user_follower(first_followed, second_follower)
    redis_admin_client.add_user_follower(second_followed, first_follower)

    # Add posts as 2 followed users
    for username, post_ids in [(first_followed, [1, 2]), (second_followed, [3, 4])]:
        # Log in as a user
        body = data_generator.auth.get_auth_login_request_body(username=username)
        login_resp = await cli.post("/auth/login", json=body)
        
        assert login_resp.status_code == 200
        access_token = login_resp.json()["access_token"]

        # Add posts
        for post_id in post_ids:
            headers = data_generator.auth.get_bearer_header(access_token)
            content = f"post {post_id}"
            body = data_generator.posts.new_post_request_body(content=content)
            resp = await cli.post(f"/users/{username}/posts", json=body, headers=headers)
            
            assert resp.status_code == 201
    
    # Check if posts were added to the followers' feeds correctly
    assert redis_admin_client.get_user_feed(first_follower) == [4, 3, 2, 1]
    assert redis_admin_client.get_user_feed(second_follower) == [2, 1]


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
