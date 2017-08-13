from flask import Flask, render_template, g, flash, url_for, redirect, abort
from flask_bcrypt import check_password_hash
from flask_login import current_user, LoginManager, login_user, logout_user, login_required


import forms
import models

# set up the flask app
DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

app = Flask(__name__)
app.secret_key = 'luGKI^T*&G5idfK*UFlg6f6i7^f'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    try:
        return models.User.get(models.User.id == user_id)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    g.db.get_conn()
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


@app.route('/')
def index():
    entries = models.JournalEntry.select().where(g.user == models.JournalEntry.user)
    return render_template('index.html', entries=entries)


@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("Yay, you registered!", "success")
        models.User.create_user(
            email=form.email.data,
            password=form.password.data
        )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out! Come back soon!", "success")
    return redirect(url_for('index'))


@app.route('/details/<int:entry_id>')
@login_required
def details(entry_id):
    try:
        entry = models.JournalEntry.get(models.JournalEntry.id==entry_id)
    except models.DoesNotExist:
        abort(404)
    else:
        return render_template('detail.html', entry=entry)


@app.route('/entry', methods=('GET', 'POST'))
@app.route('/entry/<int:entry_id>', methods=('GET', 'POST'))
def entry(entry_id=None):
    """Page to create a new entry or edit an existing entry"""
    form = forms.JournalEntryForm()
    if entry_id:  # edit an existing entry
        template = 'edit.html'
    else:  # create a new entry
        template = 'new.html'
        if form.validate_on_submit():
            try:
                models.JournalEntry.create(
                    user=g.user._get_current_object(),
                    title=form.title.data,
                    date=form.date.data,
                    time_spent=form.time_spent.data,
                    what_i_learned=form.what_i_learned.data,
                    resources_to_remember=form.resources_to_remember.data
                )
            except:
                flash("Journal Entry Failed to save...", 'error')
            else:
                flash("Journal Entry Saved", 'success')
                return redirect(url_for('index'))
    return render_template(template, form=form)


@app.route('/entries')
@login_required
def list():
    """Display the Journal Entries' Title and Date"""
    entries = models.JournalEntry.select().where(g.user == models.JournalEntry.user)
    return render_template('entries.html', entries=entries)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)
