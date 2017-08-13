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
    """Class to save Journal Entries"""
    user = ForeignKeyField(User, related_name='journal_entry')
    title = CharField()
    date = DateField()
    time_spent = IntegerField()
    what_i_learned = TextField()
    resources_to_remember = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-date',)


def initialize():
    """Set up the database tables, if necessary"""
    DATABASE.connect()
    DATABASE.create_tables([User, JournalEntry], safe=True)
    DATABASE.close()
