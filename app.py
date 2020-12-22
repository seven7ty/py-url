import os
from flask import Flask, redirect

app: Flask = Flask(__name__)


@app.route('/<slug>')
def redirect(slug):
    return redirect()


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT')))
