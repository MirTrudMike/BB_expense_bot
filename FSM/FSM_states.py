from aiogram.fsm.state import default_state, State, StatesGroup


class OldFSM(StatesGroup):
    choose_date = State()
    choose_group = State()
    input_amount = State()
    save_or_comment = State()
    add_comment = State()
    save = State()
    more_or_done = State()


class GetSumFSM(StatesGroup):
    choose_from = State()
    choose_to = State()
    leave_or_delete = State()


class PassTryFSM(StatesGroup):
    input_pass = State()
    get_informed = State()


class AdminFSM(StatesGroup):
    input_index = State()
    confirm_del = State()
    confirm_restore_base = State()


class BfFSM(StatesGroup):
    input_bf_number = State()
    confirm_cook = State()
    input_cook_salary = State()
    input_cook_exp = State()


class AdminGetSumFSM(StatesGroup):
    choose_from = State()
    choose_to = State()
    leave_or_delete = State()


