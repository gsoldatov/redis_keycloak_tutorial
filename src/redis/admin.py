from redis import Redis
from redis.exceptions import BusyLoadingError, ConnectionError

from time import sleep
from typing import Self

from config import RedisConfig
from src.app.models import UserWithID
from src.redis.util import RedisKeys


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
    
    def get_user(self, username: str) -> UserWithID | None:
        user_data = self.client.hgetall(RedisKeys.user(username))
        return UserWithID.model_validate(user_data) if user_data else None
    

