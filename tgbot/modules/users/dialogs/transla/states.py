from aiogram.fsm.state import State, StatesGroup


class TopicsState(StatesGroup):
    START = State()


class SelectTopic(StatesGroup):
    START = State()