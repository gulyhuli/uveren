#! encoding: utf-8
import telebot
import os
import time
from datetime import datetime
from db_layer import db_acces
from db_layer import states
from telebot import types, apihelper
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import configparser
import atexit

# если в окуржении есть переменная HEROKU, значит получаем токен из переменной окружения
if 'HEROKU' in list(os.environ.keys()):
    TOKEN = str(os.environ.get('TOKEN'))
# иначе импортируем его из скрытого в файлы в папке проекта
else:
    import token_key
    TOKEN = token_key.token

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
config = configparser.ConfigParser()
config.read('conf.ini')
ADMIN_ID = 446116692
MY_ID = 410634632
bot_access_text = 'Чтобы начать продвижение вашего канала, вам нужно: \n\n1. Добавить этого бота в администраторы ' \
                  'вашего канала\n*абсолютно безопасно - боту хватит одного любого разрешения, например, ' \
                  'на добавление пользователей*\n\n2. Переслать пост из вашего канала в чат бота\n\n3. ' \
                  'Проследовать дальнейшим указаниям бота \n' \
                  '[инструкция для помощи](http://telegra.ph/Kak-sdelat-bota-administratorom-02-08)'


def save_data():
    with open('conf.ini', 'w') as conf:
            config.write(conf)


def update_users():
    if datetime.now().hour == 0:
        config.set('stat', 'new_users', '0')
        save_data()


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=update_users,
    trigger=IntervalTrigger(hours=1),
    id='my_job',
    name='Clean list of new users',
    replace_existing=True
)
atexit.register(lambda: scheduler.shutdown())


def get_main_menu_markup():
    markup = types.ReplyKeyboardMarkup()
    markup.row('👁 Смотреть пост', '➕ Подписаться на канал')
    markup.row('🚀 Для рекламодателей')
    markup.row('📱 Мой профиль', '💰 Баланс')
    markup.row('📊 Статистика', '⚠️ Правила')
    markup.resize_keyboard = True
    return markup


def get_cancel_markup():
    markup = types.ReplyKeyboardMarkup()
    markup.row('Отмена')
    markup.resize_keyboard = True
    return markup


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda mes: mes.text == '✅ Главное меню')
def greeting(mes):
    markup = get_main_menu_markup()
    user = db_acces.get_user(mes.from_user.id)
    if user is None:
        db_acces.create_user(mes.from_user.first_name, mes.from_user.id)
        user = db_acces.get_user(mes.from_user.id)
        current_users = int(config['stat']['new_users']) + 1
        config.set('stat', 'new_users', str(current_users))
        save_data()
    bot.send_message(mes.from_user.id, 'Приветствую, {name}!'.format(name=user.name),
                     reply_markup=markup)


@bot.message_handler(content_types=['text'], func=lambda mes: db_acces.get_user(mes.from_user.id) is None)
def other_message(mes):
    bot.send_message(mes.from_user.id, 'Какая-то ошибка, введите /start для начала работы',
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda mes: mes.text == '🚀 Для рекламодателей' and
                     db_acces.get_user(mes.from_user.id) is not None)
def for_customers(mes: types.Message):
    text = '*Добро пожаловать!*\nЧерез бота Вы можете заказать подписчиков в Ваш канал или купить просмотры поста из ' \
           'Вашего канала.\nОба действия *повышают* цену канала и/или рекламы.\nТакже Вы можете заказать рекламную ' \
           'рассылку на указанную аудиторию.\nВыберите услугу в меню. '
    markup = types.ReplyKeyboardMarkup()
    markup.row('Подписчики', 'Просмотры')
    markup.row('Мои заказы')
    markup.row('✅ Главное меню')
    markup.row_width = True
    markup.resize_keyboard = True
    bot.send_message(mes.from_user.id, text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(func=lambda mes: mes.text == 'Подписчики' and
                     db_acces.get_user_state(mes.from_user.id) is states.CHOOSE_OPTION)
def order_channel(mes: types.Message):
    db_acces.set_user_state(mes.from_user.id, states.FORWARD_POST_FOR_SUB)
    bot.send_message(mes.from_user.id, bot_access_text, parse_mode='Markdown',
                     reply_markup=get_cancel_markup())


@bot.message_handler(func=lambda mes: mes.text == 'Просмотры' and
                     db_acces.get_user_state(mes.from_user.id) is states.CHOOSE_OPTION)
def order_post(mes: types.Message):
    db_acces.set_user_state(mes.from_user.id, states.FORWARD_POST_FOR_WATCH)
    bot.send_message(mes.from_user.id, 'Перешлите желаемый для продвижения пост', parse_mode='Markdown',
                     reply_markup=get_cancel_markup())


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) is states.FORWARD_POST_FOR_WATCH or
                     db_acces.get_user_state(mes.from_user.id) is states.FORWARD_POST_FOR_SUB)
def forward_message(mes: types.Message):
    if not mes.text == 'Отмена':
        if db_acces.get_user_state(mes.from_user.id) == states.FORWARD_POST_FOR_WATCH and mes.forward_from_chat is not None:
            username = mes.from_user.id
            post_id = mes.message_id
            user = db_acces.get_user_state(mes.from_user.id)
            db_acces.create_order_post(post_id, username, 0.5, 50, user)
            bot.send_message(mes.from_user.id,
                             '👑 Все сделано правильно!\n👥Теперь введите стоимость 1 просмотра вашего '
                             'поста в рублях (минимальная стоимость: 0.04 рублей)')
            db_acces.set_user_state(mes.from_user.id, states.SET_PRICE_FOR_WATCH)
        elif db_acces.get_user_state(mes.from_user.id) == states.FORWARD_POST_FOR_SUB and \
                mes.forward_from_chat is not None:

            username = mes.forward_from_chat.username
            try:
                bot.get_chat_members_count('@' + username)
            except apihelper.ApiException:
                bot.send_message(mes.from_user.id, 'Бот не является администратором канала!')
            else:
                user = db_acces.get_user_state(mes.from_user.id)
                db_acces.create_channel(username, 0.5, 50, user)
                bot.send_message(mes.from_user.id,
                                 '👑 Все сделано правильно!\n👥Теперь введите стоимость 1 подписчика на ваш '
                                 'канал в рублях (минимальная стоимость: 0.5 рублей')
                db_acces.set_user_state(mes.from_user.id, states.SET_PRICE_FOR_SUB)

        else:
            bot.send_message(mes.from_user.id, 'Какая-то ошибка, попробуйте еще раз', reply_markup=get_cancel_markup())
    else:
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_main_menu_markup())


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) == states.SET_PRICE_FOR_WATCH)
def set_price_for_watch(mes: types.Message):
    if not mes.text == 'Отмена':
        try:
            price = float(mes.text)
        except ValueError:
            bot.send_message(mes.from_user.id, 'Неверное значение. Попробуйте еще раз')
        else:
            if price >= 0.04:
                bot.send_message(mes.from_user.id, 'Отлично! Теперь введите желаемое количество просмотров',
                                 reply_markup=types.ReplyKeyboardRemove())
                db_acces.set_price_for_new_post(mes.from_user.id, price)
                db_acces.set_user_state(mes.from_user.id, states.SET_COUNT_OF_WATCH)
            else:
                bot.send_message(mes.from_user.id, 'Минимальная стоимость просмотра: 0.04р')
    else:
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        db_acces.delete_post_order(mes.from_user.id)
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_main_menu_markup())


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) == states.SET_COUNT_OF_WATCH)
def set_count_of_watch(mes: types.Message):
    try:
        count = int(mes.text)
    except ValueError:
        bot.send_message(mes.from_user.id, 'Неверное значение. Попробуйте еще раз')
    else:
        if count >= 50:
            price = db_acces.get_price_for_new_post(mes.from_user.id)
            db_acces.set_watchs_for_new_post(mes.from_user.id, count)
            res = count * price
            bot.send_message(mes.from_user.id, 'Отлично! Итоговая стоимость продвижения '
                                               'составит {count} * {price} = {res}р.'
                                               .format(count=count, price=price, res=res))
            markup = types.ReplyKeyboardMarkup()
            markup.row('Подтвердить ✅')
            markup.row('Отмена')
            markup.resize_keyboard = True
            bot.send_message(mes.from_user.id, 'Всё верно?', reply_markup=markup)
            db_acces.set_user_state(mes.from_user.id, states.CONFIRM_WATCHS)
        else:
            bot.send_message(mes.from_user.id, 'Минимальное количество: 50')


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) == states.CONFIRM_WATCHS)
def confirm_watches(mes: types.Message):
    if mes.text == 'Подтвердить ✅':
        price = db_acces.get_price_for_new_post(mes.from_user.id)
        count = db_acces.get_watchs_for_new_post(mes.from_user.id)
        end_price = count * price
        balance = db_acces.get_user_balance(mes.from_user.id)
        if (balance - end_price) >= 0:
            db_acces.set_user_balance(mes.from_user.id, balance - end_price)
            db_acces.publish_post_order(mes.from_user.id)
            bot.send_message(mes.from_user.id, 'Ваш заказ успешно оформлен!', reply_markup=get_main_menu_markup())
            db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        else:
            bot.send_message(mes.from_user.id, 'Недостаточно средств! Пополните свой баланс и повторите заказ снова',
                             reply_markup=get_main_menu_markup())
            db_acces.delete_post_order(mes.from_user.id)
            db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
    elif mes.text == 'Отмена':
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_main_menu_markup())
        db_acces.delete_post_order(mes.from_user.id)
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
    else:
        bot.send_message(mes.from_user.id, 'Какой-то странный ответ. Попробуйте еще раз')


# ------ Channels -------


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) == states.SET_PRICE_FOR_SUB)
def set_price_for_sub(mes: types.Message):
    if not mes.text == 'Отмена':
        try:
            price = float(mes.text)
        except ValueError:
            bot.send_message(mes.from_user.id, 'Неверное значение. Попробуйте еще раз')
        else:
            if price >= 0.5:
                bot.send_message(mes.from_user.id, 'Отлично! Теперь введите желаемое количество подписчиков',
                                 reply_markup=types.ReplyKeyboardRemove())
                db_acces.set_price_for_new_channel(mes.from_user.id, price)
                db_acces.set_user_state(mes.from_user.id, states.SET_COUNT_OF_SUB)
            else:
                bot.send_message(mes.from_user.id, 'Минимальная стоимость подписки: 0.25р')
    else:
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        db_acces.delete_channel_order(mes.from_user.id)
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_main_menu_markup())


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) == states.SET_COUNT_OF_SUB)
def set_count_of_sub(mes: types.Message):
    try:
        count = int(mes.text)
    except ValueError:
        bot.send_message(mes.from_user.id, 'Отлично! Теперь введите желаемое количество просмотров')
    else:
        if count >= 50:
            price = db_acces.get_price_for_new_channel(mes.from_user.id)
            db_acces.set_sub_for_new_channel(mes.from_user.id, count)
            res = count * price
            bot.send_message(mes.from_user.id, 'Отлично! Итоговая стоимость продвижения '
                                               'составит {count} * {price} = {res}р.'
                                               .format(count=count, price=price, res=res))
            markup = types.ReplyKeyboardMarkup()
            markup.row('Подтвердить ✅')
            markup.row('Отмена')
            markup.resize_keyboard = True
            bot.send_message(mes.from_user.id, 'Всё верно?', reply_markup=markup)
            db_acces.set_user_state(mes.from_user.id, states.CONFIRM_SUB)
        else:
            bot.send_message(mes.from_user.id, 'Минимальное количество: 50')


@bot.message_handler(func=lambda mes: db_acces.get_user_state(mes.from_user.id) == states.CONFIRM_SUB)
def confirm_sub(mes: types.Message):
    if mes.text == 'Подтвердить ✅':
        price = db_acces.get_price_for_new_channel(mes.from_user.id)
        count = db_acces.get_sub_for_new_channel(mes.from_user.id)
        end_price = price * count
        balance = db_acces.get_user_balance(mes.from_user.id)
        if (balance - end_price) >= 0:
            db_acces.set_user_balance(mes.from_user.id, balance - end_price)
            db_acces.publish_channel_order(mes.from_user.id)
            bot.send_message(mes.from_user.id, 'Ваш заказ успешно оформлен!', reply_markup=get_main_menu_markup())
            db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        else:
            bot.send_message(mes.from_user.id, 'Недостаточно средств! Пополните свой баланс и повторите заказ снова',
                             reply_markup=get_main_menu_markup())
            db_acces.delete_post_order(mes.from_user.id)
            db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
    elif mes.text == 'Отмена':
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_main_menu_markup())
        db_acces.delete_post_order(mes.from_user.id)
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
    else:
        bot.send_message(mes.from_user.id, 'Какой-то странный ответ. Попробуйте еще раз')


@bot.message_handler(func=lambda mes: mes.text == 'Мои заказы')
def my_orders(mes: types.Message):
    text = '🕵 Ваши текущие заказы 💰\n\n'
    posts = db_acces.get_user_order_posts(mes.from_user.id)
    channels = db_acces.get_user_order_channels(mes.from_user.id)
    if channels.count() > 0:
        for c in channels:
            username = c.username
            count = c.how_many_sub
            price = c.price_for_sub
            end_price = c.price_for_order
            text += '📣 Канал @{username}\n' \
                    'стоимость: заказа - подписки: {end_price}р. - {price}р.\n' \
                    'подписок осталось: {count}\n\n'.format(username=username, end_price=end_price,
                                                            price=price, count=count)
    if posts.count() > 0:
        i = 0
        for p in posts:
            i += 1
            username = p.from_chat_username
            count = p.how_many_watch
            price = p.price_for_watch
            end_price = p.price_for_order
            id_p = p.from_message_id
            text += '📣 пост из @{username} №{i}\n' \
                    'стоимость: заказа - просмотра: {end_price}р. - {price}р.\n' \
                    'просмотров осталось: {count}\n\n'.format(username=username, i=i, end_price=end_price,
                                                              price=price, count=count, id=id_p)
    else:
        text = ' У вас нет заказов! ✋'
    bot.send_message(mes.from_user.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda mes: mes.text == '📱 Мой профиль' and db_acces.get_user(mes.from_user.id) is not None)
def profile(mes: types.Message):
    user = db_acces.get_user(mes.from_user.id)
    uname = 'Нет'
    if mes.from_user.username is not None:
        uname = mes.from_user.username
    text = '<b>Твой профиль, {name}</b> \n\n' \
           '🔑Мой id: {id} \n' \
           '👤Мой username: {uname} \n' \
           '➕Сделано подписок: {sub} \n' \
           '👀Просмотрено постов: {post}\n' \
           '🍷Доход с подписок: {isub}р \n' \
           '🍸Доход с просмотров: {iwatch}р \n' \
           '💰Текущий баланс: {balance}р \n' \
           '💳Выведено всего: {ded}р \n' \
           '💰Заработано всего: {earned}р'\
        .format(name=user.name, id=str(user.telegram_id),
                uname='@' + uname, sub=user.made_sub,
                post=user.watched_posts, isub=user.income_sub,
                iwatch=user.income_watched, balance=user.balance,
                ded=user.deduced, earned=user.earned)
    bot.send_message(mes.from_user.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda mes: mes.text == '💰 Баланс' and db_acces.get_user(mes.from_user.id) is not None)
def get_balance(mes: types.Message):
    balance = db_acces.get_user_balance(mes.from_user.id)
    markup = types.ReplyKeyboardMarkup()
    markup.row('💳 Вывод', '💵 Пополнение')
    markup.row('✅ Главное меню')
    markup.resize_keyboard = True
    bot.send_message(mes.from_user.id, 'Ваш текущий баланс: {b} рублей'.format(b=str(balance)),
                     reply_markup=markup)


@bot.message_handler(func=lambda mes: mes.text == '💵 Пополнение' and db_acces.get_user(mes.from_user.id) is not None)
def put_money(mes: types.Message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('Qiwi', 'Yandex.Money', 'Другой')
    markup.row('✅ Главное меню')
    bot.send_message(mes.from_user.id, 'Выберите способ пополнения', reply_markup=markup)


@bot.message_handler(func=lambda mes: mes.text == 'Qiwi' and db_acces.get_user(mes.from_user.id) is not None)
def put_money_qiwi(mes: types.Message):
    user_id = str(mes.from_user.id)
    text = '🔥Для пополнения баланса переведите нужную сумму ' \
           'на QIWI кошелек с номером 79184334240 и следующим комментарием *{id}* к переводу *(важно, иначе платеж не засчитается!)*.\n' \
           '⚡️Сумма будет зачислена в течение нескольких минут.'.format(id=user_id)
    markup = types.ReplyKeyboardMarkup()
    markup.row('✅ Главное меню')
    bot.send_message(mes.from_user.id, text, reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda mes: mes.text == 'Yandex.Money' and db_acces.get_user(mes.from_user.id) is not None)
def put_money_yandex(mes: types.Message):
    user_id = str(mes.from_user.id)
    text = '🔥Для пополнения баланса переведите нужную сумму ' \
           'по [ссылке](https://money.yandex.ru/to/410016312082017) и следующим комментарием *{id}* к переводу *(важно, иначе платеж не засчитается!)*.\n' \
           '⚡️Сумма будет зачислена в течение нескольких минут.'.format(id=user_id)
    markup = types.ReplyKeyboardMarkup()
    markup.row('✅ Главное меню')
    bot.send_message(mes.from_user.id, text, reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda mes: mes.text == 'Другой' and db_acces.get_user(mes.from_user.id) is not None)
def put_money_other(mes: types.Message):
    user_id = str(mes.from_user.id)
    text = '🔥Для пополнения баланса другим способом ' \
           'обратитесь к администратору 👤 @Evgenyadmin со следующим комментарием *{id}* к переводу *(важно, иначе платеж не засчитается!)*.\n' \
           '⚡️Сумма будет после согласования.'.format(id=user_id)
    markup = types.ReplyKeyboardMarkup()
    markup.row('✅ Главное меню')
    bot.send_message(mes.from_user.id, text, reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda mes: mes.text == '💳 Вывод' and db_acces.get_user(mes.from_user.id) is not None)
def take_money(mes: types.Message):
    user_id = str(mes.from_user.id)
    text = 'Для вывода средств, обратитесь к администратору @Evgenyadmin 👤, со следующим комментарием *{id}*'.format(id=user_id)
    markup = types.ReplyKeyboardMarkup()
    markup.row('✅ Главное меню')
    bot.send_message(mes.from_user.id, text, reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda mes: mes.text == '⚠️ Правила')
def rules(mes: types.Message):
    text = '!!!ПРАВИЛА использования бота \n\n👨‍💻 Исполнителям ЗАПРЕЩАЕТСЯ:\n\n1.' \
           ' Отписываться от канала (в течении 7 ' \
           'дней) ❗штраф 7 рублей за отписку с одного канала.\n\n2. Создавать более одного аккаунта для выполнения ' \
           'заданий (* попытки вывода средств на одинаковые кошельки *) 😱 баланс пользователя будет обнулён при ' \
           'выводе средств\n\n👔 Заказчикам ЗАПРЕЩАЕТСЯ:\n\n1. Размещать каналы, группы и посты мошеннического, ' \
           'порнографического, террористического, наркотического, суицидального или дипрессивного содержания 😱 заказ ' \
           'будет удалён полностью без возврата средств\n\n2. Убирать права у бота до завершения заказа 😱 заказ ' \
           'будет удалён полностью без возврата средств❗️ ' \
           '*рекомендуется не удалять бота из администраторов в течении ' \
           '7 дней с момента ОКОНЧАНИЯ заказа, иначе проверка подписки пользователей на Ваш канал будет ' \
           'невозможна*\n\n❕Тех-поддержка:  @Evgenyadmin '
    bot.send_message(mes.from_user.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda mes: mes.text == '📊 Статистика')
def stat(mes: types.Message):
    users = str(db_acces.get_users().count())
    channels = str(db_acces.get_channels().count())
    posts = str(db_acces.get_posts().count())
    new_users = config['stat']['new_users']
    end_channels = config['stat']['end_channels']
    end_posts = config['stat']['end_posts']
    got_money = config['stat']['got_money']
    gave_money = config['stat']['gave_money']

    text = '📊 *Статистика проекта:*\n\n' \
           '👥Всего пользователей: {u}\n' \
           '👤Новых за сегодня: {nu}\n' \
           '🎯Каналов на продвижении: {c}\n' \
           '🎬Постов на продвижении: {p}\n' \
           '🎯Обработано каналов: {nc}\n' \
           '🎬Обработано постов: {np}\n' \
           '💵Общий заработок: {gm}р\n' \
           '💳Выплачено денег: {gam}р\n'.format(
               u=users,
               nu=new_users,
               c=channels,
               p=posts,
               nc=end_posts,
               np=end_posts,
               gm=got_money,
               gam=gave_money
           )
    bot.send_message(mes.from_user.id, text, parse_mode='Markdown')


@bot.message_handler(func=lambda mes: mes.text == '👁 Смотреть пост')
def watch_post(mes: types.Message):
    queue = db_acces.get_user_pos_post(mes.from_user.id)
    post = db_acces.get_post(queue)
    if post is not None:
        money = post.price_for_watch / 2
        username = post.from_chat_username
        bot.forward_message(mes.from_user.id, username, post.from_message_id)
        msg = bot.send_message(mes.from_user.id, 'Смотрим на пост 3 секунды. 3... 2... 1...')
        db_acces.decrement_watchs(queue)
        db_acces.increment_watched_posts(mes.from_user.id)
        db_acces.add_sum_to_balance(mes.from_user.id, money)
        db_acces.add_sum_to_earned(mes.from_user.id, money)
        db_acces.add_income_watched(mes.from_user.id, money)
        time.sleep(3)
        bot.edit_message_text('Отлично! Вы заработали {m}р.'.format(m=str(money)), mes.from_user.id, msg.message_id)
        db_acces.set_user_pos_post(mes.from_user.id, queue + 1)

        bot.send_message(mes.from_user.id, 'Продолжайте в том же духе', reply_markup=get_main_menu_markup())

        if db_acces.get_post_count_of_watch(queue) == 0:
            new_post = int(config['stat']['end_posts']) + 1
            config.set('stat', 'end_posts', str(new_post))
            save_data()
            db_acces.delete_channel(queue)

            db_acces.delete_post(queue)
            db_acces.decrement_user_pos_post(queue)
    else:
        bot.send_message(mes.from_user.id, 'Пока смотреть нечего, проверьте чуть позже')


@bot.message_handler(func=lambda mes: mes.text == '➕ Подписаться на канал')
def subscribe_to_channel(mes: types.Message):
    queue = db_acces.get_user_pos_channel(mes.from_user.id)
    channel = db_acces.get_channel(queue)
    if channel is not None:
        money = channel.price_for_sub
        link = db_acces.get_channel_link(queue)
        keyboard = types.InlineKeyboardMarkup()
        button_sub = types.InlineKeyboardButton(text='Подписаться на канал', url=link)
        button_check = types.InlineKeyboardButton('Проверить подписку на канал', callback_data=channel.username)
        keyboard.add(button_sub, button_check)
        bot.send_message(mes.from_user.id, 'Подпишитесь на канал, чтобы получить деньги', reply_markup=keyboard)
    else:
        bot.send_message(mes.from_user.id, 'Пока предложений нет, проверьте чуть позже', reply_markup=get_main_menu_markup())


@bot.callback_query_handler(func=lambda call: True)
def check_subscription(call: types.CallbackQuery):
    # TODO: написать систему проверки прав админа у бота
    username = call.data
    try:
        if bot.get_chat_member('@' + username, call.from_user.id) is not None:
            queue = db_acces.get_user_pos_channel(call.from_user.id)
            channel = db_acces.get_channel(queue)

            if channel is None:
                bot.delete_message(call.from_user.id, call.message.message_id)
                return

            money = channel.price_for_sub / 2

            db_acces.decrement_sub(queue)
            db_acces.increment_made_sub(call.from_user.id)
            db_acces.add_sum_to_balance(call.from_user.id, money)
            db_acces.add_sum_to_earned(call.from_user.id, money)
            db_acces.add_income_sub(call.from_user.id, money)

            bot.edit_message_text('Отлично! Вы заработали {m}р.'.format(m=str(money)), call.from_user.id, call.message.message_id,
                                  reply_markup=get_main_menu_markup())

            db_acces.set_user_pos_channel(call.from_user.id, queue + 1)
            if db_acces.get_channel_count_of_sub(queue) == 0:
                new_channel = int(config['stat']['end_channels']) + 1
                config.set('stat', 'end_channels', str(new_channel))
                save_data()
                db_acces.delete_channel(queue)
                db_acces.decrement_user_pos_channel(queue)
        else:
            bot.send_message(call.from_user.id, 'Вы не подписались на канал')
    except apihelper.ApiException:
            queue = db_acces.get_user_pos_channel(call.from_user.id)
            channel = db_acces.get_channel(queue)

            if channel is None:
                bot.delete_message(call.from_user.id, call.message.message_id)
                return

            money = channel.price_for_sub / 2

            db_acces.decrement_sub(queue)
            db_acces.increment_made_sub(call.from_user.id)
            db_acces.add_sum_to_balance(call.from_user.id, money)
            db_acces.add_sum_to_earned(call.from_user.id, money)
            db_acces.add_income_sub(call.from_user.id, money)

            bot.edit_message_text('Отлично! Вы заработали {m}р.'.format(m=str(money)), call.from_user.id, call.message.message_id)
            bot.send_message(call.from_user.id, 'Продолжайте в том же духе', reply_markup=get_main_menu_markup())

            db_acces.set_user_pos_channel(call.from_user.id, queue + 1)
            if db_acces.get_channel_count_of_sub(queue) == 0:
                new_channel = int(config['stat']['end_channels']) + 1
                config.set('stat', 'end_channels', str(new_channel))
                save_data()
                db_acces.delete_channel(queue)
                db_acces.delete_channel(queue)
                db_acces.decrement_user_pos_channel(queue)


def get_admin_markup():
    markup = types.ReplyKeyboardMarkup()
    markup.row('Начислить баланс пользователю')
    markup.row('Сделать объявление всем пользователям')
    markup.row('Пользователь вывел сумму')
    markup.row('✅ Главное меню')
    markup.resize_keyboard = True
    return markup


@bot.message_handler(commands=['admin'], func=lambda mes: (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.CHOOSE_OPTION)
@bot.message_handler(func=lambda mes: (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.CHOOSE_OPTION and (mes.text == 'Админ панель 📲'))
def admin_panel(mes: types.Message):
    text = 'Приветствую админ, {u}!'.format(u=mes.from_user.first_name)
    bot.send_message(mes.from_user.id, text, reply_markup=get_admin_markup())


@bot.message_handler(func=lambda mes: mes.text == 'Начислить баланс пользователю' and
                     (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.CHOOSE_OPTION)
def add_sum_to_balance_id(mes: types.Message):
    text = 'Чтобы пополнить баланс - введи <код пользователя> - <сумма числом>\n\n' \
           'Например: 446116692 - 30'
    markup = types.ReplyKeyboardMarkup()
    markup.row('Отмена')
    markup.resize_keyboard = True
    db_acces.set_user_state(mes.from_user.id, states.ADD_MONEY)
    bot.send_message(mes.from_user.id, text, reply_markup=markup)


@bot.message_handler(func=lambda mes: (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.ADD_MONEY)
def add_sum_to_balance(mes: types.Message):
    if mes.text == 'Отмена':
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_admin_markup())
        return
    try:
        user_id, money = map(int, str(mes.text).split(' - '))
    except ValueError:
        bot.send_message(mes.from_user.id, 'Неверный формат, попробуйте снова')
    else:
        result = db_acces.add_sum_to_balance(user_id, money)
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        if result:
            got_money = int(config['stat']['got_money']) + money
            config.set('stat', 'got_money', str(got_money))
            save_data()
            bot.send_message(user_id, 'На ваш баланс зачислено {}р.'.format(str(money)))
            bot.send_message(mes.from_user.id, 'Баланс пользователя успешно пополнен', reply_markup=get_admin_markup())
        else:
            bot.send_message(mes.from_user.id, 'Ошибка пополнения баланса!', reply_markup=get_admin_markup())


@bot.message_handler(func=lambda mes: mes.text == 'Пользователь вывел сумму' and
                     (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.CHOOSE_OPTION)
def remove_sum_from_balance_id(mes: types.Message):
    text = 'Чтобы уменьшить баланс - введи <код пользователя> - <сумма числом>\n\n' \
           'Например: 446116692 - 30'
    markup = types.ReplyKeyboardMarkup()
    markup.row('Отмена')
    markup.resize_keyboard = True
    db_acces.set_user_state(mes.from_user.id, states.REMOVE_MONEY)
    bot.send_message(mes.from_user.id, text, reply_markup=markup)


@bot.message_handler(func=lambda mes: (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.REMOVE_MONEY)
def remove_sum_from_balance(mes: types.Message):
    if mes.text == 'Отмена':
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        bot.send_message(mes.from_user.id, 'Отменено', reply_markup=get_admin_markup())
        return
    try:
        user_id, money = map(int, str(mes.text).split(' - '))
    except ValueError:
        bot.send_message(mes.from_user.id, 'Неверный формат, попробуйте снова')
    else:
        balance = db_acces.get_user_balance(user_id)
        if balance is None:
            bot.send_message(mes.from_user.id, 'Такого счета не существует', reply_markup=get_admin_markup())
            db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
            return
        if (balance - money) <= 0:
            result = db_acces.set_user_balance(user_id, 0)
        else:
            result = db_acces.set_user_balance(user_id, balance - money)
        db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
        if result:
            gave_money = int(config['stat']['gave_money']) + money
            config.set('stat', 'gave_money', str(gave_money))
            save_data()
            bot.send_message(user_id, 'C вашего балансв снято {}р.'.format(str(money)))
            bot.send_message(mes.from_user.id, 'Баланс пользователя успешно уменьшен', reply_markup=get_admin_markup())
        else:
            bot.send_message(mes.from_user.id, 'Ошибка уменьшения баланса!', reply_markup=get_admin_markup())


@bot.message_handler(func=lambda mes: mes.text == 'Сделать объявление всем пользователям' and
                     (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.CHOOSE_OPTION)
def insert_text(mes: types.Message):
    text = 'Данная опция отправляет всем пользователем объявление в разметке Markdown \n\n' \
           'Справка по разметке: \n\n' \
           '*Жирный*\n_Курсив_\n[название URL](http://www.example.com/)\n`код в виде строки`\n\n' \
           'Отправь текст, чтобы сделать объявление'
    db_acces.set_user_state(mes.from_user.id, states.SHARE_INFO)
    bot.send_message(mes.from_user.id, text, reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda mes: (mes.from_user.id == ADMIN_ID or mes.from_user.id == MY_ID) and
                     db_acces.get_user_state(mes.from_user.id) == states.SHARE_INFO)
def share_info(mes: types.Message):
    text = mes.text
    users = db_acces.get_users()
    for u in users:
        try:
            bot.send_message(u.telegram_id, text, parse_mode='Markdown')
        except:
            pass
    db_acces.set_user_state(mes.from_user.id, states.CHOOSE_OPTION)
    bot.send_message(mes.from_user.id, 'Рассылка завершена', reply_markup=get_admin_markup())


@bot.message_handler(content_types=['text'])
def other_message(mes: types.Message):
    bot.send_message(mes.from_user.id, 'Какая-то ошибка, введите /start для начала работы',
                     reply_markup=types.ReplyKeyboardRemove())


# если в окуржении есть переменная HEROKU, значит поднимаем сервер
# иначе запускаем прослушку
if 'HEROKU' in list(os.environ.keys()):
    @server.route('/' + TOKEN, methods=['POST'])
    def get_message():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    @server.route('/')
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url='https://my-money-bot.herokuapp.com/' + TOKEN)
        return '!', 200
    if __name__ == '__main__':
        db_acces.init_db()
        server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
else:
    bot.remove_webhook()
    bot.polling(True)
