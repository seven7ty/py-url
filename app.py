import os
import re
import psycopg2
import psycopg2.extras
import flask
from collections import namedtuple
from dotenv import load_dotenv

load_dotenv()

app: flask.Flask = flask.Flask(__name__)

database = psycopg2.connect(dbname=os.getenv("DB_NAME"),
                            user=os.getenv("DB_USER"),
                            host=os.getenv("DB_HOST"),
                            port=os.getenv("DB_PORT"),
                            password=os.getenv("DB_PASSWORD"))

Response = namedtuple('Response', ['json', 'code'])
server_error_response = Response(
    {"success": False, "message": "Internal Server Error - something went wrong while computing this request"}, 500)
not_found_response = Response(
    {"success": False, "message": "Not Found - this slug does not exist"}, 404)
invalid_url_response = Response(
    {"success": False, "message": "Bad Request - the 'link' field is not a valid URL"}, 400)
invalid_slug_response = Response(
    {"success": False, "message": "Bad Request - The slug can only contain letters, digits and hyphens."}, 400)


def is_valid_slug(string: str) -> bool:
    valid = re.compile(r'[a-z\d-]', re.IGNORECASE)
    return bool(re.match(valid, string))


def is_valid_url(url: str) -> bool:
    regex = re.compile(r'[a-zA-z\d]*')
    if bool(re.match(regex, url)) and url.startswith(('https://', 'http://')) and '.' in url:
        return True
    return False


def create(body: dict, slug: str) -> Response:
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        if 'link' not in body or type(link := body['link']) is not str:
            return Response({"success": False,
                             "message": "Bad Request - please specify a string link redirect in the request body"}, 400)
        elif len(link) > 100:
            return Response({"success": False,
                             "message": "Bad Request - link cannot be longer than 100 characters"}, 400)
        elif type(link) is not str:
            return Response({
                "success": False,
                "message": "Bad Request - link must be of type 'string'."
            }, 400)
        elif not is_valid_url(link):
            return invalid_url_response
        elif not is_valid_slug(slug):
            return invalid_slug_response
        cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
        res = cur.fetchone()
        if res:
            return Response({"success": False, "message": "Bad Request - this slug already exists"}, 400)
        cur.execute('INSERT INTO links (link, slug) VALUES (%s, %s)', (str(link), str(slug)))
        database.commit()
        return Response({"success": True, "message": "Success - short link created"}, 201)


def get(slug: str) -> Response:
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
        res = cur.fetchone()
        if res:
            return Response({"success": True, "payload": {"link": res.link}}, 200)
        return not_found_response


def delete(slug: str) -> Response:
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
        res = cur.fetchone()
        if res:
            cur.execute('DELETE FROM links WHERE slug = %s', (slug,))
            database.commit()
            return Response({"success": True, "message": "Success - short link deleted successfully"}, 204)
        return not_found_response


def put(slug: str) -> Response:
    with database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cur:
        if 'link' not in flask.request.json or type(link := flask.request.json['link']) is not str:
            return Response(
                {"success": False,
                 "message": "Bad Request - body has to include a 'link' field of type 'string'."}, 400)
        if len(link) > 100:
            return Response({"success": False,
                             "message": "Bad Request - link cannot be longer than 100 characters"}, 400)
        if not is_valid_url(link):
            return invalid_url_response
        cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
        res = cur.fetchone()
        if res:
            cur.execute('UPDATE links SET link = %s WHERE slug = %s', (str(link), slug))
            database.commit()
            return Response({"success": True, "message": "Success - link updated successfully."}, 204)
        return not_found_response


@app.route('/api/<slug>', methods=['GET', 'POST', 'DELETE', 'PUT'])
def api_interaction(slug):
    response = server_error_response
    if flask.request.method == 'GET':
        response = get(slug)
    elif flask.request.method == 'POST':
        response = create(flask.request.json, slug)
    elif flask.request.method == 'DELETE':
        response = delete(slug)
    elif flask.request.method == 'PUT':
        response = put(slug)
    return flask.jsonify(response.json), response.code


@app.route('/<slug>', methods=['GET'])
def redirect(slug):
    response: Response = get(slug)
    if response[1] == 200:
        return flask.redirect(response.json['payload']['link'])
    return flask.render_template('bad-link.html')


@app.route('/', methods=['GET'])
def home():
    return flask.render_template('home.html')


if __name__ == '__main__':
    port = int(os.getenv('PORT'))
    print(f'Server started on port {port}')
    app.run(port=port)
