from aiogram.fsm.state import default_state, State, StatesGroup


class OldFSM(StatesGroup):
    choose_date = State()
    choose_group = State()
    input_amount = State()
    saveorcomment = State()
    add_comment = State()
    save = State()

