import traceback
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable

from src.exceptions import KeycloakConnectionException, RedisConnectionException, \
    InvalidOperationException, UnauthorizedOperationException, ForbiddenOperationException
from src.util.logging import log


async def error_middleware(
    request: Request,
    call_next: Callable[[Request],
    Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    
    except InvalidOperationException as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    
    except UnauthorizedOperationException as e:
        return JSONResponse(status_code=401, content={"detail": str(e)})
    
    except ForbiddenOperationException as e:
        return JSONResponse(status_code=403, content={"detail": str(e)})
    
    except (KeycloakConnectionException, RedisConnectionException) as e:
        log(e)
        return Response(status_code=503)
    
    except Exception as e:
        log(f"{str(e)}\n{traceback.format_exc()}")
        return Response(status_code=500)


def setup_middleware(app: FastAPI) -> None:
    app.middleware("http")(error_middleware)
