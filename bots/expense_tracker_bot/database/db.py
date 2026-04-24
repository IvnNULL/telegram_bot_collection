import logging
from datetime import date

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Expense, Payer, PlaceCategory

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


async def list_payers(session: AsyncSession) -> list[Payer] | None:
    data = await session.execute(select(Payer).order_by(Payer.counter.desc()))
    rows = data.scalars().all()
    return rows if rows else None


async def add_place_category(session: AsyncSession, *, place: str, category: str) -> None:
    stmt = await session.execute(
        select(PlaceCategory).filter_by(place=place, category=category)
    )
    item = stmt.scalar_one_or_none()

    if item:
        item.counter += 1
    else:
        new_item = PlaceCategory(place=place, category=category)
        session.add(new_item)

    await session.commit()


async def get_category_by_place(session: AsyncSession, *, place: str) -> None:
    stmt = (
        select(PlaceCategory.category)
        .filter_by(place=place)
        .order_by(PlaceCategory.counter.desc())
        # .limit(3)
    )
    rows = await session.execute(stmt)
    rows = rows.scalars().all()
    return rows if rows else None
