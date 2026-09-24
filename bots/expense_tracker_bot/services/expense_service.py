from datetime import datetime

from aiogram.types import BufferedInputFile

from database.models import Expense
from texts.texts import TEXTS


def expenses_to_text(expenses: list[Expense]) -> str:
    texts = []
    previous_date = None
    for expense in expenses:
        if previous_date != expense.date:
            previous_date = expense.date
            texts.append(f'\n<b>{expense.date.strftime("%d.%m.%Y")}</b>\n')
        amount = f'{expense.amount:_}'.replace('_', ' ')
        texts.append(f'{expense.place}: {amount} р. - {expense.payer}\n')
    return ''.join(texts)


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


def text_to_csv_file(csv_text: str) -> BufferedInputFile:
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'expenses_{now}.csv'
    file_bytes = csv_text.encode('utf-8-sig')
    csv_file = BufferedInputFile(file_bytes, filename=filename)
    return csv_file


def expense_dump(expense: Expense) -> dict:
    return {
        'id': expense.id,
        'date': expense.date,
        'category': expense.category,
        'place': expense.place,
        'description': expense.description,
        'amount': expense.amount,
        'payer': expense.payer,
    }


def expense_dict_to_text(expense_dict: dict) -> str:
    expense_amount = expense_dict.get('amount', '')
    if expense_amount:
        expense_amount = f'{expense_amount:_} р.'.replace('_', ' ')
    return (
        f'Дата: {expense_dict["date"].strftime(TEXTS["DATE_FORMAT"])}\n'
        f'Место: {expense_dict.get("place", "")}\n'
        f'Категория: {expense_dict.get("category", "")}\n'
        f'Описание: {expense_dict.get("description", "")}\n'
        f'Сумма: {expense_amount}\n'
        f'Плательщик: {expense_dict.get("payer", "")}'
    )


def expense_to_text(expense: Expense) -> str:
    return expense_dict_to_text(expense_dump(expense))


def expenses_to_button_labels(expenses: list[Expense]) -> list[str]:
    return [' | '.join([expense.place, expense.category, f'{expense.amount}', expense.payer]) for expense in expenses]
