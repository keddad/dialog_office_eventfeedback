import peewee
from datetime import datetime

database = peewee.SqliteDatabase("db.db")


class Event(peewee.Model):
    name = peewee.CharField(default="Event")
    details = peewee.CharField()
    owner = peewee.IntegerField()

    class Meta:
        database = database


class User(peewee.Model):
    uid = peewee.IntegerField()
    state = peewee.CharField(default="START")

    class Meta:
        database = database


class Review(peewee.Model):
    writer_name = peewee.CharField()
    writer_uid = peewee.IntegerField()
    event_id = peewee.IntegerField()
    rating = peewee.IntegerField()
    text = peewee.CharField()
    write_time = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = database


database.create_tables([Event, User, Review])
