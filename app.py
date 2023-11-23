import os
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import NamedTuple

from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor, upload_fail, upload_success
from sqlalchemy import delete, insert, select, update
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import (db, get_post_by_id, get_posts_by_tag_id,
                get_published_post_by_id, get_published_posts_by_tag_id,
                get_user_by_id, get_user_by_username)
from forms import LoginForm, PostForm, UserForm, get_fields
from models import File, Post, Tag, User, db
from utils import make_path

app = Flask(__name__)


app.config['SECRET_KEY'] = 'hbr4ui2222222ddddddd3[[[[rgrtyg5655675333vsdfhsnjrtjnrthntsnjst3333333]'

app.config['DATABASE_FILE'] = 'blogger.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + make_path(app.config['DATABASE_FILE'])
app.config['SQLALCHEMY_ECHO'] = False

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=2)

app.config['CKEDITOR_FILE_UPLOADER'] = 'upload'
app.config['CKEDITOR_CODE_THEME'] = 'arta'

# with this enabled, we can not delete posts using our current fetch method
# from flask_wtf.csrf import CSRFProtect
# app.config['CKEDITOR_ENABLE_CSRF'] = True
# csrf = CSRFProtect()
# csrf.init_app(app)

app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

app.config['UPLOADS_REL_PATH'] = os.path.join('static', 'uploads') # must be somewhere in the app's root directory
app.config['UPLOADS_FULL_PATH'] = make_path(app.config['UPLOADS_REL_PATH'])

db.init_app(app)

bootstrap = Bootstrap5(app)
ckeditor = CKEditor(app)


class CONSTS(NamedTuple):
    site_name = 'Blogger'
    site_url = 'http://127.0.0.1:8080'
    site_logo_url = '/static/images/logo.png'
    about = """Hi, this is a simple blog made using Flask, WTForms, Bootstrap."""
    contact = """If you'd like to reach out, you can..."""


class AuthActions(Enum):
    is_logged_in = 1
    log_in = 2
    log_out = 3
    get_user_id = 4


def auth(action: AuthActions, user_id=None):
    with app.app_context():
        if action == AuthActions.is_logged_in:
            return 'user_id' in session
        
        if action == AuthActions.log_in and user_id:
            session['user_id'] = user_id
            return
        
        if action == AuthActions.log_out:
            session.clear()
            return
        
        if action == AuthActions.get_user_id:
            return session['user_id']
    
    raise ValueError(action, user_id)


def get_filename_datetime():
    return datetime.now().strftime('%Y_%m_%d__%H_%M_%S__%f')


def upload_files_from_form(form):
    files = []
    for file in form.files.data:

        file_name = secure_filename(file.filename)
        if not file_name:
            continue

        file_type = None
        for header in file.headers:
            if header[0] == 'Content-Type':
                file_type = header[1].split('/')[-1]
                break

        file_name_path = f'{get_filename_datetime()}__{file_name}'
        rel_path = os.path.join(app.config['UPLOADS_REL_PATH'], file_name_path)
        full_path = os.path.join(app.config['UPLOADS_FULL_PATH'], file_name_path)
        file_data = file.read()
        with open(full_path, 'wb') as f:
            f.write(file_data)

        files.append(File(file_name=file_name, file_path=rel_path, file_type=file_type))
    return files


def login_required(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if not auth(AuthActions.is_logged_in):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password_candidate = form.password.data

        user = get_user_by_username(username)
        if user:
            if check_password_hash(user.password, password_candidate):

                auth(AuthActions.log_in, user_id=user.id)

                flash("Login successful.", "success")
                return redirect(url_for('post_list'))
        flash("Incorrect username or password.", "danger")
    return render_template("login.html", form=form, CONSTS=CONSTS, logged_in=auth(AuthActions.is_logged_in))


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    auth(AuthActions.log_out)
    flash("Logout successful.", 'success')
    return redirect(url_for("post_list"))


@app.route('/static/uploads/<path:filename>')
def uploaded_files(filename):
    return send_from_directory(app.config['UPLOADS_FULL_PATH'], filename)


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    f = request.files.get('upload')

    extension = f.filename.split('.')[-1].lower()
    if extension not in ['jpg', 'gif', 'png', 'jpeg']:
        return upload_fail(message='Image only!')
    
    f.save(os.path.join(app.config['UPLOADS_FULL_PATH'], f.filename))
    url = url_for('uploaded_files', filename=f.filename)

    return upload_success(url, filename=f.filename)


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    users = db.session.scalars(select(User))
    return render_template("user_list.html", CONSTS=CONSTS, users=users, logged_in=auth(AuthActions.is_logged_in))


@app.route('/user_create', methods=['GET', 'POST'])
@login_required
def user_create():
    form = UserForm()

    if form.validate_on_submit():
        if form.password.data.strip() != '':
            form.password.data = generate_password_hash(form.password.data)

        d = get_fields(User, form)
        db.session.execute(insert(User).values(**d))
        db.session.commit()

        flash('User created.', 'success')
        form.data.clear()

    return render_template("user.html", CONSTS=CONSTS, form=form, logged_in=auth(AuthActions.is_logged_in))


@app.route('/user_edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    user = get_user_by_id(user_id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        if form.password.data != '':
            form.password.data = generate_password_hash(form.password.data)
            d = get_fields(User, form)
        else:
            d = get_fields(User, form)
            d.pop('password') # password not changed

        db.session.execute(update(User).where(User.id == user.id).values(**d))
        db.session.commit()

        flash('User updated.', 'success')
        form.data.clear()

    return render_template("user.html", CONSTS=CONSTS, form=form, user=user, logged_in=auth(AuthActions.is_logged_in))


def get_tags_from_form(form):
    # tags must be unique -- perform one extra query to meet this criteria

    form_tags = [x.strip() for x in form.tags.data.split(',')]
    existing_tags = db.session.scalars(select(Tag).where(Tag.text.in_(form_tags))).all()
    existing_tags_text = [t.text for t in existing_tags]
    new_tags = [Tag(text=t) for t in form_tags if t not in existing_tags_text]
    return [t for t in new_tags + existing_tags if t.text] # remove empty tags


@app.route('/post_create', methods=['GET', 'POST'])
@login_required
def post_create():
    form = PostForm()

    if form.validate_on_submit():
        d = get_fields(Post, form)

        post = Post(**d)

        post.tags = get_tags_from_form(form)

        post.files = upload_files_from_form(form)

        db.session.add(post)
        flash('Post created.', 'success')
        db.session.commit()

        form.data.clear()
        return redirect(url_for('post_list'))

    return render_template("post_edit_create.html", CONSTS=CONSTS, form=form, logged_in=auth(AuthActions.is_logged_in))


@app.route('/post_edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_edit(post_id):
    form = PostForm()
    
    post = get_post_by_id(post_id)

    if not post:
        return redirect(url_for('post_list'))

    form = PostForm(obj=post)

    if form.validate_on_submit():
        d = get_fields(Post, form)

        post.tags = get_tags_from_form(form)

        existing_files = []
        if post.files:
            existing_files = post.files
        post.files = upload_files_from_form(form) + existing_files

        db.session.execute(update(Post).where(Post.id == post.id).values(**d))

        flash('Post updated.', 'success')
        db.session.commit()

        form.data.clear()
        return redirect(url_for('post_list'))

    form.tags.data = ', '.join([x.text for x in post.tags])
    return render_template("post_edit_create.html", CONSTS=CONSTS, form=form, post=post, logged_in=auth(AuthActions.is_logged_in))


@app.route('/post/<int:post_id>')
def post_read(post_id):
    if auth(AuthActions.is_logged_in):
        post = get_post_by_id(post_id)
    else:
        post = get_published_post_by_id(post_id)

    if post:
        return render_template('post.html', CONSTS=CONSTS, post=post, logged_in=auth(AuthActions.is_logged_in))

    return redirect(url_for('post_list'))


@app.route('/post_delete/<int:post_id>', methods=['DELETE'])
@login_required
def post_delete(post_id):
    
    post = get_post_by_id(post_id)

    if post:
        db.session.execute(delete(Post).where(Post.id == post_id))
        db.session.commit()

        post = get_post_by_id(post_id)
        if not post:
            flash(f'Post deleted.', 'success')
            return redirect(url_for('post_list'))
        
    flash(f'Couldn\'t find post #{post.id} to delete.')
    return redirect(url_for('post_list'))


@app.route('/')
def post_list():
    if auth(AuthActions.is_logged_in):
        posts = db.session.scalars(select(Post))
    else:
        posts = db.session.scalars(select(Post).where(Post.is_published == True))

    header = 'Showing all posts.'
    return render_template("post_list.html", CONSTS=CONSTS, posts=posts, header=header, logged_in=auth(AuthActions.is_logged_in))


@app.route('/tags/<int:tag_id>')
def tag_list(tag_id):
    """Display all posts with Tag.id equal to `tag_id`."""
    if auth(AuthActions.is_logged_in):
        posts = get_posts_by_tag_id(tag_id)
    else:
        posts = get_published_posts_by_tag_id(tag_id)

    tag_text = db.session.scalar(select(Tag.text).where(Tag.id == tag_id))
    header = None
    if tag_text:
        header = f'Showing all posts with tag "{tag_text}".'

    return render_template("post_list.html", CONSTS=CONSTS, posts=posts, header=header, logged_in=auth(AuthActions.is_logged_in))


@app.route('/about')
def about():
    return render_template('about.html', CONSTS=CONSTS, logged_in=auth(AuthActions.is_logged_in))


def build_db():
    db.create_all()
    
    user = User(username="user", first_name='Mr.', last_name='Wolf', password=generate_password_hash("user"))
    db.session.add(user)

    t1, t2, t3 = Tag(text='tag 1'), Tag(text='tag 2'), Tag(text='tag 3')

    posts = [
        Post(title='Post 1 title', text='Post 1 text', is_published=True, tags=[t1, t3]),
        Post(title='Post 2 title', text='Post 2 text', is_published=False, tags=[t1, t2]),
        Post(title='Post 3 title', text='Post 3 text', is_published=True, tags=[t1]),
    ]
    db.session.add_all(posts)
    
    db.session.commit()

 
if __name__ == '__main__':
    database_path = make_path(app.config['DATABASE_FILE'])

    if not os.path.exists(database_path):
        with app.app_context():
            build_db()

    app.run(host='127.0.0.1', port=8080, debug=True) # testing

