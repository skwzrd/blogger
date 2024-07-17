import os
import subprocess
from time import time

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for
)
from sqlalchemy import delete, select, update
from werkzeug.utils import secure_filename

from bp_auth import AuthActions, admin_required, auth
from captcha import MathCaptcha
from configs import CONSTS
from forms import CommentForm, PostForm, get_fields
from limiter import limiter
from models import Comment, File, Post, Tag, db

bp_post = Blueprint("bp_post", __name__, template_folder="templates")


def convert_html_to_markdown(html_text):
    result = subprocess.run(
        ["/usr/bin/pandoc", "--from=html+raw_html", "--to=markdown"],
        input=html_text.encode("utf-8"),
        stdout=subprocess.PIPE,
    )
    result.check_returncode()
    return result.stdout.decode("utf-8")


def convert_markdown_to_html(markdown_text):
    result = subprocess.run(
        ["/usr/bin/pandoc", "--from=markdown", "--to=html+raw_html"],
        input=markdown_text.encode("utf-8"),
        stdout=subprocess.PIPE,
    )
    result.check_returncode()
    return result.stdout.decode("utf-8")


def get_tags_from_form(form):
    # tags must be unique -- perform one extra query to meet this criteria
    form_tags = {t.strip() for t in form.tags.data.split(",") if t and t.strip() != ""}
    existing_tags = db.session.scalars(select(Tag).where(Tag.text.in_(form_tags))).all()
    existing_tags_text = [t.text for t in existing_tags]
    new_tags = [Tag(text=t) for t in form_tags if t not in existing_tags_text]
    return new_tags + existing_tags


def delete_upload(file_name):
    path = os.path.join(current_app.config["UPLOADS_FULL_PATH"], file_name)
    if os.path.isfile(path):
        os.remove(path)
        return


def get_filename_datetime():
    return time().__str__().split(".")[0]


def upload_files_from_form(form):
    files = []
    for file in form.files.data:
        file_name = secure_filename(file.filename)
        if not file_name:
            continue

        file_type = None
        for header in file.headers:
            if header[0] == "Content-Type":
                file_type = header[1].split("/")[-1]
                break

        server_file_name = f"{get_filename_datetime()}__{file_name}"
        relative_path = current_app.config["UPLOADS_REL_PATH"]
        full_path = os.path.join(current_app.config["UPLOADS_FULL_PATH"], server_file_name)
        file_data = file.read()
        with open(full_path, "wb") as f:
            f.write(file_data)

        files.append(File(file_name=file_name, relative_path=relative_path, server_file_name=server_file_name, file_type=file_type))
    return files


@bp_post.route("/post_create", methods=["GET", "POST"])
@admin_required
def post_create():
    form = PostForm()

    if form.validate_on_submit():
        d = get_fields(Post, PostForm, form)

        post = Post(**d)

        post.text_html = convert_markdown_to_html(post.text_markdown)
        post.tags = get_tags_from_form(form)
        post.files = upload_files_from_form(form)

        post.user_id = auth(AuthActions.get_user_id)

        db.session.add(post)
        flash("Post created.", "success")
        db.session.commit()

        form.data.clear()
        return redirect(url_for("bp_post.post_list"))

    return render_template("post_create.html", CONSTS=CONSTS, form=form, is_admin=auth(AuthActions.is_admin))


@bp_post.route("/post_edit/<int:post_id>", methods=["GET", "POST"])
@admin_required
def post_edit(post_id):
    form = PostForm()

    post = db.session.scalar(select(Post).where(Post.id == post_id))
    if not post:
        return redirect(url_for("bp_post.post_list"))

    form = PostForm(obj=post)

    if form.validate_on_submit():
        d = get_fields(Post, PostForm, form)

        post.text_html = convert_markdown_to_html(form.text_markdown.data)
        post.tags = get_tags_from_form(form)

        existing_files = []
        if post.files:
            existing_files = post.files
        post.files = upload_files_from_form(form) + existing_files

        db.session.execute(update(Post).where(Post.id == post.id).values(**d))

        flash("Post updated.", "success")
        db.session.commit()

        form.data.clear()
        return redirect(url_for("bp_post.post_list"))

    form.tags.data = ", ".join([t.text for t in post.tags])
    return render_template(
        "post_edit.html",
        CONSTS=CONSTS,
        form=form,
        post=post,
        is_admin=auth(AuthActions.is_admin),
    )


@bp_post.route("/admin_post_read/<int:post_id>")
@admin_required
def admin_post_read(post_id):
    post = db.session.scalar(select(Post).where(Post.id == post_id))

    if post:
        return render_template("post.html", CONSTS=CONSTS, post=post, is_admin=auth(AuthActions.is_admin))

    return redirect(url_for("bp_post.post_list"))


@bp_post.route("/post/<int:post_id>", methods=["GET", "POST"])
@limiter.limit("20/day", methods=["POST"])
def post_read(post_id):
    form = CommentForm()
    captcha = MathCaptcha(tff_file_path=current_app.config["MATH_CAPTCHA_FONT"])

    post = db.session.scalar(select(Post).where(Post.id == post_id).where(Post.is_published == True))

    if post:
        if form.validate_on_submit():
            if captcha.is_valid(form.captcha_id.data, form.captcha_answer.data):
                d = get_fields(Comment, CommentForm, form)
                comment = Comment(post_id=post_id, **d)
                db.session.add(comment)
                db.session.commit()
                form.data.clear()
                flash("Comment added.", "success")
                return redirect(url_for("bp_post.post_read", post_id=post_id))

            flash("Wrong math captcha answer", "danger")

        form.captcha_id.data, form.captcha_b64_img_str = captcha.generate_captcha()
        return render_template("post.html", CONSTS=CONSTS, post=post, form=form, is_admin=auth(AuthActions.is_admin))

    return redirect(url_for("bp_post.post_list"))


@bp_post.route("/post_delete/<int:post_id>", methods=["DELETE"])
@admin_required
def post_delete(post_id):
    post = db.session.scalar(select(Post).where(Post.id == post_id))
    if post:
        for file in post.files:
            delete_upload(file.server_file_name)

        db.session.delete(post)
        db.session.commit()

        post = db.session.scalar(select(Post).where(Post.id == post_id))
        if not post:
            flash("Post deleted.", "success")
            return redirect(url_for("bp_post.post_list"))

    flash(f"Couldn't find post #{post.id} to delete.")
    return redirect(url_for("bp_post.post_list"))


@bp_post.route("/post_delete_file/<int:post_id>/<int:file_id>", methods=["DELETE"])
@admin_required
def post_delete_file(post_id, file_id):
    file = db.session.scalar(select(File).where(File.post_id == post_id).where(File.id == file_id))
    if file:
        delete_upload(file.server_file_name)

        db.session.execute(delete(File).where(File.post_id == post_id).where(File.id == file_id))
        db.session.commit()

        file = db.session.scalar(select(File).where(File.id == file_id))
        if not file:
            flash("File deleted.", "success")
            return redirect(url_for("bp_post.post_edit", post_id=post_id))

    flash(f"Couldn't find post #{post_id} and file #{file_id} to delete.")
    return redirect(url_for("bp_post.post_edit", post_id=post_id))


@bp_post.route("/posts")
def post_list():
    if auth(AuthActions.is_admin):
        posts = db.session.scalars(select(Post).order_by(Post.published_date.desc())).all()
    else:
        posts = db.session.scalars(select(Post).where(Post.is_published == True).order_by(Post.published_date.desc())).all()

    header = "Showing all posts."
    return render_template(
        "post_list.html",
        CONSTS=CONSTS,
        posts=posts,
        header=header,
        is_admin=auth(AuthActions.is_admin),
    )
