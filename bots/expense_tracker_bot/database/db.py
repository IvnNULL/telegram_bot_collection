import logging
from datetime import date

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Expense, Payer

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


async def list_expenses(session: AsyncSession) -> list[Expense] | None:
    data = await session.execute(select(Expense).order_by(Expense.date))
    rows = data.scalars().all()
    return rows if rows else None


async def clear_expenses(session: AsyncSession) -> None:
    await session.execute(delete(Expense))
    await session.commit()


async def add_payer(session: AsyncSession, *, payer: str) -> None:
    result = await session.execute(
        select(Payer).filter_by(payer=payer)
    )
    payer_exist = result.scalar_one_or_none()

    if payer_exist:
        payer_exist.counter += 1
    else:
        new_payer = Payer(payer=payer)
        session.add(new_payer)

    await session.commit()