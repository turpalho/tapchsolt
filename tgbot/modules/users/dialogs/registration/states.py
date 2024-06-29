from aiogram.fsm.state import State, StatesGroup


class UserRegistrationState(StatesGroup):
    START = State()
    SET_NICNAME = State()
    CONFIRM_DATA = State()
    SAVE_USER = State()