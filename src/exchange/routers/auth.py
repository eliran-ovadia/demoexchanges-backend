from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.Auth.oauth2 import get_raw_token
from src.exchange.database.db_conn import get_db
from src.exchange.rate_limiter import limiter
from src.exchange.routers.repository.auth_repo import get_bearer_token, refresh_tokens, logout
from src.exchange.schemas.schemas import Token, RefreshRequest, LogoutRequest

router = APIRouter(tags=['Authentication'])
check_db = Depends(get_db)


@router.post('/token')
@limiter.limit("5/minute")
async def get_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = check_db,
) -> Token:
    return await get_bearer_token(username=form_data.username, password=form_data.password, db=db)


@router.post('/refresh')
@limiter.limit("20/minute")
async def refresh(request: Request, body: RefreshRequest, db: AsyncSession = check_db) -> Token:
    return await refresh_tokens(body.refresh_token, db)


@router.post('/logout', status_code=204)
@limiter.limit("10/minute")
async def logout_user(
    request: Request,
    body: LogoutRequest = LogoutRequest(),
    access_token: str = Depends(get_raw_token),
) -> None:
    await logout(access_token, body.refresh_token)
