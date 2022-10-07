import datetime
import json
from threading import Thread
import time
import requests
import schedule
import telebot
from telebot import types
from envparse import Env

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")

ALL_BIRTHDAY_SCHEDULE = {"Диана": datetime.date(1999, 10, 4), "Марсель": datetime.date(1996, 12, 6),
                         "Папа Альберт": datetime.date(1970, 12, 3), "Мама Света": datetime.date(1976, 1, 12),
                         "Папа Шамиль": datetime.date(1963, 2, 21), "Мама Аймара": datetime.date(1973, 7, 10),
                         "Аишка": datetime.date(2006, 2, 18), "Арслан": datetime.date(2005, 8, 18)}

PERSON_ID = {"Диана": 863356793, "Марсель": 525604245,
             "Папа Альберт": 863356793, "Мама Света": 863356793,
             "Папа Шамиль": 863356793, "Мама Аймара": 863356793,
             "Аишка": 863356793, "Арслан": 863356793}

bot = telebot.TeleBot(token=TOKEN)


def check(message):
    """ Пропускаем сообщения только от членов семьи """
    with open("./users.json", "r") as file:
        users_data = json.load(file)

    user_id = message.from_user.id

    if str(user_id) not in users_data:
        return False
    return True


@bot.message_handler(commands=["start"])
def start(message):
    if check(message):
        if message.from_user.last_name is None:
            """ Проверка на отсутствие фамилии для верного приветствия"""
            message_to_send = f"Привет, <b>{message.from_user.first_name}</b>!\nЧто хочешь узнать?"
        else:
            message_to_send = f"Привет, <b>{message.from_user.first_name} {message.from_user.last_name}</b>\nЧто хочешь " \
                              f"узнать? "

        """ Добавляем кнопки действия бота """
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        birthday_schedule = types.KeyboardButton("/birthday_schedule")
        next_birthday = types.KeyboardButton("/next_birthday")
        markup.add(birthday_schedule, next_birthday)

        bot.send_message(message.chat.id, message_to_send, parse_mode="html", reply_markup=markup)
    else:
        bot.reply_to(message, "Извините, это закрытый семейный бот")


@bot.message_handler(content_types=["text"])
def all_birthdays(message):
    if check(message):
        if message.text == "/birthday_schedule":
            birthday = types.InlineKeyboardMarkup(row_width=1)
            """ Добавление кнопок по имени каждого члена семьи, чтобы узнать день рождения """
            for name_birthday_boy in ALL_BIRTHDAY_SCHEDULE.keys():
                birthday.add(types.InlineKeyboardButton(text=name_birthday_boy, callback_data=name_birthday_boy))
            bot.send_message(chat_id=message.chat.id, text="Выберите, чье день рождения хотите узнать",
                             reply_markup=birthday)
        elif message.text == "/next_birthday":
            """ Поиск ближайшего дня рождения """
            date_now = datetime.datetime.now()
            difference_in_days = 365
            birthday_boy = ""
            for name_birthday_boy, date_of_birth in ALL_BIRTHDAY_SCHEDULE.items():
                difference = datetime.datetime(date_now.year, date_of_birth.month, date_of_birth.day) - date_now
                if (difference.days >= 0) and (difference.days < difference_in_days):
                    difference_in_days = difference.days
                    birthday_boy = name_birthday_boy
            bot.send_message(chat_id=message.chat.id, text=f"Ближайший день рождения отмечает {birthday_boy}, "
                                                           f"осталось {difference_in_days} дней")
    else:
        bot.reply_to(message, "Извините, это закрытый семейный бот")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """ Вывод даты дня рождения в формате 01.01.1999 """
    day_birth = f"{ALL_BIRTHDAY_SCHEDULE[call.data].day}"
    month_birth = f"{ALL_BIRTHDAY_SCHEDULE[call.data].month}"
    year_birth = f"{ALL_BIRTHDAY_SCHEDULE[call.data].year}"
    bot.send_message(chat_id=call.from_user.id,
                     text=call.data + ": " + "{day}.".format(
                         day=day_birth if len(day_birth) == 2 else ("0" + day_birth)) +
                          "{month}.".format(month=month_birth if len(month_birth) == 2 else ("0" + month_birth)) +
                          f"{year_birth}")
    bot.answer_callback_query(callback_query_id=call.id)


def happy_birthday():
    """ Отправка поздравления в день рождения """
    greeting_card = requests.get("https://coolsen.ru/wp-content/uploads/2021/10/167-20211025_180551.jpg")
    date_today = datetime.datetime.now()
    for name_birthday_boy, date_of_birth in ALL_BIRTHDAY_SCHEDULE.items():
        if date_today.month == date_of_birth.month:
            if date_today.day == date_of_birth.day:
                bot.send_message(chat_id=PERSON_ID[name_birthday_boy], text=f"С Днем Рождения, {name_birthday_boy}!!!")
                bot.send_photo(chat_id=PERSON_ID[name_birthday_boy], photo=greeting_card.content)


def run_schedule_telegram_bot():
    schedule.every().day.at("13:37").do(happy_birthday)

    while True:
        schedule.run_pending()
        time.sleep(1)


def run_Bot():
    while True:
        try:
            bot.polling()
        except Exception as err:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={ADMIN_CHAT_ID}"
                          f"&text={datetime.datetime.now()} ::: {err.__class__} ::: {err}")


if __name__ == "__main__":
    Thread(target=run_Bot).start()
    Thread(target=run_schedule_telegram_bot()).start()
