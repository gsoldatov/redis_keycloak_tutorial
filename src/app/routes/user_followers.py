import asyncio
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.app.dependencies import get_keycloak_client, get_redis_client, get_refreshed_token, get_decoded_token
from src.app.models import Username
from src.keycloak.client import KeycloakClient
from src.redis.client import RedisClient


user_followers_router = APIRouter(prefix="/users")


@user_followers_router.put("/{username}/followers/{follower}")
async def add_follower(
    username: Username,
    follower: Username,
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
    redis_client: Annotated[RedisClient, Depends(get_redis_client)]
):
    # Validate token username
    # NOTE: username is not currently returned in the access token
    if (token_username := decoded_token.get("preferred_username", None)) is None:
        raise HTTPException(401, detail="Invalid token format: missing username.")
    elif token_username != follower:
        raise HTTPException(403, detail="Cannot add a follower to another user.")
    
    # Check if both username and follower exist
    user, follower_user = await asyncio.gather(
        redis_client.get_user(username),
        redis_client.get_user(follower)
    )
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if follower_user is None:
        raise HTTPException(status_code=404, detail="Follower user not found.")
    
    # Forbid self-following
    if username == follower:
        raise HTTPException(status_code=400, detail="Self-following is not allowed.")
    
    # Add a follower
    await redis_client.add_follower(username, follower)

    # Get user's post IDs
    post_ids = await redis_client.get_user_post_ids(username)

    # Add user's post IDs to the follower's feed
    await redis_client.add_post_ids_to_feed(follower, post_ids)

    raise HTTPException(status_code=200)
