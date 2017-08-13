import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError, Optional, Email, Length, EqualTo

from models import User


def email_exists(form, field):
    """Return an error message if the email has been used before"""
    if User.select().where(User.email == field.data).exists():
        raise ValidationError('User with that email already exists.')


class JournalEntryForm(FlaskForm):
    """Form to create/edit a Journal Entry"""
    title = StringField(
        'Title',
        validators=[DataRequired()]
    )
    date = DateField(
        'Date',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )
    time_spent = StringField(
        'Time Spent',
        validators=[DataRequired()]
    )
    what_i_learned = TextAreaField(
        'What I Learned',
        validators=[DataRequired()]
    )
    resources_to_remember = TextAreaField(
        'Resources To Remember',
        validators=[Optional()]
    )


class RegisterForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            email_exists
        ])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8),
            EqualTo('password2', message='Passwords must match')
        ])
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
    )


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
