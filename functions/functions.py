from lexicone import LEXICON_RU
def write_user_to_env(id):
    with open('.env', mode='r') as file:
        text = file.readlines()
        text[-1] = text[-1].strip() + f',{str(id)}'
    with open('.env', mode='w') as file:
        file.writelines(text)


def decorate_expense(expense_dict):
    decorated_string = (f"📆 {expense_dict['date'].strftime('%-d %B %Y')}\n"
         f"{LEXICON_RU[expense_dict['category']]}\n"
         f"🇬🇪{expense_dict['amount']} Лари")
    return decorated_string

