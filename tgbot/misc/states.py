from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    waiting_set_new_payment_sum = State()
