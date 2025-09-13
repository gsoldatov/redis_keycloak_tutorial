from redis.asyncio import Redis
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

from src.app.models import User
from src.exceptions import RedisConnectionException
from src.redis.util import RedisKeys


REDIS_LIB_CONNECTION_EXCEPTIONS = (BusyLoadingError, ConnectionError, TimeoutError)


class RedisClient:
    def __init__(self, client: Redis):
        self.client = client
    
    async def set_user(
        self, user_id: str, user: User) -> None:
        """ Adds properties from Keycloak UserRepresentation `data` to Redis. """
        try:
            await self.client.hset(
                RedisKeys.user(user.username),
                mapping={
                    "user_id": user_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            ) # type: ignore (async client is not fully typed: https://github.com/redis/redis-py/issues/3169)
        except REDIS_LIB_CONNECTION_EXCEPTIONS as e:
            raise RedisConnectionException from e

