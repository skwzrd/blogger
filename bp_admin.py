from flask import Blueprint, render_template
from sqlalchemy import select

from bp_auth import AuthActions, admin_required, auth
from configs import CONSTS
from models import Contact, db, Log

bp_admin = Blueprint("bp_admin", __name__, template_folder="templates")


@bp_admin.route("/admin_contacts", methods=["GET"])
@admin_required
def admin_contacts():
    items = db.session.scalars(select(Contact).order_by(Contact.id.desc()).limit(30)).all()
    attributes = ["id", "name", "email", "message"]
    header = f"Showing all site messages."
    return render_template(
        "admin_item.html",
        CONSTS=CONSTS,
        items=items,
        attributes=attributes,
        header=header,
        logged_in=auth(AuthActions.is_logged_in),
        is_admin=auth(AuthActions.is_admin),
    )

@bp_admin.route("/admin_logs", methods=["GET"])
@admin_required
def admin_logs():
    items = db.session.scalars(select(Log).order_by(Log.id.desc()).limit(30)).all()
    attributes = ["id", "start_datetime_utc", "duration", "method", "x_forwarded_for", "referrer", "user_agent"]
    header = f"Showing all site logs."
    return render_template(
        "admin_item.html",
        CONSTS=CONSTS,
        items=items,
        attributes=attributes,
        header=header,
        logged_in=auth(AuthActions.is_logged_in),
        is_admin=auth(AuthActions.is_admin),
    )
