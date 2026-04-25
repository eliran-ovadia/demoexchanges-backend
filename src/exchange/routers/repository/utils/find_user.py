from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.database.models import User


async def find_user(db: AsyncSession, user_id: str = None, email: str = None) -> User | None:
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
    elif email:
        result = await db.execute(select(User).where(User.email == email))
    else:
        raise ValueError("Either user_id or email must be provided.")
    return result.scalar_one_or_none()
