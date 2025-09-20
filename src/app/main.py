import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncIterator
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.asyncio.retry import Retry
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

from config import load_config, Config
from src.app.middleware import setup_middleware
from src.app.routes import setup_routes
from src.app.tokens import RedisTokenCache


def get_lifespan(config: Config):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        redis: Redis | None = None
        try:
            # Config
            app.state.config = config

            # Setup Redis client
            redis = Redis(
                # Redis location & credentials
                host="localhost",
                port=config.redis.container_port,
                db=config.redis.database,
                password=config.redis.password,

                # Connection settings
                max_connections=config.redis.max_connections,
                socket_timeout=config.redis.socket_timeout,
                socket_connect_timeout=config.redis.socket_timeout,
                
                decode_responses=True,

                # Retry strategy & exceptions
                retry=Retry(
                    ExponentialBackoff(
                        base=config.redis.retry_base_time,
                        cap=config.redis.retry_cap_time,
                    ),
                    config.redis.number_of_retries
                ),
                retry_on_error=[BusyLoadingError, ConnectionError, TimeoutError]
            )
            app.state.redis = redis

            # Refresh token cache
            app.state.token_cache = RedisTokenCache(redis)
            
            yield
        
        finally:
            # Cleanup Redis connection pool (explicit close required for async client)
            if redis is not None:
                await redis.aclose()

    return lifespan


def create_app(config: Config) -> FastAPI:
    app = FastAPI(lifespan=get_lifespan(config))
    setup_routes(app)
    setup_middleware(app)
    return app


config = load_config()
app = create_app(config)
