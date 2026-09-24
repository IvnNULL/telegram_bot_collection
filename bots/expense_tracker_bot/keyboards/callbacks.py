from aiogram.filters.callback_data import CallbackData


class ExpenseCallback(CallbackData, prefix='expense'):
    action: str
    value: str | None = None


class MenuCallback(CallbackData, prefix='menu'):
    target: str
