from flask_sqlalchemy.model import Model
from flask_wtf import FlaskForm
from sqlalchemy import select
from werkzeug.security import check_password_hash
from wtforms.fields import (
    BooleanField,
    DateField,
    EmailField,
    HiddenField,
    IntegerField,
    MultipleFileField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import InputRequired, Length, Optional, ValidationError

from configs import get_current_datetime
from models import User, db


def get_fields(model: Model, form: FlaskForm, submitted_form: FlaskForm):
    """
    Return a Dict that only contains keys found in our WTForm declarations.
    We do this so users can't sneak in form fields like roles, created dates, etc.
    For extra precaution, we also make sure the form field is in our model.
    """
    d = {}
    form_keys = set(form.__dict__.keys())
    model_keys = set(model.__mapper__.columns.keys())
    submitted_form_keys = set(submitted_form._fields.keys())

    fields = form_keys.intersection(model_keys)

    for field in fields:
        if field not in model_keys and not field.startswith("_"):
            raise ValueError(field)

        if field in submitted_form_keys:
            d[field] = submitted_form[field].data
        else:
            raise ValueError(field)

    return d


OPTIONAL = [Optional()]


class UserForm(FlaskForm):
    first_name = StringField(validators=OPTIONAL)
    last_name = StringField(validators=OPTIONAL)
    username = StringField(validators=[InputRequired(), Length(min=2, max=128)])
    description = TextAreaField(validators=OPTIONAL)
    email = EmailField(validators=OPTIONAL)
    password = PasswordField(validators=OPTIONAL)
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=2, max=128)])
    password = PasswordField(validators=[InputRequired(), Length(min=2, max=128)])

    captcha_id = HiddenField(validators=[InputRequired()])
    captcha_answer = IntegerField("", validators=[InputRequired()])

    submit = SubmitField("Submit")

    def validate_password(self, field):
        user = db.session.scalar(select(User).where(User.username == self.username.data))

        # fail fast
        if not user or not user.username or not user.password:
            raise ValidationError("Incorrect Credentials")

        if not check_password_hash(user.password, self.password.data):
            raise ValidationError("Incorrect Credentials")


class PostForm(FlaskForm):
    title = StringField(validators=[InputRequired(), Length(min=1, max=512)])
    text_markdown = TextAreaField(validators=OPTIONAL, render_kw={"style": "height: 500px;"})
    files = MultipleFileField(validators=OPTIONAL, description="These are files for users to download.")
    tags = TextAreaField(description="Comma separated tag list", validators=OPTIONAL)
    published_date = DateField(validators=OPTIONAL, default=get_current_datetime())
    last_modified_date = DateField(validators=OPTIONAL, default=get_current_datetime())
    is_published = BooleanField(validators=OPTIONAL)
    submit = SubmitField("Submit")


class AdminCommentForm(FlaskForm):
    title = StringField(validators=OPTIONAL, description="Optional")
    text = TextAreaField(validators=[InputRequired(), Length(min=2, max=512)])
    submit = SubmitField("Submit")


class CommentForm(AdminCommentForm):
    title = StringField(validators=OPTIONAL, description="Optional")
    text = TextAreaField(validators=[InputRequired(), Length(min=2, max=512)])
    captcha_id = HiddenField(validators=[InputRequired()])
    captcha_answer = IntegerField("", validators=[InputRequired()])
    submit = SubmitField("Submit")


class ContactForm(FlaskForm):
    name = StringField(validators=OPTIONAL, description="Optional")
    email = StringField(validators=OPTIONAL, description="Optional")
    message = TextAreaField(validators=[InputRequired(), Length(8, 2048)])

    captcha_id = HiddenField(validators=[InputRequired()])
    captcha_answer = IntegerField("", validators=[InputRequired()])

    submit = SubmitField("Submit")
