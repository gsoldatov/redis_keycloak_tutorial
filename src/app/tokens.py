from datetime import datetime
from functools import wraps
from redis.asyncio import Redis

from src.exceptions import RedisConnectionException
from src.redis.client import REDIS_LIB_CONNECTION_EXCEPTIONS
from src.redis.util import RedisKeys
from src.util.logging import log


class TokenCache:
    """ In-memory access/refresh token cache. """
    def __init__(self):
        self._store: dict[str, str] = {}
    
    async def add(self, tokens: dict) -> None:
        """ Adds access & refresh tokens to the storage. """
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        self._store[access_token] = refresh_token
    
    async def get(self, access_token: str) -> str | None:
        """ Returns the refresh token for the provided `access_token` or None. """
        return self._store.get(access_token, None)

    async def pop(self, access_token: str) -> str | None:
        """ Pops the refresh token for the provided `access_token` from the storage. """
        return self._store.pop(access_token, None)
    
    async def contains(self, access_token: str) -> bool:
        return access_token in self._store


def handle_redis_connection_errors(raise_on_error: bool = False):
    def outer(fn):
        @wraps(fn)
        async def inner(self: "RedisTokenCache", *args, **kwargs):
            """ Runs a RedisTokenCache method & handles connection exceptions. """
            try:
                return await fn(self, *args, **kwargs)
            except REDIS_LIB_CONNECTION_EXCEPTIONS as e:
                log(e)
                if raise_on_error:
                    raise RedisConnectionException from e
        
        return inner
    return outer


class RedisTokenCache:
    """"""
    def __init__(self, client: Redis):
        self.client = client
    
    @handle_redis_connection_errors()
    async def add(self, tokens: dict) -> None:
        """ Adds access & refresh tokens to the storage. """
        await self.client.setex(
            RedisKeys.access_token(tokens["access_token"]),
            tokens["refresh_expires_in"],
            tokens["refresh_token"]
        )
    
    # Raise in case of connection issues to indicate
    # that a token could not be retrieved, but may be present
    # (so that /auth/logout does not return a successful response,
    # despite an actual logout not being performed)
    @handle_redis_connection_errors(raise_on_error=True)
    async def get(self, access_token: str) -> str | None:
        """ Returns the refresh token for the provided `access_token` or None. """
        return await self.client.get(RedisKeys.access_token(access_token))

    @handle_redis_connection_errors()
    async def pop(self, access_token: str) -> str | None:
        """ Pops the refresh token for the provided `access_token` from the storage. """
        return await self.client.getdel(RedisKeys.access_token(access_token))
    
    @handle_redis_connection_errors()
    async def contains(self, access_token: str) -> bool:
        return await self.client.exists(RedisKeys.access_token(access_token))
