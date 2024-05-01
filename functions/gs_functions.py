import pygsheets
from datetime import datetime
import pandas as pd

salaro_sheet_name = 'სალარო'


def create_new_month_worksheet():
    today = datetime.now()
    try:
        client = pygsheets.authorize(
            service_account_file='/home/mirtrudmike/Downloads/bb-expense-bot-credentials.json'
        )
        salaro = client.open(salaro_sheet_name)

        past_month = salaro[0]
        past_month_df = pd.DataFrame(past_month.get_all_records())

        today_str = today.strftime('%d.%m.%Y')
        end_month_index = past_month_df[past_month_df['Name'] == today_str].index.to_list()[-1]
        end_month_balance = past_month_df.iloc[end_month_index]['Balance']

        coming_month_name = today.strftime('%B')
        salaro.add_worksheet(
            title=coming_month_name,
            rows=200, cols=15,
            src_tuple=(salaro.id, past_month.id),
            index=0)

        salaro = client.open(salaro_sheet_name)
        coming_month = salaro[0]
        past_month = salaro[1]

        coming_month.delete_rows(2, end_month_index)
        coming_month.update_value('D2', val=end_month_balance, parse=True)
        coming_month.update_value('G1', val='=СУММ(D2,B:C)', parse=True)

        past_month.delete_rows(end_month_index + 3, len(coming_month.get_all_records()))

        past_month.merge_cells(start=f"A{end_month_index + 3}", end=f"E{end_month_index + 6}")

        warning_cell = past_month.cell(f"A{end_month_index + 3}")
        warning_cell.color = (0.94509804, 0.7607843, 0.19607843, 0)
        warning_cell.set_text_format('fontSize', 31)
        warning_cell.set_text_format('fontFamily', 'Lexend')
        warning_cell.set_horizontal_alignment(pygsheets.custom_types.HorizontalAlignment.CENTER)
        past_month.cell(f"A{end_month_index + 3}").set_value('Go To The Next Month')

        return True

    except:
        return None


