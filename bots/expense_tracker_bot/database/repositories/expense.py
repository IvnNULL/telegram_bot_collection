import logging
from datetime import date

from sqlalchemy import select, delete, func

from database.models import Expense
from database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ExpenseRepository(BaseRepository):
    async def add_expense(
        self,
        *,
        user_id: int,
        date: date,
        category: str,
        place: str,
        description: str,
        amount: int,
        payer: str,
    ) -> None:
        expense = Expense(
            user_id=user_id,
            date=date,
            category=category,
            place=place,
            description=description,
            amount=amount,
            payer=payer,
        )
        self.session.add(expense)
        logger.debug(f'Add expense from {user_id}')
        await self.session.commit()
        logger.debug(f'Add expense from {user_id} completed')

    async def list_expenses(self) -> list[Expense] | None:
        data = await self.session.scalars(select(Expense).order_by(Expense.date))
        expenses = data.all()
        return expenses if expenses else None

    async def get_latest_expense_date(self) -> date | None:
        latest_date = await self.session.scalar(select(func.max(Expense.date)))
        return latest_date

    async def get_expenses_by_date(self, target_date: date) -> list[Expense]:
        data = await self.session.scalars(
            select(Expense).where(Expense.date == target_date).order_by(Expense.id.desc())
        )
        expenses = data.all()
        return expenses

    async def get_expense_by_id(self, expense_id: int) -> Expense:
        data = await self.session.scalar(select(Expense).where(Expense.id == expense_id))
        return data

    async def delete_expense_by_id(self, expense_id: int) -> None:
        await self.session.execute(delete(Expense).where(Expense.id == expense_id))
        await self.session.commit()

    async def clear_expenses(self) -> None:
        await self.session.execute(delete(Expense))
        await self.session.commit()
