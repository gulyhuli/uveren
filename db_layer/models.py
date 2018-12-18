import os
from peewee import *
from playhouse.db_url import connect

if 'HEROKU' in list(os.environ.keys()):
    db = connect(os.environ.get('DATABASE_URL'))
else:
    db = SqliteDatabase('develop.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    telegram_id = IntegerField()
    name = CharField()
    # позиция просмотра поста в таблице постов
    pos_post = IntegerField(default=1)
    # позиция подписки на канал в таблице каналов
    # TODO: проверка на подписку
    pos_channel = IntegerField(default=1)
    state = IntegerField(default=0)
    made_sub = IntegerField(default=0)
    watched_posts = IntegerField(default=0)
    income_sub = DecimalField(default=0, decimal_places=2)
    income_watched = DecimalField(default=0, decimal_places=2)
    balance = DecimalField(default=0, decimal_places=2)
    deduced = DecimalField(default=0, decimal_places=2)
    earned = DecimalField(default=0, decimal_places=2)


class OrderPost(BaseModel):
    queue = IntegerField(default=1)
    from_message_id = IntegerField()
    from_chat_username = CharField()
    customer = ForeignKeyField(User)
    price_for_watch = DecimalField(default=0.02, decimal_places=2)
    how_many_watch = IntegerField(default=50)
    price_for_order = DecimalField(default=price_for_watch * how_many_watch,
                                   decimal_places=2)
    editing = BooleanField(default=True)


class OrderChannel(BaseModel):
    queue = IntegerField(default=1)
    username = CharField()
    customer = ForeignKeyField(User)
    price_for_sub = DecimalField(default=0.25, decimal_places=2)
    how_many_sub = IntegerField(default=50)
    price_for_order = DecimalField(default=price_for_sub * how_many_sub,
                                   decimal_places=2)
    editing = BooleanField(default=True)


if __name__ == '__main__':
    db.close()
    db.connect()
    db.create_tables([User, OrderPost, OrderChannel], safe=True)
