import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from os import environ

load_dotenv()

TOKEN = environ.get("BOT_TOKEN")
API_URL = environ.get("API_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


class UserState(StatesGroup):
    choosing_district = State()
    choosing_region = State()
    choosing_masjid = State()


districts_regions = {
    "Toshkent": ["Bektemir", "Mirobod", "Mirzo Ulug‘bek", "Olmazor", "Sirg‘ali", "Uchtepa", "Chilonzor", "Shayxontohur",
                 "Yunusobod", "Yakkasaroy"],
    "Toshkent viloyati": ["Bekobod", "Bo‘ka", "Bo‘stonliq", "Chinoz", "Oqqo‘rg‘on", "Ohangaron", "Parkent", "Piskent",
                          "Quyichirchiq", "Yuqorichirchiq"],
    "Andijon": ["Andijon shahri", "Asaka", "Baliqchi", "Bo‘z", "Buloqboshi", "Jalaquduq", "Izboskan", "Marhamat",
                "Oltinko‘l", "Paxtaobod", "Xo‘jaobod"],
    "Farg‘ona": ["Farg‘ona shahri", "Bag‘dod", "Beshariq", "Buvayda", "Dang‘ara", "Furqat", "Qo‘qon", "Quva", "Quvasoy",
                 "Oltiariq", "Rishton"],
    "Namangan": ["Namangan shahri", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin", "Pop", "To‘raqo‘rg‘on",
                 "Uychi", "Yangiqo‘rg‘on"],
    "Buxoro": ["Buxoro shahri", "G‘ijduvon", "Jondor", "Kogon", "Olot", "Peshku", "Qorako‘l", "Qorovulbozor", "Romitan",
               "Shofirkon", "Vobkent"],
    "Samarqand": ["Samarqand shahri", "Bulung‘ur", "Ishtixon", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Nurobod",
                  "Oqdaryo", "Paxtachi", "Payariq", "Toyloq", "Urgut"],
    "Qashqadaryo": ["Qarshi", "Chiroqchi", "Dehqonobod", "G‘uzor", "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak",
                    "Nishon", "Shahrisabz", "Yakkabog‘"],
    "Surxondaryo": ["Termiz", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo‘rg‘on", "Muzrabot", "Oltinsoy",
                    "Sariosiyo", "Sherobod", "Sho‘rchi", "Uzun"],
    "Xorazm": ["Urganch", "Bog‘ot", "Gurlan", "Qo‘shko‘pir", "Shovot", "Xiva", "Yangiariq", "Yangibozor"],
    "Navoiy": ["Navoiy shahri", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa", "Tomdi", "Uchquduq"],
    "Jizzax": ["Jizzax shahri", "Arnasoy", "Baxmal", "Do‘stlik", "Forish", "G‘allaorol", "Mirzacho‘l", "Paxtakor",
               "Yangiobod", "Zomin", "Zafarobod", "Zarbdor"],
    "Sirdaryo": ["Guliston", "Baxt", "Boyovut", "Hovos", "Mirzaobod", "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo",
                 "Yangiyer"],
    "Qoraqalpog‘iston": ["Nukus", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal‘a", "Kegeyli", "Mo‘ynoq", "Qonliko‘l",
                         "Qorao‘zak", "Shumanay", "Taxtako‘pir", "To‘rtko‘l", "Xo‘jayli"],
}


def get_keyboard(options, back_button=False, row_size=3):
    buttons = [KeyboardButton(text=option) for option in options]
    keyboard = [buttons[i:i + row_size] for i in range(0, len(buttons), row_size)]
    if back_button:
        keyboard.append([KeyboardButton(text="🔙 Orqaga")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, is_persistent=True)


async def fetch_masjid_list(state):
    data = await state.get_data()
    district = data.get("district")
    region = data.get("region")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}get-masjid-info?district={district}&region={region}") as response:
            if response.status == 200:
                return await response.json()
            return []


async def show_main_menu(message: types.Message):
    menu_keyboard = get_keyboard(["🏠 Manzilni o‘zgartirish", "🏛 Masjid ma'lumotlari"])
    await message.answer("📋 Bosh menyu:", reply_markup=menu_keyboard)


@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}check-user/?telegram_id={message.from_user.id}") as response:
            data = await response.json()
            if data['status'] and message.text != "🏠 Manzilni o‘zgartirish" and message.text != "🔙 Orqaga":
                await show_main_menu(message)
            else:
                await state.set_state(UserState.choosing_district)
                await message.answer("🇺🇿 Iltimos, viloyatingizni tanlang:",
                                     reply_markup=get_keyboard(list(districts_regions.keys())))


@dp.message(UserState.choosing_district)
async def choose_district(message: types.Message, state: FSMContext):
    if message.text not in districts_regions:
        await message.answer("❌ Noto‘g‘ri viloyat tanlandi. Qayta urinib ko‘ring.")
        return
    await state.update_data(district=message.text)
    await state.set_state(UserState.choosing_region)
    await message.answer("📍 Hududingizni tanlang:",
                         reply_markup=get_keyboard(districts_regions[message.text], back_button=True))


@dp.message(UserState.choosing_region)
async def choose_region(message: types.Message, state: FSMContext):
    data = await state.get_data()
    district = data.get("district")

    if message.text == "🔙 Orqaga":
        await start_handler(message, state)
        return

    if message.text not in districts_regions.get(district, []):
        await message.answer("❌ Noto‘g‘ri hudud tanlandi. Qayta urinib ko‘ring.")
        return

    await state.update_data(region=message.text)

    masjid_data = await fetch_masjid_list(state)
    masjid_names = [m["name"] for m in masjid_data] if masjid_data else ["❌ Ma'lumot topilmadi"]

    await state.set_state(UserState.choosing_masjid)
    await message.answer("🏛 Masjidni tanlang:", reply_markup=get_keyboard(masjid_names, back_button=True))


@dp.message(UserState.choosing_masjid)
async def choose_masjid(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(UserState.choosing_region)
        data = await state.get_data()
        await message.answer("📍 Hududingizni tanlang:",
                             reply_markup=get_keyboard(districts_regions[data.get("district")], back_button=True))
        return

    await state.update_data(masjid=message.text)
    data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}add-or-update/", json={
            "telegram_id": message.from_user.id,
            "district": data["district"],
            "region": data["region"],
            "masjid": message.text
        }) as response:
            if response.status == 200 or response.status == 201:
                await state.clear()
                await show_main_menu(message)
            else:
                await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko‘ring.")
                return


@dp.message(F.text.startswith('🏠 Manzilni o‘zgartirish'))
async def change_location(message: types.Message, state: FSMContext):
    await start_handler(message, state)


@dp.message(F.text.startswith("🏛 Masjid ma'lumotlar"))
async def change_location(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}get-user-masjid/?telegram_id={message.from_user.id}") as response:
            if response.status == 200:
                data = await response.json()
                masjid = data["masjid"]
                text = (
                    f"📍 *{masjid['name']}*  \n"
                    f"🏙 *Hudud:* {masjid['district']} viloyati, {masjid['region']} tumani\n"
                    f"📞 *Aloqa:* {masjid['contact']}\n"
                    f"📌 *Manzil:* [Xaritada ko‘rish]({masjid['location_url']})\n\n"
                    f"🕌 *Namoz vaqtlari:*\n"
                    f"  - 🌅 *Bomdod:* {masjid['bomdod']}\n"
                    f"  - ☀ *Quyosh:* {masjid['quyosh']}\n"
                    f"  - 🕛 *Peshin:* {masjid['peshin']}\n"
                    f"  - 🌇 *Asr:* {masjid['asr']}\n"
                    f"  - 🌆 *Shom:* {masjid['shom']}\n"
                    f"  - 🌙 *Xufton:* {masjid['xufton']}"
                )

                await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko‘ring.")
                return


if __name__ == "__main__":
    import asyncio

    asyncio.run(dp.start_polling(bot))
