from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.exchange.app_logger import logger
from src.exchange.background_tasks.fetch_market_movers.market_movers_manager import MarketMoversManager
from src.exchange.database.models import MarketStatus
from src.exchange.external_client_handlers.client_requests import get_quote
from src.exchange.external_client_handlers.client_requests import get_sentiment
from src.exchange.external_client_handlers.client_response_models.quote_handler import QuoteHandler
from src.exchange.external_client_handlers.client_response_models.search_handler import SearchHandler, \
    get_search_handler


def get_parsed_quote(request: str, db: Session) -> dict:
    raw_quotes = get_quote(request, db)
    parsed_quotes_to_return = {}

    if isinstance(raw_quotes, dict) and 'symbol' in raw_quotes:  # For single quote
        try:
            parser = QuoteHandler(**raw_quotes)
            parsed_quotes_to_return = parser.to_parsed_quote()
        except Exception as e:
            logger.error(f"Error processing single quote: {raw_quotes}. Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing stock quote"
            )
    else:  # For multiple quotes
        for symbol, raw_quote in raw_quotes.items():
            try:
                parser = QuoteHandler(**raw_quote)
                parsed_quotes_to_return[symbol] = parser.to_parsed_quote()
            except Exception as e:
                logger.warning(f"Error processing quote for symbol {symbol}. Skipping. Error: {e}")

    return parsed_quotes_to_return


def fetch_market_status(db: Session) -> MarketStatus:
    market = db.query(MarketStatus).filter(MarketStatus.exchange_name == 'NYSE').first()
    if not market:
        raise HTTPException(status_code=404, detail="Market status not found")
    return market.is_market_open


def stock_search(request: str, page: int, page_size: int):
    search_handler: SearchHandler = get_search_handler(request=request)
    return search_handler.search(page=page, page_size=page_size)


def market_movers():
    return MarketMoversManager.get_market_movers()

def stock_sentiment(symbol: str) -> dict[str, Any]:
    raw_sentiment = get_sentiment(symbol)
    if not raw_sentiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sentiment not found for {symbol}")
    return raw_sentiment[0]
