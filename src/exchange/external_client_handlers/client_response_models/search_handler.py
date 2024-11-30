from functools import lru_cache
from typing import Any

from src.exchange.external_client_handlers.client_requests import get_search_result


class SearchHandler:

    def __init__(self, request: str = ''):
        self.search_results: list = get_search_result(request)
        self.paginated_results = None

    def search(self, page: int, page_size: int) -> dict[str, Any]:
        total_results = len(self.paginated_results)
        start_index = (page - 1) * page_size
        end_index = page * page_size
        paginated_results = self.paginated_results[start_index:end_index]

        return {
            "total_results": total_results,
            "page": page,
            "page_size": page_size,
            "results": paginated_results,
        }


# Factory cache - use LRU to swap entries
@lru_cache(maxsize=100)
def get_search_handler(request: str = '') -> SearchHandler:
    return SearchHandler(request)
