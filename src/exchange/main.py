from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.exchange.background_tasks.app_events import lifespan
from src.exchange.rate_limiter import limiter
from src.exchange.routers.auth import router as auth_router
from src.exchange.routers.info import router as info_router
from src.exchange.routers.portfolio import router as portfolio_router
from src.exchange.routers.user import router as user_router

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)
app.include_router(info_router)
app.include_router(portfolio_router)
app.include_router(user_router)


@app.get("/health", tags=["health"], include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}
