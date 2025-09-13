from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.app.dependencies import get_redis_client
from src.app.models import Username
from src.redis.client import RedisClient


users_router = APIRouter(prefix="/users")


@users_router.get("/{username}")
async def get_user(
    username: Username,
    redis_client: Annotated[RedisClient, Depends(get_redis_client)]
):
    user = await redis_client.get_user(username)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    
    return user
