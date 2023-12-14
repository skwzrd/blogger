from flask import Blueprint, render_template
from sqlalchemy import select

from bp_auth import AuthActions, admin_required, auth
from configs import CONSTS
from models import Comment, Contact, Log, db

bp_admin = Blueprint("bp_admin", __name__, template_folder="templates")


@bp_admin.route("/admin_contacts", methods=["GET"])
@admin_required
def admin_contacts():
    items = db.session.scalars(select(Contact).order_by(Contact.id.desc()).limit(30)).all()
    attributes = ["id", "name", "email", "message"]
    header = "Showing all site messages."
    return render_template(
        "admin_item.html",
        CONSTS=CONSTS,
        items=items,
        attributes=attributes,
        header=header,
        is_admin=auth(AuthActions.is_admin),
    )


@bp_admin.route("/admin_comments", methods=["GET"])
@admin_required
def admin_comments():
    items = db.session.scalars(select(Comment).order_by(Comment.id.desc()).limit(30)).all()
    attributes = ["id", "title", "text", "post_id"]
    header = "Showing all site comments."
    return render_template(
        "admin_item.html",
        CONSTS=CONSTS,
        items=items,
        attributes=attributes,
        header=header,
        is_admin=auth(AuthActions.is_admin),
    )


@bp_admin.route("/admin_logs", methods=["GET"])
@admin_required
def admin_logs():
    items = db.session.scalars(select(Log).where(Log.path.not_like("/static%")).order_by(Log.id.desc()).limit(30)).all()
    attributes = ["id", "start_datetime_utc", "duration", "method", "x_forwarded_for", "referrer", "path", "user_agent"]
    header = "Showing all site logs."
    return render_template(
        "admin_item.html",
        CONSTS=CONSTS,
        items=items,
        attributes=attributes,
        header=header,
        is_admin=auth(AuthActions.is_admin),
    )
