from lexicone import LEXICON_RU
import json
import numpy as np
import pandas as pd
from datetime import datetime
import os
from aiogram.types.input_file import FSInputFile


def write_user_to_env(id):
    with open('.env', mode='r') as file:
        text = file.readlines()
        text[-1] = text[-1].strip() + f',{str(id)}'
    with open('.env', mode='w') as file:
        file.writelines(text)


def write_user_to_block(id):
    with open('.env', mode='r') as file:
        text = file.readlines()
        text[-2] = text[-2].strip() + f',{str(id)}\n'
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


def get_sum(from_date, to_date, base):
    s = 'Посчитал:\n'
    df = pd.DataFrame(base[1:])
    df['date'] = np.vectorize(lambda s: datetime.strptime(s, '%d %B %Y'))(df['date'])
    df = df[(df['date'] >= from_date) & (df['date'] <= to_date)]
    result = df.groupby('category').sum(numeric_only=True)
    if len(df) > 0:
        for category in result.sort_values('amount', ascending=False).index:
            s += f"\n{LEXICON_RU[category]}: {result.loc[category]['amount']}"
        return s
    else: return None


def make_xlsx(from_date, to_date, base):
    file_name = f"Cash_expenses-{from_date.strftime('%-d%B')}-{to_date.strftime('%-d%B')}.xlsx"
    df = pd.DataFrame(base[1:]).drop('input_type', axis=1)
    df.columns = ['Date', 'Category', 'Amount', 'Comment']
    df['Date'] = np.vectorize(lambda s: datetime.strptime(s, '%d %B %Y'))(df['Date'])
    df = df.sort_values('Date')
    df = df[(df['Date'] >= from_date) & (df['Date'] <= to_date)]
    if len(df) > 0:
        df['Date'] = df['Date'].apply(lambda d: d.strftime('%-d %B %Y').ljust(2))
        df.to_excel(f"{os.path.abspath('./xlsx_reports')}/{file_name}", index=False)
        file = FSInputFile(f"{os.path.abspath('./xlsx_reports')}/{file_name}")
        return file
    else:
        return None


def find_expense_index_in_base(index):
    with open('expense_base.json') as file:
        expense_base = json.load(file)
    one = list(filter(lambda d: d['index'] == index, expense_base))[-1]
    base_index = expense_base.index(one)
    return base_index


def delete_record_by_base_index(base_index):
    with open('expense_base.json', mode='r') as file:
        base = json.load(file)
    base.pop(base_index)
    with open('expense_base.json', mode='w') as file:
        json.dump(base, file, indent=4, ensure_ascii=False)


