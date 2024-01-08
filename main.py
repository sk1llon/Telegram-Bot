import telebot
import time
from config import BOT_TOKEN, API_KEY
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage


menu = {'Fish': 1, 'Meat': 2, 'Juice': 3}


state_storage = StateMemoryStorage()
bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)


class MyStates(StatesGroup):
    name = State()
    table_number = State()
    order = State()
    print_info = State()


@bot.message_handler(commands=['start'])
def start(message):
    bot.set_state(message.from_user.id, MyStates.name, message.chat.id)
    bot.send_message(message.chat.id, 'Hi! I can help you to choose and order food you want!\nEnter your name')


@bot.message_handler(state='*', commands=['cancel'])
def any_state(message):
    bot.send_message(message.chat.id, 'Your state was cancelled')
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=MyStates.name)
def get_name(message):
    bot.send_message(message.chat.id, 'Now enter the number of the table you are sitting at')
    bot.set_state(message.from_user.id, MyStates.table_number, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['name'] = message.text


@bot.message_handler(state=MyStates.table_number, is_digit=True)
def get_table(message):
    bot.send_message(message.chat.id, 'Our menu:')
    for keys, values in menu.items():
        bot.send_message(message.chat.id, '{key} - {value} rub'.format(key=keys, value=values))
    bot.send_message(message.chat.id, 'What do you want?')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['table'] = message.text
    bot.set_state(message.from_user.id, MyStates.order, message.chat.id)


@bot.message_handler(state=MyStates.table_number, is_digit=False)
def incorrect_table(message):
    bot.send_message(message.chat.id, 'Incorrect value. Enter the number of the table again')


@bot.message_handler(state=MyStates.order)
def get_order(message):
    order_list = []
    bot.set_state(message.from_user.id, MyStates.print_info, message.chat.id)
    while message.text != 'All':
        bot.send_message(message.chat.id, 'Something else?')
        time.sleep(5)
        order_list.append(message.text)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['order'] = order_list


@bot.message_handler(state=MyStates.print_info)
def print_info(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        msg = ("Check your order:\n"
               "Name: {name}\n"
               "Table number: {table}\n"
               "Order: {order}".format(
                name=data['name'],
                table=data['table'],
                order=(dish for dish in data['order'])
               ))
        bot.send_message(message.chat.id, msg, parse_mode='html')
    bot.delete_state(message.from_user.id, message.chat.id)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())

bot.infinity_polling(skip_pending=True)
