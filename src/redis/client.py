from functools import wraps

from redis.asyncio import Redis
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

from src.app.models import User, UserPublic, PostWithID, Post
from src.exceptions import RedisConnectionException
from src.redis.util import RedisKeys, get_post_id_mapping


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
        user_data = await self.client.hgetall(RedisKeys.user(username)) # type: ignore
        return UserPublic.model_validate(user_data) if user_data else None

    @handle_redis_connection_errors
    async def add_follower(self, username: str, follower: str) -> None:
        """ Adds a `follower` to the followers sorted set of a `username`. """
        await self.client.zadd(
            RedisKeys.user_followers(username),
            {follower: 0}
        ) # type: ignore
    
    @handle_redis_connection_errors
    async def get_paginated_user_followers(self, username: str, last_viewed: int | None) -> list[str]:
        start = last_viewed + 1 if last_viewed is not None else 0
        end = start + 4    # 5 per page
        return await self.client.zrange(RedisKeys.user_followers(username), start, end)
    
    @handle_redis_connection_errors
    async def remove_follower(self, username: str, follower: str) -> None:
        """ Removes a `follower` from the followers sorted set of a `username`. """
        await self.client.zrem(
            RedisKeys.user_followers(username),
            follower
        ) # type: ignore
    
    @handle_redis_connection_errors
    async def add_new_post(self, post: Post) -> PostWithID:
        """ Saves a new post in the database. """
        # Get post ID of the new post
        post_id = await self.client.incr(RedisKeys.next_post_id, amount=1)
        
        # Set post data
        added_post = PostWithID.model_validate({**post.model_dump(), "post_id": post_id})
        await self.client.set(RedisKeys.post(post_id), added_post.model_dump_json())

        # Add post to author's list of posts
        await self.client.zadd(RedisKeys.user_posts(post.author), get_post_id_mapping(post_id))
        
        # Return ID of new post
        return added_post

    @handle_redis_connection_errors
    async def get_post(self, post_id: int) -> PostWithID | None:
        """ Returns a post with the provided `post_id`, if it exists. """
        post_data = await self.client.get(RedisKeys.post(post_id))
        return PostWithID.model_validate_json(post_data) if post_data else None

    @handle_redis_connection_errors
    async def get_paginated_user_posts(self, username: str, last_viewed: int | None) -> list[PostWithID]:
        """ Returns a paginated list of posts of `username` after `last_viewed` or from start. """
        start = last_viewed + 1 if last_viewed is not None else 0
        end = start + 4     # 5 per page
        post_ids: list[str] = await self.client.zrange(RedisKeys.user_posts(username), start, end)
        if post_ids:
            posts_data = await self.client.mget([RedisKeys.post(post_id) for post_id in post_ids])
            return [PostWithID.model_validate_json(post) for post in posts_data]
        else:
            return []
    
    @handle_redis_connection_errors
    async def get_user_post_ids(self, username: str) -> list[str]:
        """ Returns a list of post IDs authored by `username`. """
        return await self.client.zrange(RedisKeys.user_posts(username), 0, -1)  # type: ignore
    
    # @handle_redis_connection_errors
    # async def get_user_posts(self, username: str) -> list[PostWithID]:
    #     """ Returns a list of posts authored by `username`. """
    #     post_ids = await self.client.lrange(RedisKeys.user_posts(username), 0, -1)  # type: ignore
    #     if not post_ids: return []

    #     keys = (RedisKeys.post(post_id) for post_id in post_ids)
    #     return [PostWithID.model_validate_json(value) for value in await self.client.mget(keys)]

    @handle_redis_connection_errors
    async def add_post_to_followers_feeds(self, post: PostWithID) -> None:
        """ Adds a `post` IDs to the feeds of its author's followers. """
        followers = await self.client.zrange(RedisKeys.user_followers(post.author), 0, -1)
        if followers:
            pipe = self.client.pipeline()
            post_id_mapping = get_post_id_mapping(post.post_id)
            for follower in followers:
                pipe.zadd(RedisKeys.user_feed(follower), post_id_mapping)
            await pipe.execute()
    
    @handle_redis_connection_errors
    async def add_post_ids_to_feed(self, username: str, post_ids: list[int] | list[str]) -> None:
        """ Adds `post_ids` to the feed of a user with `username`. """
        if not post_ids: return
        await self.client.zadd( RedisKeys.user_feed(username), get_post_id_mapping(post_ids))
    
    @handle_redis_connection_errors
    async def remove_post_ids_from_feed(self, username: str, post_ids: list[int] | list[str]) -> None:
        """ Removes `post_ids` from the feed of a user with `username`. """
        if not post_ids: return
        removed_post_ids = [str(post_id) for post_id in post_ids]
        await self.client.zrem( RedisKeys.user_feed(username), *removed_post_ids)
