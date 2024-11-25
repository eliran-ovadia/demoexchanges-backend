from sqlalchemy.orm import Session

from src.exchange.database.models import User, MarketStatus


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
        first_stock = next(iter(quotes.values()))  # get the first element in the dict
        market.is_market_open = first_stock.get('is_market_open')  # apply to database
        db.commit()
        return first_stock.get('is_market_open')
