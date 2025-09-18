"""
DELETE /users/:username/followers/:follower route tests.
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
    data_generator: DataGenerator,
    cli_no_kc_and_redis: AsyncClient
):
    headers = data_generator.auth.get_bearer_header_with_invalid_token()
    resp = await cli_no_kc_and_redis.delete("/users/username/followers/follower", headers=headers)
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

    # Try to remove a follower
    headers = data_generator.auth.get_bearer_header(access_token)
    resp = await cli_no_redis.delete("/users/other_username/followers/username", headers=headers)

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
    # Username validation

    headers = data_generator.auth.get_bearer_header(access_token)
    resp = await cli_no_redis.delete("/users/a/followers/follower", headers=headers)
    assert resp.status_code == 422

    # Follower validation
    resp = await cli_no_redis.delete("/users/username/followers/a", headers=headers)
    assert resp.status_code == 422


async def test_invalid_token(
    data_generator: DataGenerator,
    cli_no_redis: AsyncClient
):
    headers = data_generator.auth.get_bearer_header_with_invalid_token()
    resp = await cli_no_redis.delete("/users/username/followers/follower", headers=headers)
    assert resp.status_code == 401


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

    # Try to add a follower to the second user
    headers = data_generator.auth.get_bearer_header(access_token)
    resp = await cli.delete("/users/some_user/followers/second_user", headers=headers)

    assert resp.status_code == 403


async def test_non_existing_username(
        data_generator: DataGenerator,
        keycloak_admin_client: KeycloakAdminClient,
        redis_admin_client: RedisAdminClient,
        cli: AsyncClient
):
    # Add a user to Keycloak & Redis
    keycloak_admin_client.add_user()
    redis_admin_client.set_user(data_generator.users.redis_user_data())

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Try to unfollow a non-existing user
    headers = data_generator.auth.get_bearer_header(access_token)
    resp = await cli.delete("/users/non-existing/followers/username", headers=headers)

    assert resp.status_code == 404


async def test_self_unfollowing(
        data_generator: DataGenerator,
        keycloak_admin_client: KeycloakAdminClient,
        redis_admin_client: RedisAdminClient,
        cli: AsyncClient
):
    # Add a user to Keycloak & Redis
    keycloak_admin_client.add_user()
    redis_admin_client.set_user(data_generator.users.redis_user_data())

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body()
    login_resp = await cli.post("/auth/login", json=body)
    
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Try to follow self
    headers = data_generator.auth.get_bearer_header(access_token)
    resp = await cli.delete("/users/username/followers/username", headers=headers)

    assert resp.status_code == 400


async def test_remove_followers_followers_set(
        data_generator: DataGenerator,
        keycloak_admin_client: KeycloakAdminClient,
        redis_admin_client: RedisAdminClient,
        cli: AsyncClient
):
    # Add users
    followed, first_follower, second_follower, third_follower = "followed", "first_follower", "second_follower", "third_follower"
    for username in (followed, first_follower, second_follower):
        keycloak_admin_client.add_user(username=username)
        redis_admin_client.set_user(data_generator.users.redis_user_data(username=username))
    
    # Add followers
    for follower in (first_follower, second_follower, third_follower):
        redis_admin_client.add_user_follower(followed, follower)

    # Log in & unfollow with different users
    for follower in (first_follower, second_follower):
        # Log in as a user
        body = data_generator.auth.get_auth_login_request_body(username=follower)
        login_resp = await cli.post("/auth/login", json=body)
        
        assert login_resp.status_code == 200
        access_token = login_resp.json()["access_token"]

        # Unfollow a user
        headers = data_generator.auth.get_bearer_header(access_token)
        resp = await cli.delete(f"/users/{followed}/followers/{follower}", headers=headers)

        assert resp.status_code == 200
    
    # Check if followed user has correct followers
    assert redis_admin_client.get_user_followers(followed) == [third_follower]


async def test_remove_unfollowed(
        data_generator: DataGenerator,
        keycloak_admin_client: KeycloakAdminClient,
        redis_admin_client: RedisAdminClient,
        cli: AsyncClient
):
    # Add users
    followed, follower, not_a_follower = "followed", "follower", "not_a_follower"
    for username in (followed, follower, not_a_follower):
        keycloak_admin_client.add_user(username=username)
        redis_admin_client.set_user(data_generator.users.redis_user_data(username=username))
    
    # Add an existing follower
    redis_admin_client.add_user_follower(followed, follower)

    # Log in as a user
    body = data_generator.auth.get_auth_login_request_body(username=not_a_follower)
    login_resp = await cli.post("/auth/login", json=body)

    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Unfollow a not followed user
    headers = data_generator.auth.get_bearer_header(access_token)
    resp = await cli.delete(f"/users/{followed}/followers/{not_a_follower}", headers=headers)

    assert resp.status_code == 200
    
    # Check if followed user has correct followers
    assert redis_admin_client.get_user_followers(followed) == [follower]


async def test_remove_followers_follower_feed(
        data_generator: DataGenerator,
        keycloak_admin_client: KeycloakAdminClient,
        redis_admin_client: RedisAdminClient,
        cli: AsyncClient
):
    # Add users
    follower, first_followed, second_followed, third_followed = "follower", "first_followed", "second_followed", "third_followed"
    for username in (follower, first_followed, second_followed):
        keycloak_admin_client.add_user(username=username)
        redis_admin_client.set_user(data_generator.users.redis_user_data(username=username))
    
    # Adds posts of followers
    redis_admin_client.add_post(data_generator.posts.post(post_id=1, author=first_followed))
    redis_admin_client.add_post(data_generator.posts.post(post_id=2, author=second_followed))
    redis_admin_client.add_post(data_generator.posts.post(post_id=3, author=third_followed))
    redis_admin_client.add_post(data_generator.posts.post(post_id=4, author=first_followed))
    redis_admin_client.add_post(data_generator.posts.post(post_id=5, author=second_followed))
    redis_admin_client.add_post(data_generator.posts.post(post_id=6, author=third_followed))

    # Add followers
    for followed in (first_followed, second_followed, third_followed):
        redis_admin_client.add_user_follower(followed, follower)
    
    # Log in as a follower
    body = data_generator.auth.get_auth_login_request_body(username=follower)
    login_resp = await cli.post("/auth/login", json=body)

    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Unfollow 2 users
    for followed in (first_followed, second_followed):
        headers = data_generator.auth.get_bearer_header(access_token)
        resp = await cli.delete(f"/users/{followed}/followers/{follower}", headers=headers)

        assert resp.status_code == 200
    
    # Check if posts of unfollowed users were correctly removed from the follower's feed
    assert redis_admin_client.get_user_feed(follower) == [3, 6]


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
