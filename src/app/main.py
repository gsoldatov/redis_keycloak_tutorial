import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncIterator

from config import load_config, Config
from src.app.routes import router


def get_lifespan(config: Config):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.config = config
        yield
    return lifespan


def create_app(config: Config) -> FastAPI:
    app = FastAPI(lifespan=get_lifespan(config))
    app.include_router(router, prefix="")
    return app


config = load_config()
app = create_app(config)
