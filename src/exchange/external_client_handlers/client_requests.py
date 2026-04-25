from fastapi import HTTPException, status

from .client_manager import ClientManager
from ..app_logger import logger
from ..schemas.fmp_schemas import QuoteSchema


def _to_quote_schema(raw: dict) -> QuoteSchema:
    """Map one FMP /quote object to our internal QuoteSchema."""
    return QuoteSchema(
        symbol=raw.get("symbol", ""),
        name=raw.get("name", ""),
        exchange=raw.get("exchange", ""),
        currency="USD",
        price=float(raw.get("price") or 0.0),
        open=float(raw.get("open") or 0.0),
        high=float(raw.get("dayHigh") or 0.0),
        low=float(raw.get("dayLow") or 0.0),
        previous_close=float(raw.get("previousClose") or 0.0),
        change=float(raw.get("change") or 0.0),
        percent_change=float(raw.get("changesPercentage") or 0.0),
        volume=int(raw.get("volume") or 0),
        avg_volume=int(raw.get("avgVolume") or 0),
        year_high=float(raw.get("yearHigh") or 0.0),
        year_low=float(raw.get("yearLow") or 0.0),
    )


def fetch_stock_price(symbol: str) -> float:
    fmp = ClientManager.get_client()
    data = fmp.get(endpoint="quote-short",params={"symbol": symbol})
    if not data:
        logger.critical(f"Price not found for symbol: {symbol}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Price for symbol {symbol} not found")
    return float(data[0].get("price") or 0.0)


def fetch_quote(symbols: str) -> dict[str, QuoteSchema]:
    """Always returns {symbol: QuoteSchema} — same shape for one or many symbols."""
    fmp = ClientManager.get_client()
    endpoint = "batch-quote" if "," in symbols else "quote" # Backup because we use the starter plan so we do not have access to batch-quote
    data = fmp.get(endpoint=endpoint, params={"symbol": symbols})
    if not data:
        logger.error(f"Quote not found for symbols: {symbols}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Quote for {symbols} not found")
    return {item["symbol"]: _to_quote_schema(item) for item in data}


def fetch_search(prompt: str, output_size: int = 50) -> list[dict]:
    fmp = ClientManager.get_client()
    data = fmp.get("search-symbol", params={"query": prompt, "limit": output_size})
    if not data:
        logger.critical(f"Search failed for prompt: {prompt}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No results for search: {prompt}")
    return data


def fetch_sentiment(symbol: str) -> dict:
    fmp = ClientManager.get_client()
    data = fmp.get("grades-consensus", params={"symbol": symbol})
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No sentiment data for this symbol")
    return data[0]


def fetch_all_stocks() -> list:
    """Returns NYSE/NASDAQ stocks normalized to the UsStocks model field shape."""
    fmp = ClientManager.get_client()
    try:
        data = fmp.get("stock/list")
    except Exception as e:
        logger.error(f"Failed to fetch stock list: {e}")
        return []
    return [
        {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "currency": "",
            "exchange": item.get("exchangeShortName", ""),
            "mic_code": "",
            "country": "United States",
            "type": item.get("type", ""),
            "figi_code": "",
        }
        for item in (data or [])
        if item.get("exchangeShortName") in {"NYSE", "NASDAQ"}
        and item.get("type") == "stock"
    ]


def fetch_market_movers() -> dict:
    fmp = ClientManager.get_client()
    data = fmp.get(endpoint="most-actives")
    if not data:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Market movers unavailable")
    stocks = [
        {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "price": item.get("price"),
            "change": item.get("change"),
            "percent_change": item.get("changesPercentage", ""),
        }
        for item in data
    ]
    return {"stocks": stocks}


def fetch_market_status() -> dict:
    fmp = ClientManager.get_client()
    data = fmp.get(endpoint="exchange-market-hours", params={"exchange": "NASDAQ"})[0]
    if not isinstance(data, dict):
        logger.critical("Unexpected response from FMP market-status endpoint")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Market status unavailable")
    return data


def fetch_splits_calendar(from_date: str, to_date: str) -> list:
    """Returns all stock splits in the given date range across all tickers."""
    fmp = ClientManager.get_client()
    try:
        # "from" is a Python keyword — must be passed via explicit dict
        data = fmp.get("stock-split-calendar", params={"from": from_date, "to": to_date})
    except Exception as e:
        logger.error(f"Failed to fetch splits calendar {from_date} → {to_date}: {e}")
        return []
    return data or []
