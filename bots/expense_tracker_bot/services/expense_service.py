from sqlalchemy.ext.asyncio import AsyncSession
from database.db import list_expenses
from texts.texts import TEXTS


async def get_expenses_text(session: AsyncSession) -> str:
    expenses = await list_expenses(session)

    if expenses is None:
        return TEXTS['no_expenses']

    text = ''
    previous_date = None
    for expense in expenses:
        if previous_date != expense.date:
            previous_date = expense.date
            text += f'\n\n{expense.date}\n'
        text += f'{expense.place}: {expense.amount:_} р. - {expense.payer}\n'

    return text


async def get_expenses_csv_text(session: AsyncSession) -> str:
    expenses = await list_expenses(session)

    if expenses is None:
        return TEXTS['no_expenses']

    lines = []
    for expense in expenses:
        lines.append(
            f'{expense.date};'
            f'{expense.category};'
            f'{expense.place};'
            f'{expense.description};'
            f'{expense.amount};'
            f'{expense.payer}'

        )

    return '\n'.join(lines)
