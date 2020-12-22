import os
import psycopg2
import psycopg2.extras
import flask
from dotenv import load_dotenv

load_dotenv()

app: flask.Flask = flask.Flask(__name__)
database = psycopg2.connect(dbname=os.getenv("DB_NAME"),
                            user=os.getenv("DB_USER"),
                            host=os.getenv("DB_HOST"),
                            port=os.getenv("DB_PORT"),
                            password=os.getenv("DB_PASSWORD"))


@app.route('/<slug>', methods=['GET'])
def redirect(slug):
    cur = database.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    cur.execute('SELECT link FROM links WHERE slug = %s', (slug,))
    res = cur.fetchone()
    if hasattr(res, 'link'):
        return flask.jsonify({"success": True, "payload": {"link": res.link}})
    return flask.jsonify({"success": False, "message": "Not Found - this slug does not exist"})


@app.route('/', methods=['GET'])
def home():
    return flask.jsonify({})


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT')))
