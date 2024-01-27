import telebot
import sqlite3
from random import choice
from telebot.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from config import BOT_TOKEN


with sqlite3.connect('telegram_bot.db', check_same_thread=False) as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    table_num INTEGER NOT NULL,
    order_dishes VARCHAR NOT NULL)""")


bot = telebot.TeleBot(BOT_TOKEN)


menu = {'Супы': {'Борщ со сметаной': 390, 'Суп лапша куриная с яйцом': 390},
        'Горячие блюда': {'Пельмени домашние': 550, 'Филе морского окуня': 950, 'Запеченное филе куриной грудки': 690,
                          'Котлеты куриные с картофельным пюре': 630},
        'Горячие закуски': {'Креветки Темпура': 510, 'Куриные крылья': 510},
        'Салаты': {'Салат "Цезарь" с курицей': 590, 'Салат "Цезарь" с тигровыми креветками': 930,
                   'Салат "Дальневосточный"': 760, 'Салат "Варадеро': 610},
        'Напитки': {'Морс клюквенный': 210, 'Боржоми': 250, 'Апельсиновый сок': 420, 'Яблочный сок': 420}}

choose_answer = ['Прекрасный выбор!', 'Желаете что-нибудь ещё?', 'Замечательно!',
                 'Великолепно!', 'Может быть что-нибудь ещё?']

menu_path = None
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
                           'Привет! Я бот, который поможет вам выбрать и заказать еду в нашем ресторане\n\n'
                           'Введите ваше имя')
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
    bot.send_message(message.chat.id, 'Наше меню',
                     reply_markup=menu_type_markup())


def menu_type_markup():
    """
    Создание готовых ответов для пользователя (список блюд)
    """
    markup = InlineKeyboardMarkup()
    for i_dish in menu.keys():
        dish = InlineKeyboardButton(resize_markup=True, text=i_dish, callback_data=i_dish)
        markup.add(dish)
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обработчик call`ов
    """
    if call.data == 'Меню':
        bot.edit_message_text('Меню', call.message.chat.id, call.message.id, reply_markup=menu_type_markup())
    elif call.data == 'Всё':
        check_order(call)
    elif call.data in menu.keys():
        send_food_categories(call)
    else:
        bot.send_message(call.message.chat.id, text=choice(choose_answer))
        get_order(call)

    
def send_food_categories(call):
    """
    Получает категорию меню выбранную пользователем и выводит блюда данной категории
    """
    if call.data == 'Супы':
        bot.edit_message_text('Супы', call.message.chat.id, call.message.id,
                              reply_markup=order_markup(call.data))
    elif call.data == 'Горячие блюда':
        bot.edit_message_text('Горячие блюда', call.message.chat.id, call.message.id,
                              reply_markup=order_markup(call.data))
    elif call.data == 'Горячие закуски':
        bot.edit_message_text('Горячие закуски', call.message.chat.id, call.message.id,
                              reply_markup=order_markup(call.data))
    elif call.data == 'Салаты':
        bot.edit_message_text('Салаты', call.message.chat.id, call.message.id,
                              reply_markup=order_markup(call.data))
    elif call.data == 'Напитки':
        bot.edit_message_text('Напитки', call.message.chat.id, call.message.id,
                              reply_markup=order_markup(call.data))


def order_markup(menu_type):
    """
    Inline Keyboard для заказа
    """
    global menu_path
    markup = InlineKeyboardMarkup()
    if menu_type in menu.keys():
        menu_path = menu_type
    for i_dish, i_price in menu[menu_path].items():
        dish = InlineKeyboardButton(resize_markup=True, text='{dish} - {price}'.format(
            dish=i_dish,
            price=i_price
        ), callback_data=i_dish)
        markup.add(dish)
    call_no = InlineKeyboardButton(text='Всё', callback_data='Всё')
    menu_call = InlineKeyboardButton(text='Меню', callback_data='Меню')
    markup.add(call_no, menu_call)
    return markup


def get_order(call):
    """
    Составление заказа
    """
    global order_list, menu_path
    order_list.append(call.data)
    bot.edit_message_text(call.message.chat.id, call.message.id, reply_markup=order_markup(menu_path))


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
    msg = bot.send_message(call.message.chat.id, 'Всё верно?', reply_markup=yes_no_markup())
    bot.register_next_step_handler(msg, finish)


def yes_no_markup():
    """
    Создание готовых ответов для пользователя
    """
    markup = ReplyKeyboardMarkup()
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
        bot.send_message(message.chat.id, 'Заказ будет готов в течение 20 минут', reply_markup=ReplyKeyboardRemove())
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
                               reply_markup=yes_no_markup())
        bot.register_next_step_handler(msg, finish)


def insert_data(u_name, u_table, u_order):
    """
    Заносим данные в базу
    """
    cursor.execute('INSERT INTO users (name, table_num, order_dishes) VALUES (?, ?, ?)',
                   (u_name, u_table, u_order))
    conn.commit()


bot.polling(non_stop=True)
