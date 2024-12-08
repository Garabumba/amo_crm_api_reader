import asyncio
from datetime import datetime, timedelta
from clickhouse_connect import get_async_client
from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from services.file_service import FileService
import os
import csv
import aiofiles

async def read_users_from_csv(file_path):
    clinics_dict = {}

    async with aiofiles.open(file_path, mode='r') as file:
        reader = csv.reader((await file.read()).splitlines(), delimiter=';')
        next(reader)

        for user, clinic, chat_id, monthly_plan in reader:
            clinic_data = clinics_dict.setdefault(clinic, {'chat_id': int(chat_id), 'users': []})
            clinic_data['users'].append({'user': user, 'monthly_plan': float(monthly_plan)})

    return clinics_dict

async def load_config(file_service):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, file_service.read_json_from_file)

def create_query(users_array):
    user_list = "', '".join(users_array)
    return f"""
        SELECT user_info.*, total_summa.total_summa FROM
        (SELECT
            responsible_user,
            MAX(leads_count) AS leads_count,
            MAX(leads_with_summa) AS leads_with_summa,
            MAX(conversion) AS conversion,
            SUM(oplata_summa) AS oplata_summa,
            SUM(oplata_credit_summa) AS oplata_credit_summa,
            lead_PervichkaVtorichka
        FROM test_db.users
        WHERE responsible_user IN ('{user_list}')
        GROUP BY responsible_user, lead_PervichkaVtorichka) AS user_info
        LEFT JOIN
        (SELECT 
            responsible_user, 
            SUM(oplata_summa) + MAX(oplata_credit_summa) AS total_summa 
        FROM test_db.users
        WHERE date >= toStartOfMonth(now()) 
        AND date < toStartOfMonth(addMonths(now(), 1))
        GROUP BY responsible_user) AS total_summa
        ON user_info.responsible_user = total_summa.responsible_user
    """

def process_query_results(rows, users):
    data = []
    user_map = {user['user']: user['monthly_plan'] for user in users}

    for row in rows.result_rows:
        user_name = row[0]
        total_summa = row[7] or 0
        current_user = next((u for u in data if u['name'] == user_name), None)
        if not current_user:
            current_user = {
                'name': user_name,
                'prinyal_pervichek': 0,
                'prodazh_s_pervichek': 0,
                'konv': 0,
                'viruchka_s_pervichek': 0,
                'prinyal_vtorichek': 0,
                'prodazh_so_vtorichek': 0,
                'viruchka_so_vtorichki': 0,
                'viruchka_s_prochih_doplat': 0,
                'total_viruchka': total_summa,
                'monthly_plan': user_map.get(user_name, 0),
            }
            data.append(current_user)

        if row[6] == 'Первичка':
            current_user.update({
                'prinyal_pervichek': row[1],
                'prodazh_s_pervichek': row[2],
                'konv': row[3],
                'viruchka_s_pervichek': row[4],
            })
        elif row[6] == 'Вторичка':
            current_user.update({
                'prinyal_vtorichek': row[1],
                'prodazh_so_vtorichek': row[2],
                'viruchka_so_vtorichki': row[4],
            })

        current_user['viruchka_s_prochih_doplat'] = row[5]

    return data

def format_user_message(user):
    run_rate = (
        user['total_viruchka'] / user['monthly_plan'] * 100
        if user['total_viruchka'] != 0 else 0
    )
    return (
        f"<b>{user['name']} ({datetime.now().date().strftime('%d.%m.%Y')})</b>\n"
        f"<i>Принял первичек:</i> {user['prinyal_pervichek']}\n"
        f"<i>Продаж с первичек:</i> {user['prodazh_s_pervichek']}\n"
        f"<i>Конверсия с первички:</i> {user['konv']}%\n"
        f"<i>Выручка с первички:</i> {user['viruchka_s_pervichek']} ₽\n"
        f"<i>Принял вторичек:</i> {user['prinyal_vtorichek']}\n"
        f"<i>Продаж со вторичек:</i> {user['prodazh_so_vtorichek']}\n"
        f"<i>Выручка со вторички:</i> {user['viruchka_so_vtorichki']} ₽\n"
        f"<i>Выручка с прочих доплат:</i> {user['viruchka_s_prochih_doplat']} ₽\n"
        f"<i>План на месяц:</i> {user['monthly_plan']} ₽\n"
        f"<i>RunRate:</i> {run_rate:.2f} %"
    )

async def send_message(bot, chat_id, message, logs_file_service):
    try:
        await bot.send_message(chat_id, text=message, parse_mode=ParseMode.HTML)
    except Exception as ex:
        await logs_file_service.write_log_file(
            f"Ошибка отправки сообщения: {ex}"
        )

async def main():
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    csv_file_path = os.path.join(parent_dir, 'leads_csv/users.csv')

    bot_config_file_service = FileService('bot_config.json')
    db_config_file_service = FileService('upload_csv_in_clickhouse_config.json')
    logs_file_service = FileService('BotLogs.txt')

    bot_json_config = await load_config(bot_config_file_service)
    db_config_json = await load_config(db_config_file_service)

    bot_token = bot_json_config['BOT_TOKEN']
    db_config = {
        'host': db_config_json['HOST'],
        'port': db_config_json['PORT'],
        'username': db_config_json['USERNAME'],
        'password': db_config_json['PASSWORD'],
        'database': db_config_json['DB_NAME'],
    }

    client = await get_async_client(**db_config)
    clinic_users = await read_users_from_csv(csv_file_path)

    async with Bot(token=bot_token) as bot:
        tasks = []
        for clinic, value in clinic_users.items():
            users = value['users']
            users_array = [u['user'] for u in users]

            query = create_query(users_array)
            rows = await client.query(query)
            data = process_query_results(rows, users)

            for user in data:
                message = format_user_message(user)
                chat_id = value['chat_id']

                tasks.append(send_message(bot, chat_id, message, logs_file_service))

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
