from aiogram.fsm.state import State, StatesGroup


class ExpenseAddSteps(StatesGroup):
    waiting_for_place = State()
    waiting_for_category = State()
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_payer = State()
    waiting_for_date = State()

    waiting_for_confirmation = State()


class ExpenseEditSteps(StatesGroup):
    browsing = State()
    changing_date = State()
    deleting = State()
