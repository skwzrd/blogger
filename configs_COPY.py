import os
from datetime import datetime, timedelta
from typing import NamedTuple

import pytz

from utils import make_path


class CONSTS(NamedTuple):
    TESTING = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=4)
    DATABASE_FILE = "DATA.db"
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + make_path(DATABASE_FILE)
    SQLALCHEMY_ECHO = False
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024 * 1024  # gb
    UPLOADS_REL_PATH = os.path.join("static", "uploads")  # must be somewhere in the app's root directory
    UPLOADS_FULL_PATH = make_path(UPLOADS_REL_PATH)

    supported_file_uploads = ["jpg", "gif", "png", "jpeg", "mp4", "webm", "mp3"]

    MATH_CAPTCHA_FONT = os.path.join(os.path.dirname(__file__), "fonts/tly.ttf")

    if not os.path.exists(UPLOADS_FULL_PATH):
        os.mkdir(UPLOADS_FULL_PATH, mode=770)

    datetime_format = "%A, %B %d, %Y"
    datetime_timezone = "America/Toronto"

    with open(make_path("secret.txt"), encoding="utf-8") as f:
        SECRET_KEY = f.read().strip()

    redis_url = "redis://localhost:6379"

    site_name = "site_name"

    site_host = "127.0.0.1"
    site_port = 8080

    site_url = "https://site_name.com"
    if TESTING:
        site_url = f"http://{site_host}:{site_port}"

    site_logo_url = "/static/images/logo_COPY.png"

    site_version = "v2.0"

    admin_username = "admin"
    admin_password = "password12345"
    admin_email = "admin@my_site.com"

    intro = f"""<div class="d-flex justify-content-between">  <div>Welcome to {site_name}!</div>  <div>{site_version}</div> </div>"""
    body = """Body."""
    conclusion = """Conclusion"""
    email_html = f"""<a href="mailto:{admin_email}">{admin_email}</a>"""
    contact = f"""Feel free to reach out to us at {email_html}, or by filling out the contact form below."""

    # These get displayed in the nav. Items should be like {name: endpoint_path}
    navlinks = {
        'Music': 'music',
    }

    rss_feed = True
    rss_title = site_name
    rss_description = site_name
    rss_link = site_url
    rss_author = site_name


def get_current_datetime(timezone_str=CONSTS.datetime_timezone):
    utc_now = datetime.now()
    timezone = pytz.timezone(timezone_str)
    now_tz = utc_now.replace(tzinfo=pytz.utc).astimezone(timezone)
    return now_tz
