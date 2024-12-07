from functools import lru_cache
from typing import Any, Optional

from src.exchange.external_client_handlers.client_requests import get_search_result


# result for result in results if results["exchange"] in {"NYSE", "NASDAQ"}
class SearchHandler:

    def __init__(self, results: list = None):
        self.search_results: list = []
        for result in results:
            if result['exchange'] in {'NYSE', 'NASDAQ'} and result['country'] =='United States':  # Filter results for US stocks only
                self.search_results.append(SingleResultHandler(**result).get_modeled_result())  # Model each result
        self.paginated_results = None

    def search(self, page: int, page_size: int) -> dict[str, Any]:
        paginated_results = self.search_results[page * page_size: page * page_size + page_size]
        return {
            "total_results": len(self.search_results),
            "page": page,
            "page_size": page_size,
            "results": paginated_results
        }


class SingleResultHandler:
    def __init__(self, country: Optional[str] = None, currency: Optional[str] = None,
                 exchange: Optional[str] = None, instrument_name: Optional[str] = None,
                 symbol: Optional[str] = None, **kwargs):
        self.country = country
        self.currency = currency
        self.exchange = exchange
        self.instrument_name = instrument_name
        self.symbol = symbol

    def get_modeled_result(self):
        return {
            "country": self.country,
            "currency": self.currency,
            "exchange": self.exchange,
            "instrument_name": self.instrument_name,
            "symbol": self.symbol
        }


@lru_cache(maxsize=1000)
def get_search_handler(request: str = '') -> SearchHandler:
    return SearchHandler(get_search_result(request))
