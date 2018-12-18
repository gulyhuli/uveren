from db_layer.models import *
import my_logger
import logging


logger = my_logger.get_logger()
logger.setLevel(logging.INFO)


def init_db():
    db.close()
    db.connect()
    db.create_tables([User, OrderPost, OrderChannel], safe=True)


# ------ User -------


def create_user(name: str, telegram_id: int):
    try:
        logger.info('Создание пользователя с nickname {id} ...'.format(id=telegram_id))
        User.create(name=name, telegram_id=telegram_id)
    except Exception:
        logger.error('ошибка создания пользователя!')
        return False
    else:
        logger.info('успешное созданием пользователя {id}'.format(id=telegram_id))
        return True


def get_user(telegram_id: int):
    try:
        logger.info('поиск пользователя с id: {id} ...'.format(id=telegram_id))
        user = User.get(User.telegram_id == telegram_id)
    except DoesNotExist:
        logger.error('ошибка поиска пользователя!')
        return None
    else:
        logger.info('успешное получение пользователя c id: {id}'.format(id=telegram_id))
        return user


def get_users():
    try:
        logger.info('получение всех пользователей')
        users = User.select()
    except DoesNotExist:
        logger.error('ошибка поиска пользователей!')
        return None
    else:
        logger.info('успешное получение пользователей')
        return users


def set_user_state(telegram_id: int, state: int):
    user = get_user(telegram_id)
    if user is not None:
        logger.info('изменение состояние')
        user.state = state
        user.save()
        return True
    else:
        logger.error('ошибка изменения состояния')
        return False


def get_user_state(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        logger.info('получение состояния')
        return user.state
    else:
        logger.error('ошибка получения состояния')
        return None


def get_user_order_channels(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        orders = OrderChannel.select().where(OrderChannel.customer == user and OrderChannel.editing == False)
        return orders
    else:
        return None


def get_user_order_posts(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        orders = OrderPost.select().where(OrderPost.customer == user and OrderPost.editing == False)
        return orders
    else:
        return None


def set_user_pos_post(telegram_id: int, position: int):
    user = get_user(telegram_id)
    if user is not None:
        user.pos_post = position
        user.save()
        return True
    else:
        return False


def decrement_user_pos_post(queue: int):
    users = User.select().where(User.pos_post >= queue)
    for u in users:
        u.pos_post -= 1
        u.save()
    return True


def decrement_user_pos_channel(queue: int):
    users = User.select().where(User.pos_channel >= queue)
    for u in users:
        u.pos_channel -= 1
        u.save()
    return True


def get_user_pos_post(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.pos_post
    else:
        return None


def set_user_pos_channel(telegram_id: int, position: int):
    user = get_user(telegram_id)
    if user is not None:
        user.pos_channel = position
        user.save()
        return True
    else:
        return False


def get_user_pos_channel(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.pos_channel
    else:
        return None


def increment_watched_posts(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        user.watched_posts += 1
        user.save()
        return False
    else:
        return None


def increment_made_sub(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        user.made_sub += 1
        user.save()
        return False
    else:
        return None


def get_income_sub(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.income_sub
    else:
        return None


def add_income_sub(telegram_id: int, count: int):
    user = get_user(telegram_id)
    if user is not None:
        user.income_sub += count
        user.save()
        return True
    else:
        return False


def get_income_watched(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.income_watched
    else:
        return None


def add_income_watched(telegram_id: int, count: int):
    user = get_user(telegram_id)
    if user is not None:
        user.income_watched += count
        user.save()
        return True
    else:
        return False


def get_user_balance(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.balance
    else:
        return None


def set_user_balance(telegram_id: int, sum_set: int):
    user = get_user(telegram_id)
    if user is not None:
        user.balance = sum_set
        user.save()
        return True
    else:
        return False


def add_sum_to_balance(telegram_id: int, sum_add: int):
    user = get_user(telegram_id)
    if user is not None:
        user.balance += sum_add
        user.save()
        return True
    else:
        return False


def add_sum_to_deduced(telegram_id: int, sum_add: int):
    user = get_user(telegram_id)
    if user is not None:
        user.deduced += sum_add
        user.save()
        return True
    else:
        return False


def add_sum_to_earned(telegram_id: int, sum_add: int):
    user = get_user(telegram_id)
    if user is not None:
        user.earned += sum_add
        user.save()
        return True
    else:
        return False


def get_deduced(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.deduced
    else:
        return None


def get_earned(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        return user.earned
    else:
        return None


# ------ OrderPost -------


def create_order_post(from_id: int, from_chat: str, price: float, how_many: int, customer: User):
    try:
        queue = OrderPost.select().count() + 1
        OrderPost.create(queue=queue, from_message_id=from_id, from_chat_username=from_chat,
                         price_for_watch=price, how_many_watch=how_many, customer=customer)
        return True
    except Exception:
        return False


def get_post(queue: int):
    try:
        post = OrderPost.get(OrderPost.queue == queue)
    except DoesNotExist:
        return None
    else:
        return post


def get_posts():
    try:
        logger.info('получение всех постов')
        posts = OrderPost.select()
    except DoesNotExist:
        logger.error('ошибка поиска постов!')
        return None
    else:
        logger.info('успешное получение постов')
        return posts


def get_post_count_of_watch(queue: int):
    post = get_post(queue)
    if post is not None:
        return post.how_many_watch
    else:
        return None


def get_editing_post(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        try:
            post = OrderPost.get(OrderPost.customer == user and OrderPost.editing)
        except DoesNotExist:
            return None
        else:
            return post
    else:
        return None


def delete_post(queue: int):
    post = get_post(queue)
    if post is not None:
        posts = OrderPost.select().where(OrderPost.queue > post.queue)
        for p in posts:
            p.queue -= 1
            p.save()
        post.delete_instance()
        return True
    else:
        return False


def set_price_for_new_post(telegram_id: int, value: float):
    post = get_editing_post(telegram_id)
    if post is not None:
        post.price_for_watch = value
        post.save()
        return True
    else:
        return False


def get_price_for_new_post(telegram_id: int):
    post = get_editing_post(telegram_id)
    if post is not None:
        return post.price_for_watch
    else:
        return None


def set_watchs_for_new_post(telegram_id: int, value: float):
    post = get_editing_post(telegram_id)
    if post is not None:
        post.how_many_watch = value
        post.save()
        return True
    else:
        return False


def get_watchs_for_new_post(telegram_id: int):
    post = get_editing_post(telegram_id)
    if post is not None:
        return post.how_many_watch
    else:
        return None


def publish_post_order(telegram_id: int):
    post = get_editing_post(telegram_id)
    if post is not None:
        post.editing = False
        post.price_for_order = post.how_many_watch * post.price_for_watch
        post.save()
        return True
    else:
        return False


def delete_post_order(telegram_id: int):
    post = get_editing_post(telegram_id)
    if post is not None:
        post.delete_instance()
        return True
    else:
        return False


def get_price_for_watch(queue: int):
    post = get_post(queue)
    if post is not None:
        return post.price_for_watch
    else:
        return None


def get_price_for_post_order(queue: int):
    post = get_post(queue)
    if post is not None:
        return post.price_for_order
    else:
        return None


def decrement_watchs(queue: int):
    post = get_post(queue)
    if post is not None:
        post.how_many_watch -= 1
        post.save()
        return True
    else:
        return False


# ------ OrderChannel -------


def create_channel(username: str, price: float, how_many: int, customer: User):
    try:
        queue = OrderChannel.select().count() + 1
        OrderChannel.create(queue=queue, username=username,
                            price_for_sub=price, how_many_sub=how_many, customer=customer)
        return True
    except Exception:
        return False


def get_channels():
    try:
        logger.info('получение всех постов')
        channels = OrderChannel.select()
    except DoesNotExist:
        logger.error('ошибка поиска постов!')
        return None
    else:
        logger.info('успешное получение постов')
        return channels


def get_channel(queue: int):
    try:
        chanel = OrderChannel.get(OrderChannel.queue == queue)
    except DoesNotExist:
        return None
    else:
        return chanel


def get_editing_channel(telegram_id: int):
    user = get_user(telegram_id)
    if user is not None:
        try:
            channel = OrderChannel.get(OrderChannel.customer == user and OrderChannel.editing)
        except DoesNotExist:
            return None
        else:
            return channel
    else:
        return None


def delete_channel(queue: int):
    channel = get_channel(queue)
    if channel is not None:
        channels = OrderChannel.select().where(OrderChannel.queue > channel.queue)
        for c in channels:
            c.queue -= 1
            c.save()
        channel.delete_instance()
        return True
    else:
        return False


def get_price_for_sub(queue: int):
    channel = get_channel(queue)
    if channel is not None:
        return channel.price_for_sub
    else:
        return None


def get_price_for_sub_order(queue: int):
    channel = get_channel(queue)
    if channel is not None:
        return channel.price_for_order
    else:
        return None


def set_price_for_new_channel(telegram_id: int, value: float):
    channel = get_editing_channel(telegram_id)
    if channel is not None:
        channel.price_for_sub = value
        channel.save()
        return True
    else:
        return False


def get_price_for_new_channel(telegram_id: int):
    channel = get_editing_channel(telegram_id)
    if channel is not None:
        return channel.price_for_sub
    else:
        return None


def set_sub_for_new_channel(telegram_id: int, value: float):
    channel = get_editing_channel(telegram_id)
    if channel is not None:
        channel.how_many_sub = value
        channel.save()
        return True
    else:
        return False


def get_sub_for_new_channel(telegram_id: int):
    channel = get_editing_channel(telegram_id)
    if channel is not None:
        return channel.how_many_sub
    else:
        return None


def publish_channel_order(telegram_id: int):
    channel = get_editing_channel(telegram_id)
    if channel is not None:
        channel.editing = False
        channel.price_for_order = channel.how_many_sub * channel.price_for_sub
        channel.save()
        return True
    else:
        return False


def delete_channel_order(telegram_id: int):
    channel = get_editing_channel(telegram_id)
    if channel is not None:
        channel.delete_instance()
        return True
    else:
        return False


def get_channel_link(queue: int):
    channel = get_channel(queue)
    if channel is not None:
        return 'https://t.me/' + channel.username
    else:
        return None


def decrement_sub(queue: int):
    channel = get_channel(queue)
    if channel is not None:
        channel.how_many_sub -= 1
        channel.save()
        return True
    else:
        return False


def get_channel_count_of_sub(queue: int):
    channel = get_channel(queue)
    if channel is not None:
        return channel.how_many_sub
    else:
        return None


def statistics():
    users = User.select().count()
    channels = OrderChannel.select().count()
    posts = OrderPost.select().count()
    deduced = 0
    for u in User.select():
        deduced += u.deduced
    return '👥Всего пользователей: {u}\n' \
           '🎯Каналов на продвижении: {c}\n' \
           '🎬Постов на продвижении: {p}\n' \
           '💳Выплачено денег: {d}'.format(
               u=str(users),
               c=str(channels),
               p=str(posts),
               d=deduced)
