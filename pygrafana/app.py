import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify, _app_ctx_stack, Response
from contextlib import closing
import json
from slugify import slugify as awesome_slugify

import traceback

sqlite3.register_converter("BOOLEAN", lambda v: v != '0')

# configuration
DATABASE = '/tmp/database.sqlite'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'


app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

class APIException(Exception):
    status_code = 411

class PreconditionException(APIException):
    status_code = 412

class ErrorException(APIException):
    status_code = 400


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def exception_handler(e):
    response = jsonify({'code': e.status_code, 'message': str(e)})
    response.status_code = e.status_code
    return response

@app.errorhandler(404)
def bad_404(e):
    response = jsonify({'code': 404, 'message': str(e)})
    response.status_code = 404
    return response

@app.errorhandler(PreconditionException)
def precondition_failed(e):
    return exception_handler(e)

@app.errorhandler(ErrorException)
def request_failed(e):
    return exception_handler(e)


def slugify(text):
    return awesome_slugify(text, to_lower=True)


def get_dashboard(slug):
    cur = g.db.execute('select slug, dashboard, isStarred, created, updated, expires, id from dashboards where slug = ?', [slug])

    row = cur.fetchone()

    if row is None:
        return None

    ret = dict()

    canStar = False
    isHome = False

    if slug is 'home':
        isHome = True

    ret['meta'] = dict(slug=row[0], created=row[3], updated=row[4], expires=row[5], canStar=canStar, canSave=True, canEdit=True, isHome=isHome)

    if canStar:
        ret['meta']['isStarred'] = bool(row[2])

    ret['dashboard'] = json.loads(row[1])
    ret['dashboard']['id'] = row[6]
    ret['version'] = 1

    return ret

@app.route('/api/dashboards/db', methods=['POST'])
def view_update_dashboard():
    data = request.get_json(force=True)

    try:
        dashboard = data['dashboard']
        version = dashboard['version']
        id = dashboard['id']
        title = dashboard['title']
    except KeyError as e:
        raise ErrorException("Missing key in dashboard")

    slug = slugify(title)


    if id is None:
        # check if there is already a dashboard with the same slug
        cursor = g.db.execute('select id from dashboards where slug = ?', [slug])
        if cursor.fetchone() is not None:
            raise PreconditionException("Dashboard with title '%s' already exists" % title)

        version = 1
        dashboard['version'] = 1

        cursor = g.db.execute('insert into dashboards (slug, dashboard) values (?, ?)',
                    [slug, json.dumps(dashboard)])
        if cursor.rowcount is not 1:
            success = False
        else:
            success = True
    else:
        cursor = g.db.execute('select dashboard from dashboards where slug = ?', [slug])
        row = cursor.fetchone()

        if row is None:
            raise PreconditionException("No matching dashboard found to update")

        current_dashboard = json.loads(row[0])

        current_version = current_dashboard['version']

        if current_version > version:
            raise PreconditionException("Current version is newer than the updated one")

        version = current_version + 1
        dashboard['version'] = version

        cursor = g.db.execute('update dashboards set dashboard=?, slug=? where id=?', [json.dumps(dashboard), slug, id])
        if cursor.rowcount is 0:
            success = False
        else:
            success = True

    ret = dict()
    ret['slug'] = slug
    ret['status'] = success
    ret['version'] = version

    g.db.commit()

    return jsonify(**ret)


@app.route('/api/dashboards/db', methods=['GET'])
def view_list_dashboards():
    cur = g.db.execute('select slug from dashboards')

    dashboards = [dict(slug=row[0]) for row in cur.fetchall()]


    ret = dict()
    ret['dashboards'] = dashboards

    flash("list_dashboards")

    return jsonify(**ret)

@app.route('/api/dashboards/home', methods=['GET'])
def view_get_home_dashboard():
    ret = get_dashboard('home')

    if ret is None:
        raise RuntimeError("Home dashboard not found")

    flash("get home dashboard")

    return jsonify(**ret)


@app.route('/api/dashboards/db/<slug>', methods=['GET'])
def view_get_dashboard(slug):

    ret = get_dashboard(slug)

    return jsonify(**ret);


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/api/search', methods=['GET'])
def view_search_dashboard():
    title = request.args.get('query')
    starred = request.args.get('starred')
    tag = request.args.get('tag')
    tagcloud = request.args.get('tagcloud')

    if tagcloud is not None:
        raise ErrorException("tagcloud feature not implemented")

    if tag is not None:
        raise ErrorException("tag feature not implemented")

    q = []
    if title is not None and len(title) is not 0:
        slug = slugify(title)
        q.append("slug LIKE '%s'" % slug)

    if starred is not None:
        isStarred = True if starred in ['true', 'True', 'TRUE'] else False
        q.append("isStarred = '%s'" % str(isStarred).lower())

    where = ""
    if len(q) > 0:
        where = "where %s " % (' AND ').join(q)

    print('select id, dashboard, isStarred from dashboards %s ' % where)

    result = query_db("select id, slug, dashboard, isStarred from dashboards %s " % where)

    ret = []

    for entry in result:

        dashboard = json.loads(entry[2])

        uri = "db/%s" % entry[1]
        type = "dash-db"

        d = dict(id=entry[0], title=dashboard['title'], uri=uri, type=type, tags=[], isStarred=bool(entry[3]))

        ret.append(d)

    print(ret)

    return Response(json.dumps(ret),  mimetype='application/json')
