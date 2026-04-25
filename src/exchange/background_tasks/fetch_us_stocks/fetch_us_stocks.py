from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.external_client_handlers.client_requests import fetch_all_stocks
from src.exchange.external_client_handlers.client_response_models.fetch_stocks_handler import FetchStocksHandler


async def update_stock_list(db: AsyncSession) -> None:
    stock_data = await fetch_all_stocks()
    await FetchStocksHandler(stock_data).update_stocks_in_db(db)
