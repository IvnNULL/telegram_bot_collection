from aiogram.fsm.state import State, StatesGroup


class FSMFillForm(StatesGroup):
    fill_place = State()
    fill_category = State()
    fill_description = State()
    fill_amount = State()
    fill_payer = State()
    save_form = State()
    change_date = State()


class FSMEditExpense(StatesGroup):
    browsing = State()
    changing_date = State()
