from typing import Any, Optional


class SingleSearchResultHandler:
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


class SearchHandler:

    def __init__(self, results: list = None):
        self.search_results: list = []
        for result in results:
            if result['exchange'] in {'NYSE', 'NASDAQ'} and result[
                'country'] == 'United States':  # Filter results for US stocks only
                self.search_results.append(
                    SingleSearchResultHandler(**result).get_modeled_result())  # Model each result
        self.paginated_results = None

    def search(self, page: int, page_size: int) -> dict[str, Any]:
        paginated_results = self.search_results[page * page_size: page * page_size + page_size]
        return {
            "total_results": len(self.search_results),
            "page": page,
            "page_size": page_size,
            "results": paginated_results
        }
