from fastapi import FastAPI
from .auth import auth_router
from .protected_test import protected_router
from .user_feed import user_feed_router
from .user_followers import user_followers_router
from .user_posts import user_posts_router
from .users import users_router
from .posts import posts_router


def setup_routes(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(protected_router)
    app.include_router(user_feed_router)
    app.include_router(user_followers_router)
    app.include_router(user_posts_router)
    app.include_router(users_router)
    app.include_router(posts_router)
