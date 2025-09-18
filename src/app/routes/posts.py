from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.app.dependencies import get_redis_client
from src.app.models import PostID
from src.redis.client import RedisClient


posts_router = APIRouter(prefix="/posts")


@posts_router.get("/{post_id}")
async def get_post(
    post_id: PostID,
    redis_client: Annotated[RedisClient, Depends(get_redis_client)]
):
    # Get post from Redis
    post = await redis_client.get_post(post_id)
    
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    return {"post": post}
