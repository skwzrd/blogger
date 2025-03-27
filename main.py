import os
from datetime import timezone

from feedgen.feed import FeedGenerator
from flask import (
    Flask,
    flash,
    g,
    make_response,
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

    try:
        # for custom endpoints
        from bp_custom import bp_custom
        app.register_blueprint(bp_custom)
    except:
        pass

    Bootstrap5(app)

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
    if CONSTS.store_requests:
        g.start_datetime_utc = get_current_datetime("Etc/UTC")

        if app.config["TESTING"]:
            database_path = make_path(app.config["DATABASE_FILE"])
            if not os.path.exists(database_path):
                with app.app_context():
                    build_db()


@app.after_request
def after(response):
    if CONSTS.store_requests:
        g.end_datetime_utc = get_current_datetime("Etc/UTC")

        if request.path.startswith("/static/"):
            return response

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
            accept_language=request.headers.get("Accept-Language", None),
            content_length=request.content_length,
        )
        db.session.add(log)
        db.session.commit()

    return response
    

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.gif')


@app.route("/", methods=["GET", "POST"])
@limiter.limit("3/day", methods=["POST"])
def index():
    form: ContactForm = ContactForm()
    captcha = MathCaptcha(tff_file_path=app.config["MATH_CAPTCHA_FONT"])

    contacts = db.session.scalars(select(Contact).order_by(Contact.created_datetime.desc())).all()
    posts = db.session.scalars(select(Post).where(Post.is_published == True).order_by(Post.published_date.desc()).limit(20)).all()
    if form.validate_on_submit():
        if captcha.is_valid(form.captcha_id.data, form.captcha_answer.data):

            if comment_is_spam(form.message.data) or CONSTS.site_name in form.email.data:
                form.data.clear()
                flash("I loath green eggs and spam.", "danger")
                return redirect(url_for("index"))

            d = get_fields(Contact, ContactForm, form)
            db.session.add(Contact(**d))
            db.session.commit()
            form.data.clear()
            flash("Message received, thank you!", "success")
            return redirect(url_for("index"))
        flash("Wrong math captcha answer", "danger")

    form.captcha_id.data, form.captcha_b64_img_str = captcha.generate_captcha()
    return render_template("index.html", CONSTS=CONSTS, posts=posts, form=form, contacts=contacts, is_admin=auth(AuthActions.is_admin))


@app.route("/rss")
def rss():
    fg = FeedGenerator()
    fg.title(CONSTS.rss_title)
    fg.description(CONSTS.rss_description)
    fg.link(href=CONSTS.rss_link)

    posts = db.session.scalars(select(Post).where(Post.is_published == True).order_by(Post.published_date.desc())).all()
    for post in posts:
        post_url = url_for("bp_post.post_read_path", post_path=post.path, _external=True)
        fe = fg.add_entry()
        fe.title(post.title)
        fe.link(href=post_url)
        fe.description(post.title)
        fe.guid(post_url, permalink=True)
        fe.author(name=CONSTS.site_name, email=CONSTS.admin_email)
        fe.pubDate(post.published_date.replace(tzinfo=timezone.utc))
        fe.updated(post.last_modified_date.replace(tzinfo=timezone.utc))

    response = make_response(fg.rss_str())
    response.headers.set("Content-Type", "text/xml")

    return response


def comment_is_spam(comment):
    """Checks against blacklisted IP addresses, and vets comment against spam keywords."""
    blocked_IP_range = ["91.219.212.", "156.146.51."]
    for blocked_IP in blocked_IP_range:
        if request.remote_addr.startswith(blocked_IP):
            return True

    spam_point_threshold = 5
    spam = {
        "get it now": 2,
        "% off": 4,
        "free": 1,
        "shipping": 2,
        "get yours": 1,
        "best": 1,
        "on sale": 2,
        "gives you": 1,
        "take care of": 1,
        "https://": 15,
        "http://": 15,
        "www.": 15,
        "buy": 1,
        "discount": 2,
        " price": 3,
        "get yours here": 4,
        "get yours": 2,
        ",\n": 1,
        "special": 1,
        "act now": 2,
        "worlds greatest": 3,
        "worlds best": 3,
        "magic sand": 10,
        " seo ": 3,
        "any help": 1,
        "best regards": 3,
        "outlook.": 15,
        f"@{CONSTS.site_name}.": 15,
        "hotmail.": 15,
        "protonmail.": 15,
        "yahoo.": 15,
        "gmail.": 15,
        "need help with": 15,
    }

    points = 0
    comment = comment.lower().replace("'", "")
    for phrase in spam:
        if phrase in comment:
            points += spam[phrase]
    return points >= spam_point_threshold


if __name__ == "__main__" and app.config["TESTING"]:
    app.run(host=CONSTS.site_host, port=CONSTS.site_port, debug=app.config["TESTING"])
