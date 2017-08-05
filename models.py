import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *

DATABASE = SqliteDatabase('journal.db')


class User(UserMixin, Model):
    """Class to save user login credentials"""
    email = CharField(unique=True)
    password = CharField()

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, email, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    email=email,
                    password=generate_password_hash(password)
                )
        except IntegrityError:
            raise ValueError("User already exists")


class JournalEntry(Model):
    """Class to save Journal Entry content"""
    user = ForeignKeyField(User, related_name='journal_entries')
    timestamp = DateTimeField(default=datetime.datetime.now)
    title = CharField()
    time_spent = IntegerField()
    learned = TextField()
    resources = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)


def initialize():
    """Set up the database tables, if necessary"""
    DATABASE.connect()
    DATABASE.create_tables([User, JournalEntry], safe=True)
    DATABASE.close()
