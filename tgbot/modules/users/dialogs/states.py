from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    start = State()