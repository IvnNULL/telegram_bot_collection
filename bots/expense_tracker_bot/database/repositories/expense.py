import logging
from datetime import date

from sqlalchemy import select, delete

from database.models import Expense
from database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ExpenseRepository(BaseRepository):
    async def add_expense(
            self,
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
        self.session.add(expense)
        logger.debug(f'Add expense from {user_id}')
        await self.session.commit()
        logger.debug(f'Add expense from {user_id} completed')

    async def list_expenses(self) -> list[Expense] | None:
        data = await self.session.scalars(
            select(Expense).order_by(Expense.date)
        )
        expenses = data.all()
        return expenses if expenses else None

    async def clear_expenses(self) -> None:
        await self.session.execute(delete(Expense))
        await self.session.commit()
