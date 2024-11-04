from exchange.models import User, MarketStatus
from sqlalchemy.orm import Session
from ....app_logger import logger
from fastapi import HTTPException, status
import os


def find_user(db: Session, user_id: str = None, email: str = None) -> User | bool:
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif email:
        user = db.query(User).filter(User.email == email).first()
    else:
        raise ValueError("Either user_id or email must be provided.")

    if not user:
        return False

    return user


def market_status_update(quotes: dict, db: Session) -> bool:
    market = db.query(MarketStatus).filter(MarketStatus.exchange_name == 'NYSE').first()
    if 'is_market_open' in quotes:
        market.is_market_open = quotes.get('is_market_open')
        db.commit()
        return quotes.get('is_market_open')
    else:
        first_stock = next(iter(quotes.values())) # get the first element in the dict
        market.is_market_open = first_stock.get('is_market_open') # apply to database
        db.commit()
        return first_stock.get('is_market_open')


def get_api_key(client: str) -> str:
    api_key = os.getenv(client)
    if not api_key:
        logger.error(f"API key for {client} is not set.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API key for {client} is missing"
        )

    return api_key