from functools import wraps

from redis.asyncio import Redis
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

from src.app.models import User, UserPublic
from src.exceptions import RedisConnectionException
from src.redis.util import RedisKeys


REDIS_LIB_CONNECTION_EXCEPTIONS = (BusyLoadingError, ConnectionError, TimeoutError)


def handle_redis_connection_errors(fn):
    @wraps(fn)
    async def inner(self: "RedisClient", *args, **kwargs):
        """ Runs a Redis client method & handles connection exceptions. """
        try:
            return await fn(self, *args, **kwargs)
        except REDIS_LIB_CONNECTION_EXCEPTIONS as e:
            raise RedisConnectionException from e
    
    return inner


class RedisClient:
    def __init__(self, client: Redis):
        self.client = client
    
    @handle_redis_connection_errors
    async def set_user(
        self, user_id: str, user: User) -> None:
        """ Adds properties from Keycloak UserRepresentation `data` to Redis. """
        await self.client.hset(
            RedisKeys.user(user.username),
            mapping={
                "user_id": user_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        ) # type: ignore (async client is not fully typed: https://github.com/redis/redis-py/issues/3169)

    @handle_redis_connection_errors
    async def get_user(self, username: str) -> UserPublic | None:
        """ Returns public attributes of a user with provided `username`, if he exists. """
        print("IN get_user")
        user_data = await self.client.hgetall(RedisKeys.user(username)) # type: ignore
        print(f"user_data = {user_data}")
        return UserPublic.model_validate(user_data) if user_data else None
