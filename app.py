import os
import psycopg2
import psycopg2.extras
import flask
import string
import random
import typing as t
from dotenv import load_dotenv

load_dotenv()

app: flask.Flask = flask.Flask(__name__)
database = psycopg2.connect(dbname=os.getenv("DB_NAME"),
                            user=os.getenv("DB_USER"),
                            host=os.getenv("DB_HOST"),
                            port=os.getenv("DB_PORT"),
                            password=os.getenv("DB_PASSWORD"))


def generate_slug(length: int = 5) -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))


def create(body: dict) -> dict:
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        if 'link' not in body:
            return {"success": False,
                    "message": "Bad Request - please specify a link redirect in the request body"}
        if len(body['link']) > 100:
            return {"success": False,
                    "message": "Bad Request - link cannot be longer than 100 characters."}
        slug = body['slug'] if 'slug' in body and len(body['slug']) < 50 else generate_slug()
        cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
        res = cur.fetchone()
        if res:
            return {"success": False, "message": "Bad Request - this slug already exists"}


@app.route('/<slug>', methods=['GET', 'POST', 'DELETE'])
def redirect(slug):
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        if flask.request.method == 'GET':
            cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
            res = cur.fetchone()
            if hasattr(res, 'link'):
                return flask.jsonify({"success": True, "payload": {"link": res.link}}), 200
            return flask.jsonify({"success": False, "message": "Not Found - this slug does not exist"}), 404
        elif flask.request.method == 'POST':
            body = flask.request.data
            if 'link' not in body:
                return flask.jsonify({"success": False,
                                      "message": "Bad Request - please specify a link redirect in the request body"}), 400

            cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
            res = cur.fetchone()
            if res:
                return flask.jsonify({"success": False, "message": "Not Found - this slug already exists"})
            cur.execute('INSERT INTO links VALUES (%%s %%s)', ())


@app.route('/', methods=['GET'])
def home():
    return flask.jsonify({})


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT')))
