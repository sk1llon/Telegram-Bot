import telebot
import sqlite3
from random import choice
from telebot.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton)
from config import BOT_TOKEN


with sqlite3.connect('telegram_bot.db', check_same_thread=False) as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    table_num INTEGER NOT NULL,
    order_dishes VARCHAR NOT NULL)""")


bot = telebot.TeleBot(BOT_TOKEN)

menu = {'Рыба': 1000, 'Мясо': 2000, 'Сок': 300}

choose_answer = ['Прекрасный выбор!', 'Желаете что-нибудь ещё?', 'Замечательно!', 'Великолепно!']
name = None
table_number = None
order_list = list()
order_str = None


@bot.message_handler(commands=['start'])
def start(message):
    """
    Приветствие и получение имени пользователя
    """
    msg = bot.send_message(message.chat.id,
                           'Привет! Я бот, который поможет вам выбрать и заказать еду в нашем ресторане'
                           '\n\nВведите ваше имя')
    bot.register_next_step_handler(msg, get_name)


def get_name(message):
    """
    Получение номера стола
    """
    global name
    if name is None:
        name = message.text
    msg = bot.send_message(message.chat.id, '{name}, введите номер стола за которым вы сидите (от 1 до 20)'.format(
        name=name
    ))
    bot.register_next_step_handler(msg, is_correct_table_num)


def is_correct_table_num(message):
    """
    Проверка корректности введённого номера стола
    """
    if message.text.isdigit() and int(message.text) in range(1, 21):
        get_table(message)
    else:
        msg = bot.send_message(message.chat.id, 'Неверное значение\nВведите номер стола ещё раз (от 1 до 20)')
        bot.register_next_step_handler(msg, is_correct_table_num)


def get_table(message):
    """
    Получаем список блюд от пользователя
    """
    global table_number
    table_number = message.text
    bot.send_message(message.chat.id, 'Что-нибудь желаете? Нажмите "Всё" когда закончите', reply_markup=gen_markup())


def gen_markup():
    """
    Создание готовых ответов для пользователя (список блюд)
    """
    markup = InlineKeyboardMarkup()
    for i_dish, i_price in menu.items():
        dish = InlineKeyboardButton(resize_markup=True, text='{dish} - {price}'.format(
            dish=i_dish, price=i_price), callback_data=i_dish)
        markup.add(dish)
    call_no = InlineKeyboardButton(resize_markup=True, text='Всё', callback_data='Всё')
    markup.add(call_no)
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'Всё':
        check_order(call)
    else:
        get_order(call)
        bot.send_message(call.message.chat.id, text=choice(choose_answer))


def get_order(call):
    global order_list
    order_list.append(call.data)
    if len(order_list) == 0:
        bot.send_message(call.message.chat.id, 'Что-нибудь желаете? Нажмите "Всё" когда закончите',
                         reply_markup=gen_markup())


def check_order(call):
    """
    Проверяем заказ
    """
    global order_list, order_str
    order_str = ', '.join(order_list)
    bot.send_message(call.message.chat.id, 'Давайте проверим введённые вами данные\n'
                                           'Номер стола - {table_number}\n'
                                           'Заказ - {order}'.format(table_number=table_number,
                                                                    order=order_str))
    msg = bot.send_message(call.message.chat.id, 'Всё верно?', reply_markup=gen_markup_2())
    bot.register_next_step_handler(msg, finish)


def gen_markup_2():
    """
    Создание готовых ответов для пользователя
    """
    markup = ReplyKeyboardMarkup()
    markup.row_width = 2
    call_yes = KeyboardButton('Да')
    call_no = KeyboardButton('Нет')
    markup.add(call_yes, call_no)
    return markup


def finish(message):
    """
    Проверяем на правильности введённые данные
    """
    global name, table_number, order_list, order_str
    if message.text == 'Да':
        bot.send_message(message.chat.id, 'Заказ будет готов в течение 20 минут')
        insert_data(name, table_number, order_str)
        name = None
        table_number = None
        order_list.clear()
        order_str = None
    elif message.text == 'Нет':
        table_number = None
        order_list.clear()
        order_str = None
        get_name(message)
    else:
        msg = bot.send_message(message.chat.id, 'Я вас немного не понял. Вся ли информация верна?',
                               reply_markup=gen_markup_2())
        bot.register_next_step_handler(msg, finish)


def insert_data(u_name, u_table, u_order):
    cursor.execute('INSERT INTO users (name, table_num, order_dishes) VALUES (?, ?, ?)',
                   (u_name, u_table, u_order))
    conn.commit()


bot.polling(non_stop=True)
