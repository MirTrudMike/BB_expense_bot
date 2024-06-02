import os.path
import pygsheets
import requests
from datetime import datetime, timedelta
import json

room_ids = {'728438': '1',
            '728439': '2',
            '728440': '3',
            '728441': '4',
            '728442': '5',
            '728443': '6',
            '728444': '8',
            '728445': '7',
            '778115': 'No-show'}


def make_breakfast_plan_for_day(date: datetime, bnovo_login, bnovo_password):
    today = date.strftime("%Y-%m-%d")

    session = requests.Session()
    login_info = json.dumps({"username": bnovo_login, "password": bnovo_password})
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = session.post('https://online.bnovo.ru/', headers=headers, data=login_info)

    if response.status_code == 200:
        headers = {'X-Requested-With': 'XMLHttpRequest',
                   'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        payload = json.dumps({"dfrom": today,
                              "dto": today,
                              "daily": 1})

        result = list(
            filter(lambda d: room_ids[d['room_id']] != 'No show',
                   session.post('https://online.bnovo.ru/planning/bookings',
                                headers=headers, data=payload).json()['result']))

        calc = {str(i): 0 for i in range(1, 9)}
        ids_for_today = [bk['booking_id'] for bk in result]

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'}

        for bk_id in ids_for_today:
            full_bk_info = session.get(f'https://online.bnovo.ru/booking/general/{bk_id}', headers=headers).json()
            bf_in_bk = list(filter(lambda d: d['service_id'] == '180811' and d['date'] == today,
                                   full_bk_info['booking']['prices_all']))
            if bf_in_bk:
                calc[room_ids[full_bk_info['booking']['actual_price']['room_id']]] = int(bf_in_bk[0]['quantity'])

        session.close()

        bf_total = sum(calc.values())

        text = (f"\n1🔹 _________ {calc['1']}🍳"
                f"\n2🔹 _________ {calc['2']}🍳"
                f"\n3🔹 _________ {calc['3']}🍳"
                f"\n4🔹 _________ {calc['4']}🍳"
                f"\n5🔹 _________ {calc['5']}🍳"
                f"\n6🔹 _________ {calc['6']}🍳"
                f"\n8🔹 _________ {calc['8']}🍳"
                f"\n7🔹 _________ {calc['7']}🍳")

        return bf_total, text

    else:
        return False


def get_cook_counter():
    month = datetime.now().strftime("%m-%Y")
    with open(f"{os.path.abspath('./breakfast/counter.json')}", mode='r') as file:
        counter = json.load(file)
        cook_day_number = counter['cook_days'].setdefault(month, 0)
    return cook_day_number


def write_bf_to_counter(bf_number, cook_day, cook_salary):
    try:
        date = datetime.now().strftime("%d.%m.%Y")
        month = datetime.now().strftime("%m-%Y")

        with open(f"{os.path.abspath('./breakfast/counter.json')}", mode='r') as file:
            counter = json.load(file)

        counter['days'].update({date: bf_number})
        if cook_day != 'XXX':
            counter['cook_days'][month] = (counter['cook_days'].setdefault(month, 0) * 0) + cook_day

        counter['cook_salary'].update({date: cook_salary})

        with open(f"{os.path.abspath('./breakfast/counter.json')}", mode='w') as file:
            json.dump(counter, file, indent=4, ensure_ascii=False)

        return True

    except:
        return 100


def write_bf_google(bf_number, cook_day, cook_salary):
    try:
        date = datetime.now().strftime("%d.%m.%Y")
        today_month = datetime.now().strftime('%B-%Y')
        sheet_name = 'Breakfast_counter'
        full_base_id = '1Ai_tk1B5t05xqbJgjzLZW8aPiNUlN3bxvSgQt-9HUNc'
        client = pygsheets.authorize(
            service_account_file=f"{os.path.abspath('./config_data/bb_gs.json')}")
        full_base = client.open(sheet_name)

        if full_base[0].title != today_month:
            new_month = full_base.add_worksheet(title=today_month, src_tuple=(full_base_id, full_base[0].id), index=0)
            new_month.delete_rows(2, len(full_base[0].get_all_records()))
            full_base = client.open(sheet_name)

        base = full_base[0]
        free_row = len(base.get_all_records()) + 2
        base.update_row(free_row, [date, bf_number, cook_day, cook_salary])

        return True

    except:
        return 200


def write_breakfast(bf_number, cook_day, cook_salary):
    counter = write_bf_to_counter(bf_number, cook_day, cook_salary)
    google = write_bf_google(bf_number, cook_day, cook_salary)

    return [counter, google]
