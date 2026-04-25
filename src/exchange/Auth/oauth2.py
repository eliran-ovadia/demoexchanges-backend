from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.exchange.Auth.token_functions import verify_token
from src.exchange.redis_manager import RedisManager
from src.exchange.schemas.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="Token")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    token_data, jti = verify_token(token, _CREDENTIALS_EXCEPTION)
    if await RedisManager.get_client().is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


async def get_raw_token(token: str = Depends(oauth2_scheme)) -> str:
    """Returns the raw JWT string — used by logout to blacklist it."""
    return token
