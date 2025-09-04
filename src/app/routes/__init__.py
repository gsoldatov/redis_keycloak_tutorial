from fastapi import FastAPI
from .auth import auth_router
from .protected_test import protected_router


def setup_routes(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(protected_router)
