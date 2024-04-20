from lexicone import LEXICON_RU
import json

def write_user_to_env(id):
    with open('.env', mode='r') as file:
        text = file.readlines()
        text[-1] = text[-1].strip() + f',{str(id)}'
    with open('.env', mode='w') as file:
        file.writelines(text)


def decorate_expense(expense_dict):
    decorated_string = (f"📆 {expense_dict['date']}\n"
         f"{LEXICON_RU[expense_dict['category']]}\n"
         f"🪙 {expense_dict['amount']} Лари")
    return decorated_string


def update_base_file(base: list):
    with open('expense_base.json', mode='w') as file:
        json.dump(base, file, indent=4, ensure_ascii=False)





