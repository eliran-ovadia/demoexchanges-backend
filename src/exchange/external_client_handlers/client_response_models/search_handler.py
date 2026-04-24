from typing import Any, Optional


class SingleSearchResultHandler:
    def __init__(self, symbol: Optional[str] = None, name: Optional[str] = None,
                 currency: Optional[str] = None, exchangeShortName: Optional[str] = None,
                 **kwargs):
        self.symbol = symbol
        self.instrument_name = name
        self.currency = currency
        self.exchange = exchangeShortName
        self.country = "United States"  # We only include NYSE/NASDAQ results

    def get_modeled_result(self) -> dict:
        return {
            "country": self.country,
            "currency": self.currency,
            "exchange": self.exchange,
            "instrument_name": self.instrument_name,
            "symbol": self.symbol,
        }


class SearchHandler:

    def __init__(self, results: list = None):
        self.search_results: list = []
        for result in (results or []):
            if result.get("exchangeShortName") in {"NYSE", "NASDAQ"}:
                self.search_results.append(
                    SingleSearchResultHandler(**result).get_modeled_result()
                )

    def search(self, page: int, page_size: int) -> dict[str, Any]:
        paginated = self.search_results[page * page_size: page * page_size + page_size]
        return {
            "total_results": len(self.search_results),
            "page": page,
            "page_size": page_size,
            "results": paginated,
        }
