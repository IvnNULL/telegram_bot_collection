from aiogram.types import BufferedInputFile
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
            text += f'\n<b>{expense.date.strftime('%d.%m.%Y')}</b>\n'
        amount = f'{expense.amount:_}'.replace('_', ' ')
        text += f'{expense.place}: {amount} р. - {expense.payer}\n'

    return text


async def get_expenses_csv_text(session: AsyncSession) -> str:
    expenses = await list_expenses(session)

    if expenses is None:
        return TEXTS['no_expenses']

    lines = []
    for expense in expenses:
        lines.append(
            f'{expense.date.strftime('%d.%m.%Y')};'
            f'{expense.category};'
            f'{expense.place};'
            f'{expense.description};'
            f'{expense.amount};'
            f'{expense.payer}'
        )

    return '\n'.join(lines)


def get_expenses_csv_file(csv_text: str):
    file_bytes = csv_text.encode('utf-8-sig')

    csv_file = BufferedInputFile(
        file_bytes,
        filename='expenses.csv'
    )

    return csv_file
