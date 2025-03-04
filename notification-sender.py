import asyncio
import requests
from aiogram import Bot
from datetime import datetime, time
import pytz
from dotenv import load_dotenv
from os import environ

load_dotenv()

TOKEN = environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)

USER_API_URL = environ.get("API_URL")
UZBEKISTAN_TZ = pytz.timezone("Asia/Tashkent")

NOTIFICATION_TIMES = {
    time(4, 56): "Bomdod",
    time(5, 32): "Quyosh", #6:13
    time(11, 59): "Peshin",
    time(15, 51): "Asr",
    time(17, 37): "Shom",
    time(18, 50): "Xufton"
}

last_sent_time = None


async def send_notification(user_id, prayer_name, time):
    async with bot:
        message = f"📢 *{prayer_name} {time}* namozi vaqti yetib keldi! Alloh qabul qilsin. 🤲"
        await bot.send_message(user_id, message, parse_mode="Markdown")


def fetch_users():
    try:
        response = requests.get(f"{USER_API_URL}api/v1/get-all-user-info/")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ API error: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ API request failed: {e}")
        return []


async def check_and_send_notifications():
    global last_sent_time

    while True:
        now = datetime.now(UZBEKISTAN_TZ)
        current_time = now.time().replace(second=0, microsecond=0)

        if current_time in NOTIFICATION_TIMES and current_time != last_sent_time:
            prayer_name = NOTIFICATION_TIMES[current_time]
            users = fetch_users()

            for user in users:
                user_id = user["telegram_id"]
                await send_notification(user_id, prayer_name, user['masjid'][prayer_name.lower()])

            last_sent_time = current_time
            print(f"✅ Sent '{prayer_name}' notifications at {now.strftime('%H:%M')} Uzbekistan Time")

        await asyncio.sleep(10)


async def main():
    await check_and_send_notifications()


if __name__ == "__main__":
    asyncio.run(main())
