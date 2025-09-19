from redis import Redis
from redis.exceptions import BusyLoadingError, ConnectionError

from time import sleep
from typing import Self

from config import RedisConfig
from src.app.models import UserWithID, PostWithID
from src.redis.util import RedisKeys, get_post_id_mapping


class RedisAdminClient:
    """
    Class for performing administrative & test data operations.
    """

    def __init__(self, redis_config: RedisConfig):
        self.client = Redis(
            host="localhost",
            port=redis_config.container_port,
            db=redis_config.database,
            password=redis_config.password,

            decode_responses=True
        )
    
    def __enter__(self) -> Self:
        self.wait_for_server()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        pass

    def wait_for_server(self) -> None:
        # Wait for Redis to be ready
        max_attempts = 600
        interval = 0.1
        current_attempt = 0

        while True:
            try:
                self.client.ping()
                return
            except (BusyLoadingError, ConnectionError) as e:
                current_attempt += 1
                if current_attempt == max_attempts:
                    raise TimeoutError("Failed to await Redis server.")
                sleep(interval)

    def flush_db(self) -> None:
        """ Clears all data in the database. """
        self.client.flushdb()
    
    def set_user(self, user: UserWithID) -> None:
        self.client.hset(RedisKeys.user(user.username), mapping=user.model_dump())
    
    def get_user(self, username: str) -> UserWithID | None:
        user_data = self.client.hgetall(RedisKeys.user(username))
        return UserWithID.model_validate(user_data) if user_data else None
    
    def add_user_follower(self, username: str, follower: str) -> None:
        # Add follower to the followers list
        self.client.zadd(RedisKeys.user_followers(username), {follower: 0})

        # Add username's posts to the followers feed
        user_post_ids: list[str] = self.client.zrange(RedisKeys.user_posts(username), 0, -1)    # type: ignore
        if user_post_ids:
            self.client.zadd(RedisKeys.user_feed(follower), get_post_id_mapping(user_post_ids))
    
    def get_user_followers(self, username: str) -> list[str]:
        return self.client.zrange(
            RedisKeys.user_followers(username), 0, -1
        )   # type: ignore
    
    def add_post(self, post: PostWithID):
        # Add post data
        self.client.set(RedisKeys.post(post.post_id), post.model_dump_json())

        # Add post to the posts of author
        self.client.zadd(RedisKeys.user_posts(post.author), get_post_id_mapping(post.post_id))

        # Add post to the feeds of author followers
        followers: list[str] = self.client.zrange(RedisKeys.user_followers(post.author), 0, -1) # type: ignore
        for follower in followers:
            self.client.zadd( RedisKeys.user_feed(follower), get_post_id_mapping(post.post_id))
    
    def get_user_post_ids(self, username: str) -> list[int]:
        return [
            int(post_id) for post_id in 
            self.client.zrange(RedisKeys.user_posts(username), 0, -1)   # type: ignore
        ]
    
    def get_posts(self, post_ids: list[int]) -> list[PostWithID]:
        keys = [RedisKeys.post(post_id) for post_id in post_ids]
        posts_json: list[str] = self.client.mget(keys)  # type: ignore
        return [PostWithID.model_validate_json(post) for post in posts_json]

    def get_next_post_id(self) -> int:
        return int(
            self.client.get(RedisKeys.next_post_id) # type: ignore
        )
    
    def get_user_feed(self, username: str) -> list[int]:
        str_post_ids: list[str] = self.client.zrange(
            RedisKeys.user_feed(username), 0, -1
        )   # type: ignore
        return [int(post_id) for post_id in str_post_ids]

