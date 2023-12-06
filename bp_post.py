import os
from datetime import datetime

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_ckeditor import upload_fail, upload_success
from sqlalchemy import delete, select, update
from werkzeug.utils import secure_filename

from bp_auth import AuthActions, auth, login_required
from configs import CONSTS
from forms import PostForm, get_fields
from models import File, Post, Tag, db

bp_post = Blueprint("bp_post", __name__, template_folder="templates")


def get_tags_from_form(form):
    # tags must be unique -- perform one extra query to meet this criteria
    form_tags = [x.strip() for x in form.tags.data.split(',') if x and x.strip() != '']
    existing_tags = db.session.scalars(select(Tag).where(Tag.text.in_(form_tags))).all()
    existing_tags_text = [t.text for t in existing_tags]
    new_tags = [Tag(text=t) for t in form_tags if t not in existing_tags_text]
    return new_tags + existing_tags


def get_filename_datetime():
    return datetime.now().strftime("%Y_%m_%d__%H_%M_%S__%f")


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

        file_name_path = f"{get_filename_datetime()}__{file_name}"
        rel_path = os.path.join(current_app.config["UPLOADS_REL_PATH"], file_name_path)
        full_path = os.path.join(current_app.config["UPLOADS_FULL_PATH"], file_name_path)
        file_data = file.read()
        with open(full_path, "wb") as f:
            f.write(file_data)

        files.append(File(file_name=file_name, file_path=rel_path, file_type=file_type))
    return files


@bp_post.route("/upload", methods=["POST"])
@login_required
def upload():
    f = request.files.get("upload")

    extension = f.filename.split(".")[-1].lower()
    if extension not in ["jpg", "gif", "png", "jpeg"]:
        return upload_fail(message="Image only!")

    f.save(os.path.join(current_app.config["UPLOADS_FULL_PATH"], f.filename))
    url = url_for("uploaded_files", filename=f.filename)

    return upload_success(url, filename=f.filename)


@bp_post.route("/post_create", methods=["GET", "POST"])
@login_required
def post_create():
    form = PostForm()

    if form.validate_on_submit():
        d = get_fields(Post, PostForm, form)

        post = Post(**d)

        post.tags = get_tags_from_form(form)

        post.files = upload_files_from_form(form)

        post.user_id = auth(AuthActions.get_user_id)

        db.session.add(post)
        flash("Post created.", "success")
        db.session.commit()

        form.data.clear()
        return redirect(url_for("bp_post.post_list"))

    return render_template(
        "post_create.html", CONSTS=CONSTS, form=form, logged_in=auth(AuthActions.is_logged_in), is_admin=auth(AuthActions.is_admin)
    )


@bp_post.route("/post_edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def post_edit(post_id):
    form = PostForm()

    post = db.session.scalar(select(Post).where(Post.id == post_id))
    if not post:
        return redirect(url_for("bp_post.post_list"))

    form = PostForm(obj=post)

    if form.validate_on_submit():
        d = get_fields(Post, PostForm, form)

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

    form.tags.data = ", ".join([x.text for x in post.tags])
    return render_template(
        "post_edit.html",
        CONSTS=CONSTS,
        form=form,
        post=post,
        logged_in=auth(AuthActions.is_logged_in),
        is_admin=auth(AuthActions.is_admin),
    )


@bp_post.route("/post/<int:post_id>")
def post_read(post_id):
    if auth(AuthActions.is_logged_in):
        post = db.session.scalar(select(Post).where(Post.id == post_id))
    else:
        post = db.session.scalar(
            select(Post)
            .where(Post.id == post_id)
            .where(Post.is_published == True)
        )

    if post:
        return render_template(
            "post.html", CONSTS=CONSTS, post=post, logged_in=auth(AuthActions.is_logged_in), is_admin=auth(AuthActions.is_admin)
        )

    return redirect(url_for("bp_post.post_list"))


@bp_post.route("/post_delete/<int:post_id>", methods=["DELETE"])
@login_required
def post_delete(post_id):
    post = db.session.scalar(select(Post).where(Post.id == post_id))
    if post:
        db.session.execute(delete(Post).where(Post.id == post_id))
        db.session.commit()

        post = db.session.scalar(select(Post).where(Post.id == post_id))
        if not post:
            flash(f"Post deleted.", "success")
            return redirect(url_for("bp_post.post_list"))

    flash(f"Couldn't find post #{post.id} to delete.")
    return redirect(url_for("bp_post.post_list"))


@bp_post.route("/posts")
def post_list():
    if auth(AuthActions.is_logged_in):
        posts = db.session.scalars(select(Post)).all()
    else:
        posts = db.session.scalars(select(Post).where(Post.is_published == True)).all()

    header = "Showing all posts."
    return render_template(
        "post_list.html",
        CONSTS=CONSTS,
        posts=posts,
        header=header,
        logged_in=auth(AuthActions.is_logged_in),
        is_admin=auth(AuthActions.is_admin),
    )
