import os

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for
)
from flask_bootstrap import Bootstrap5
from sqlalchemy import select
from werkzeug.middleware.proxy_fix import ProxyFix

from bp_admin import bp_admin
from bp_auth import AuthActions, auth, bp_auth
from bp_post import bp_post
from bp_tag import bp_tag
from bp_user import bp_user
from captcha import MathCaptcha
from configs import CONSTS, get_current_datetime
from flask_ckeditor_edit import CKEditor
from forms import ContactForm, get_fields
from init_database import build_db
from limiter import limiter
from models import Contact, Log, Post, db
from utils import make_path


def create_app():
    app = Flask(__name__)

    app.config.from_object(CONSTS)

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_user)
    app.register_blueprint(bp_post)
    app.register_blueprint(bp_tag)

    Bootstrap5(app)
    CKEditor(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    db.init_app(app)

    limiter.init_app(app)

    return app


app = create_app()


@app.route("/static/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory(app.config["UPLOADS_FULL_PATH"], filename)


@app.errorhandler(404)
def not_found(e: Exception):
    return (
        render_template("error_404.html", CONSTS=CONSTS, is_admin=auth(AuthActions.is_admin)),
        404,
    )


@app.errorhandler(500)
def internal_server_error(e):
    return (
        render_template("error_500.html", CONSTS=CONSTS, is_admin=auth(AuthActions.is_admin)),
        500,
    )


@app.before_request
def before():
    g.start_datetime_utc = get_current_datetime('Etc/UTC')

    if app.config["TESTING"]:
        database_path = make_path(app.config["DATABASE_FILE"])
        if not os.path.exists(database_path):
            with app.app_context():
                build_db()


@app.after_request
def after(response):
    g.end_datetime_utc = get_current_datetime('Etc/UTC')

    log = Log(
        x_forwarded_for=request.headers.get("X-Forwarded-For", None),
        remote_addr=request.headers.get("Remote-Addr", None),
        referrer=request.referrer,
        content_md5=request.content_md5,
        origin=request.origin,
        scheme=request.scheme,
        method=request.method,
        path=request.path,
        query_string=request.query_string.decode(),
        duration=(g.end_datetime_utc - g.start_datetime_utc).total_seconds(),
        start_datetime_utc=g.start_datetime_utc,
        end_datetime_utc=g.end_datetime_utc,
        user_agent=request.user_agent.__str__(),
        accept=request.headers.get("Accept", None),
        accept_language=request.headers.get("Accept-Language", None),
        accept_encoding=request.headers.get("Accept-Encoding", None),
        content_length=request.content_length,
    )
    db.session.add(log)
    db.session.commit()

    return response


@app.route("/", methods=["GET", "POST"])
@limiter.limit("3/day", methods=["POST"])
def index():
    form = ContactForm()
    captcha = MathCaptcha(tff_file_path=app.config["MATH_CAPTCHA_FONT"])

    posts = db.session.scalars(select(Post).where(Post.is_published == True).order_by(Post.last_modified_date.desc()).limit(10)).all()
    if form.validate_on_submit():
        if captcha.is_valid(form.captcha_id.data, form.captcha_answer.data):
            d = get_fields(Contact, ContactForm, form)
            db.session.add(Contact(**d))
            db.session.commit()
            form.data.clear()
            flash("Message received, thank you!", "success")
            return redirect(url_for("index"))
        flash("Wrong math captcha answer", "danger")

    form.captcha_id.data, form.captcha_b64_img_str = captcha.generate_captcha()
    return render_template("index.html", CONSTS=CONSTS, posts=posts, form=form, is_admin=auth(AuthActions.is_admin))


if __name__ == "__main__" and app.config["TESTING"]:
    app.run(host=CONSTS.site_host, port=CONSTS.site_port, debug=app.config["TESTING"])
