from aiogram.fsm.state import State, StatesGroup


class TranslationState(StatesGroup):
    START = State()
    SELECT_TARGET_LANGUAGE = State()
    TRANSLATE = State()