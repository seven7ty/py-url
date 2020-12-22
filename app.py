import os
import psycopg2
import psycopg2.extras
import flask
import string
import random
from collections import namedtuple
from dotenv import load_dotenv

load_dotenv()

app: flask.Flask = flask.Flask(__name__)
Response = namedtuple('Response', ['json', 'code'])
database = psycopg2.connect(dbname=os.getenv("DB_NAME"),
                            user=os.getenv("DB_USER"),
                            host=os.getenv("DB_HOST"),
                            port=os.getenv("DB_PORT"),
                            password=os.getenv("DB_PASSWORD"))


def generate_slug(length: int = 5) -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))


def create(body: dict) -> Response:
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        if 'link' not in body:
            return Response({"success": False,
                    "message": "Bad Request - please specify a link redirect in the request body"}, 400)
        if len(body['link']) > 100:
            return Response({"success": False,
                    "message": "Bad Request - link cannot be longer than 100 characters."}, 400)
        slug = body['slug'] if 'slug' in body and len(body['slug']) < 50 else generate_slug(10)
        cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
        res = cur.fetchone()
        if res:
            return Response({"success": False, "message": "Bad Request - this slug already exists"}, 400)
        cur.execute('INSERT INTO links VALUES (%%s %%s)', (body['link'], slug))
        return Response({"success": True, "payload": {"link": body['link'], "slug": slug}}, 201)

def get(slug: str) -> tuple()


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
            response = create(flask.request.data)
            return flask.jsonify(response.json), response.code


@app.route('/', methods=['GET'])
def home():
    return flask.jsonify({})


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT')))
