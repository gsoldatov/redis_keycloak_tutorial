import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Annotated

from src.app.dependencies import get_redis_client, get_decoded_token
from src.app.models import Username, NewPost, Post, PaginationCursor
from src.redis.client import RedisClient


user_posts_router = APIRouter(prefix="/users")


@user_posts_router.post("/{username}/posts")
async def add_post(
    username: Username,
    new_post: NewPost,
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
    redis_client: Annotated[RedisClient, Depends(get_redis_client)]
):
    # Validate token username
    # NOTE: username is not currently returned in the access token
    if (token_username := decoded_token.get("preferred_username", None)) is None:
        raise HTTPException(401, detail="Invalid token format: missing username.")
    elif token_username != username:
        raise HTTPException(403, detail="Cannot add a post to another user.")
        
    # Add a post
    post = Post.model_validate({
        **new_post.model_dump(),
        "created_at": datetime.now(tz=timezone.utc),
        "author": username
    })
    post_with_id = await redis_client.add_new_post(post)

    # Add post to the followers' feeds
    await redis_client.add_post_to_followers_feeds(post_with_id)
    
    # Return new post in response
    return JSONResponse(status_code=201, content={"post": post_with_id.model_dump()})


@user_posts_router.get("/{username}/posts")
async def get_posts(
    username: Username,
    redis_client: Annotated[RedisClient, Depends(get_redis_client)],
    last_viewed: Annotated[PaginationCursor | None, Query()] = None
):
    # Check if user exists
    user = await redis_client.get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Get paginated user posts
    posts = await redis_client.get_paginated_user_posts(username, last_viewed)

    if not posts:
        raise HTTPException(status_code=404, detail="Posts not found.")
    
    return JSONResponse(content={"posts": [post.model_dump() for post in posts]})
