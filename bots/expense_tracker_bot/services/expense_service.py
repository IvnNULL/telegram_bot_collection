from aiogram.types import BufferedInputFile

from database.models import Expense
from texts.texts import TEXTS


def expenses_to_text(expenses: list[Expense]) -> str:
    text = ''
    previous_date = None
    for expense in expenses:
        if previous_date != expense.date:
            previous_date = expense.date
            text += f'\n<b>{expense.date.strftime("%d.%m.%Y")}</b>\n'
        amount = f'{expense.amount:_}'.replace('_', ' ')
        text += f'{expense.place}: {amount} р. - {expense.payer}\n'

    return text


def expenses_to_csv_text(expenses: list[Expense]) -> str:
    lines = []
    for expense in expenses:
        lines.append(
            f'{expense.date.strftime("%d.%m.%Y")};'
            f'{expense.category};'
            f'{expense.place};'
            f'{expense.description};'
            f'{expense.amount};'
            f'{expense.payer}'
        )

    return '\n'.join(lines)


def text_to_csv_file(csv_text: str):
    file_bytes = csv_text.encode('utf-8-sig')
    csv_file = BufferedInputFile(file_bytes, filename='expenses.csv')

    return csv_file


def prepare_edit_data(expenses: list[Expense]):
    page_size = 7
    sep = ' | '

    buttons = []

    for i, expense in enumerate(expenses):
        if i % page_size == 0:
            buttons.append([])
        buttons[-1].append(
            {
                'text': sep.join([expense.place, expense.category, f'{expense.amount}', expense.payer]),
                'index': f'{i}',
            }
        )
    if not buttons:
        buttons.append([{'text': TEXTS['edit_no_expenses'], 'index': 'pass'}])

    return {
        'expenses_buttons': buttons,
        'expenses_ids': [expense.id for expense in expenses],
        'current_page': 1,
        'total_pages': len(buttons),
    }
