import telebot
import sqlite3
from random import choice
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN


with sqlite3.connect('telegram_bot.db', check_same_thread=False) as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    table_num INTEGER NOT NULL,
    order_dishes VARCHAR NOT NULL)""")


bot = telebot.TeleBot(BOT_TOKEN)

phrases = ['fine', 'amazing', 'wonderful']

menu = {'Fish': 1000, 'Meat': 2000, 'Juice': 300}

name = None
table_number = None
order_list = list()
order_str = None


@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.send_message(message.chat.id, 'Hi! I can help you to choose and order food you want!\nEnter your name')
    bot.register_next_step_handler(msg, get_name)


def get_name(message):
    global name
    if name is None:
        name = message.text
    msg = bot.send_message(message.chat.id, 'Now enter the number of the table you are sitting at (1-20)')
    bot.register_next_step_handler(msg, get_table)


def is_correct_table_num(message):
    if message.text.isdigit() and int(message.text) in range(1, 21):
        return True
    else:
        msg = bot.send_message(message.chat.id, 'Incorrect value. Enter the number of the table again (1 - 20)')
        bot.register_next_step_handler(msg, is_correct_table_num)


def get_table(message):
    global table_number
    if is_correct_table_num(message) and table_number is None:
        table_number = message.text
    bot.send_message(message.chat.id, 'Would you like anything?', reply_markup=gen_markup())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global phrases



def gen_markup():
    markup = InlineKeyboardMarkup()
    for i_dish, i_price in menu.items():
        dish = InlineKeyboardButton(resize_markup=True, one_time_keyboard=True, text='{dish} - {price}'.format(
            dish=i_dish, price=i_price), callback_data=i_dish)
        markup.add(dish)
    call_no = InlineKeyboardButton(resize_markup=True, one_time_keyboard=True, text='No', callback_data='No')
    markup.add(call_no)
    return markup


def get_order(message):
    global order_list
    order_list.append(message.text)
    get_table(message)


def check_order(message):
    global order_list, order_str
    order_str = ', '.join(order_list)
    bot.send_message(message.chat.id, 'Let`s check your order.\n'
                                      'Table number - {table_number}\n'
                                      'Order - {order}'.format(table_number=table_number,
                                                               order=order_str))
    msg = bot.send_message(message.chat.id, 'Is everything right?', reply_markup=gen_markup_2())
    bot.register_next_step_handler(msg, finish)


def gen_markup_2():
    markup = ReplyKeyboardMarkup()
    call_yes = KeyboardButton('Yes')
    call_no = KeyboardButton('No')
    markup.add(call_yes, call_no)
    return markup


def finish(message):
    global name, table_number, order_list, order_str
    if message.text == 'Yes':
        bot.send_message(message.chat.id, 'Order will be ready in 20 minutes')
        insert_data(name, table_number, order_str)
        name = None
        table_number = None
        order_list.clear()
        order_str = None
    elif message.text == 'No':
        table_number = None
        order_list.clear()
        order_str = None
        get_name(message)
    else:
        msg = bot.send_message(message.chat.id, 'There is no such answer. Is everything right with your order?',
                               reply_markup=gen_markup_2())
        bot.register_next_step_handler(msg, finish)


def insert_data(u_name, u_table, u_order):
    cursor.execute('INSERT INTO users (name, table_num, order_dishes) VALUES (?, ?, ?)',
                   (u_name, u_table, u_order))
    conn.commit()


bot.polling(non_stop=True)
