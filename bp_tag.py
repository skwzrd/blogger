from flask import Blueprint, render_template
from sqlalchemy import select

from bp_auth import AuthActions, auth
from configs import CONSTS
from models import BridgeTag, Post, Tag, db

bp_tag = Blueprint("bp_tag", __name__, template_folder="templates")


@bp_tag.route("/tags/<int:tag_id>")
def tag_list(tag_id):
    """Display all posts with Tag.id equal to `tag_id`."""

    tag_text = db.session.scalar(select(Tag.text).where(Tag.id == tag_id))
    print(tag_text)

    if auth(AuthActions.is_logged_in):
        posts = db.session.scalars(
            select(Post).join(BridgeTag, Post.id == BridgeTag.post_id).join(Tag, Tag.id == BridgeTag.tag_id).where(Tag.id == tag_id)
        )
    else:
        posts = db.session.scalars(
            select(Post)
            .join(BridgeTag, Post.id == BridgeTag.post_id)
            .join(Tag, Tag.id == BridgeTag.tag_id)
            .where(Tag.id == tag_id)
            .where(Post.is_published == True)
        )

    header = None
    if tag_text:
        header = f'Showing all posts with tag "{tag_text}".'

    return render_template(
        "post_list.html",
        CONSTS=CONSTS,
        posts=posts,
        header=header,
        logged_in=auth(AuthActions.is_logged_in),
        is_admin=auth(AuthActions.is_admin),
    )
