import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Expense

logger = logging.getLogger(__name__)


async def add_expense(
        session: AsyncSession,
        *,
        user_id: int,
        exp_date: date,
        category: str,
        place: str,
        description: str,
        amount: int,
        payer: str
) -> None:
    expense = Expense(
        user_id=user_id,
        date=exp_date,
        category=category,
        place=place,
        description=description,
        amount=amount,
        payer=payer
    )
    session.add(expense)
    logger.debug(f'Add expense from {user_id}')
    await session.commit()
    logger.debug(f'Add expense from {user_id} completed')
