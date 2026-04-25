import math
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.app_logger import logger
from src.exchange.database.models import LastSplitDate, Portfolio


async def get_last_split_date(db: AsyncSession, current_time: datetime) -> LastSplitDate:
    """Returns the LastSplitDate row, creating it if it doesn't exist yet."""
    result = await db.execute(select(LastSplitDate))
    row = result.scalar_one_or_none()
    if row is None:
        row = LastSplitDate(last_split_check=current_time)
        db.add(row)
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.critical(f"Database commit failed when trying to update split table: {e}")
    return row


async def get_unique_stocks_list(db: AsyncSession) -> list[str]:
    result = await db.execute(select(Portfolio.symbol).group_by(Portfolio.symbol))
    return [row[0] for row in result.all()]


async def split_handler(db: AsyncSession, split: dict) -> None:
    """
    Adjust portfolio rows for a split event using a single bulk UPDATE.
    FMP split dict: {"symbol": "AAPL", "numerator": 4, "denominator": 1, "date": "..."}
    """
    symbol = split["symbol"]
    split_multiplier = split["numerator"] / split["denominator"]

    await db.execute(
        update(Portfolio)
        .where(Portfolio.symbol == symbol)
        .values(
            amount=func.ceil(Portfolio.amount * split_multiplier),
            price=Portfolio.price / split_multiplier,
        )
    )
    await db.commit()
