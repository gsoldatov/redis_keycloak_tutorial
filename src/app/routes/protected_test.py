from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.app.dependencies import validate_token_role


protected_router = APIRouter(prefix="/protected_test")


@protected_router.get("/first")
async def protected_first(
    valid_token: Annotated[None, Depends(validate_token_role("role-1"))]
):
    return {"value": 1}


@protected_router.get("/second")
async def protected_second(
    valid_token: Annotated[None, Depends(validate_token_role("role-2"))]
):
    return {"value": 2}
