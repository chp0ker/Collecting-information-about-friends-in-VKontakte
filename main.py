from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from collections import Counter
import requests
import aiogram
import json
import os

TOKEN_VK = "УКАЖИТЕ ВАШ ТОКЕН ОТ ВК"
TOKEN_TG = "УКАЖИТЕ ВАШ ТОКЕН ОТ ТГ БОТА"

bot = Bot(token=TOKEN_TG, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
storage = MemoryStorage()


class getting_link(StatesGroup):
    link_state = State()


@dp.message_handler(commands="start")
async def start_command(message: types.Message):
    await message.answer(
        "Добро пожаловать, это бот, для сбора информации об друзьях ВКонтакте"
        "\nЧтобы начать работу введите /vk"
    )


@dp.message_handler(commands="vk")
async def vk(message: types.Message):
    await message.answer("Укажите ссылку на страницу ВКонтакте")
    await getting_link.link_state.set()


@dp.message_handler(state=getting_link.link_state)
async def give_info(message: types.Message, state: FSMContext):
    all_cities = []
    all_schools = []

    link = message.text

    await state.update_data(link_state=link)

    if "https://vk.com/" not in link:
        await message.answer("Укажите ссылку на страницу ВКонтакте")
    elif "https://vk.com/" in link:
        link_id = link.replace("https://vk.com/", "")
        main_id_data = {
            "user_ids": link_id,
            "fields": "personal",
            "access_token": TOKEN_VK,
            "v": "5.131",
        }

        response = requests.post(
            "https://api.vk.com/method/users.get", data=main_id_data
        )
        main_info = response.json()

        try:
            main_id = main_info["response"][0]["id"]
        except:
            await message.answer("Страницы не существует, либо она заблокирована")
            await vk()
        id_friend_data = {"user_id": main_id, "access_token": TOKEN_VK, "v": "5.131"}

        response = requests.post(
            "https://api.vk.com/method/friends.get", data=id_friend_data
        )
        friends = response.json()

        try:
            id_person = friends["response"]["items"]
        except:
            await message.answer("Страница скрыта, либо она заблокирована")
            await vk()
        total_friends = friends["response"]["count"]
        await message.answer(f"Всего друзей: {total_friends}")
        await message.answer("Ждите отправленние данных об друзьях")
        for id_person in id_person:
            info_friends_data = {
                "user_ids": id_person,
                "fields": "bdate, contacts, city, schools, photo_max_orig",
                "access_token": TOKEN_VK,
                "v": "5.131",
            }

            response = requests.post(
                "https://api.vk.com/method/users.get", data=info_friends_data
            )
            info = response.json()

            try:
                link_tg = f"Ссылка: https://vk.com/id{id_person}"
            except:
                link_tg = ""
            try:
                first_name_tg = f"\nИмя: {info['response'][0]['first_name']}"
            except:
                first_name_tg = ""
            try:
                if info["response"][0]["last_name"] == "":
                    last_name_tg = ""
                else:
                    last_name_tg = f"\nФамилия: {info['response'][0]['last_name']}"
            except:
                last_name_tg = ""
            try:
                date_of_birth_tg = f"\nДата рождения: {info['response'][0]['bdate']}"
            except:
                date_of_birth_tg = ""
            try:
                if info["response"][0]["mobile_phone"] == "":
                    mobile_phone_tg = ""
                else:
                    mobile_phone_tg = (
                        f"\nМобильный телефон: {info['response'][0]['mobile_phone']}"
                    )
            except:
                mobile_phone_tg = ""
            try:
                if info["response"][0]["home_phone"] == "":
                    home_phone_tg = ""
                else:
                    home_phone_tg = (
                        f"\nДомашний телефон: {info['response'][0]['home_phone']}"
                    )
            except:
                home_phone_tg = ""
            try:
                all_cities.append(f"{info['response'][0]['city']['title']}")
                city_tg = f"\nГород: {info['response'][0]['city']['title']}"
            except:
                city_tg = ""
            try:
                all_schools.append(f"{info['response'][0]['schools'][0]['name']}")
                school_tg = f"\nШкола: {info['response'][0]['schools'][0]['name']}"
            except:
                school_tg = ""
            try:
                photo_max_orig_tg = (
                    f"\nФотография: {info['response'][0]['photo_max_orig']}"
                )
            except:
                photo_max_orig_tg = ""
            file = open(f"{link_id}.txt", "a", encoding="utf-8")
            file.write(
                f"{link_tg}"
                f"{first_name_tg}"
                f"{last_name_tg}"
                f"{date_of_birth_tg}"
                f"{mobile_phone_tg}"
                f"{home_phone_tg}"
                f"{city_tg}"
                f"{school_tg}"
                f"{photo_max_orig_tg}\n\n\n"
            )
        all_cities = str(Counter(all_cities))
        all_cities = (
            all_cities.replace("Counter({", "")
            .replace("})", "")
            .replace("'", "")
            .replace(", ", "\n")
        )

        all_schools = str(Counter(all_schools))
        all_schools = (
            all_schools.replace("Counter({", "")
            .replace("})", "")
            .replace("'", "")
            .replace(", ", "\n")
        )

        file.write(f"\n\n\n{all_cities}\n\n\n\n" f"{all_schools}")

        file = open(f"{link_id}.txt", "rb")
        await message.reply_document(file)

        os.remove(f"{link_id}.txt")


if __name__ == "__main__":
    executor.start_polling(dp)
