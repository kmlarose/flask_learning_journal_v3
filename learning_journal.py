from flask import Flask, render_template

import models

# set up the flask app
DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

app = Flask(__name__)
app.secret_key = '6:YSE)+*gEeY5@-H/e*7v6$JZe\pbE-['


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)
