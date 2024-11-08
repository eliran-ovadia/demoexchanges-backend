import requests

from exchange.app_logger import logger as log
from exchange.clients_methods import get_search_result, get_sentiment
from exchange.routers.repository.utils.get_portfolio_utils import *
from exchange.routers.repository.utils.process_raw_quote import process_single_quote
from .utils.utils import get_api_key


def get_parsed_quote(request: str, db: Session) -> dict:
    raw_quotes = get_quote(request, db)

    parsed_quotes_to_return = {}
    if 'symbol' in raw_quotes:  # Check for single dictionary
        parsed_quotes_to_return = process_single_quote(raw_quotes)
    else:
        for symbol, raw_quote in raw_quotes.items():
            parsed_quote = process_single_quote(raw_quote)
            parsed_quotes_to_return[symbol] = parsed_quote

    return parsed_quotes_to_return


def fetch_market_status(db: Session) -> MarketStatus:
    market = db.query(MarketStatus).filter(MarketStatus.exchange_name == 'NYSE').first()
    if not market:
        raise HTTPException(status_code=404, detail="Market status not found")
    return market.is_market_open


def stock_search(prompt: str, page: int, page_size: int) -> Dict[str, Any]:
    unfiltered_results = get_search_result(prompt)

    filtered_results = [result for result in unfiltered_results if
                        result["exchange"] == "NYSE" or result["exchange"] == "NASDAQ"]

    total_results = len(filtered_results)

    return {"total_results": total_results,
            "page": page,
            "page_size": page_size,
            "results": filtered_results[(page - 1) * page_size: page * page_size]
            }


def market_movers():
    api_key = get_api_key("ALPHA_VANTAGE_API_KEY")
    url = f'https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status() #raise if not 200
        json_response = response.json()

    except requests.exceptions.RequestException as e:
        log.error(f"alphavantage TOP_GAINERS_LOSERS call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot access market movers at the moment"
        )

    if 'most_actively_traded' not in json_response or 'last_updated' not in json_response:
        log.critical("alphavantage TOP_GAINERS_LOSERS call is not containing *most_actively_traded* or *last_updated* no more")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot access market movers at the moment"
        )

    useful_data = {
        'last_updated': json_response['last_updated'],
        'stocks': sorted([stock for stock in json_response['most_actively_traded'] if float(stock['price']) > 1],
            key=lambda x: int(x['volume']),
            reverse=True
        )
    }

    return useful_data


def stock_sentiment(symbol: str) -> Dict[str, Any]:
    raw_sentiment = get_sentiment(symbol)
    if not raw_sentiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sentiment not found for {symbol}")
    return raw_sentiment[0]