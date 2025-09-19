from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Annotated

from src.app.dependencies import get_redis_client
from src.app.models import Username, PaginationCursor
from src.redis.client import RedisClient


user_feed_router = APIRouter(prefix="/users")


@user_feed_router.get("/{username}/feed")
async def get_user_feed(
    username: Username,
    redis_client: Annotated[RedisClient, Depends(get_redis_client)],
    last_viewed: Annotated[PaginationCursor | None, Query()] = None
):
    # Check if user exists
    user = await redis_client.get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Get paginated user feed posts
    posts = await redis_client.get_paginated_user_feed(username, last_viewed)

    if not posts:
        raise HTTPException(status_code=404, detail="Posts not found.")
    
    return JSONResponse(content={"posts": [post.model_dump() for post in posts]})
