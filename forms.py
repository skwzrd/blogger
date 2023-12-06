from datetime import datetime

from flask_ckeditor import CKEditorField
from flask_sqlalchemy.model import Model
from flask_wtf import FlaskForm
from sqlalchemy import select
from werkzeug.security import check_password_hash
from wtforms.fields import (
    BooleanField,
    DateField,
    DateTimeField,
    EmailField,
    MultipleFileField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import InputRequired, Length, Optional, ValidationError

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


MAIN_VALIDATORS = [InputRequired(), Length(min=2, max=128)]
OPTIONAL = [Optional()]


class UserForm(FlaskForm):
    first_name = StringField(validators=OPTIONAL)
    last_name = StringField(validators=OPTIONAL)
    username = StringField(validators=MAIN_VALIDATORS)
    description = TextAreaField(validators=OPTIONAL)
    email = EmailField(validators=OPTIONAL)
    password = PasswordField(validators=OPTIONAL)
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=2, max=128)])
    password = PasswordField(validators=[InputRequired(), Length(min=2, max=128)])
    submit = SubmitField("Submit")

    def validate_password(self, field):
        user = db.session.scalar(select(User).where(User.username == self.username.data))

        # fail fast
        if not user or not user.username or not user.password:
            raise ValidationError("Incorrect Credentials")

        if not check_password_hash(user.password, self.password.data):
            raise ValidationError("Incorrect Credentials")


class PostForm(FlaskForm):
    published_date = DateField(validators=OPTIONAL, default=datetime.now())
    title = StringField(validators=MAIN_VALIDATORS)
    text = CKEditorField(validators=OPTIONAL)
    files = MultipleFileField(validators=OPTIONAL, description="These are files for users to download.")
    tags = TextAreaField(description="Comma separated tag list", validators=OPTIONAL)
    last_modified_date = DateField(validators=OPTIONAL, default=datetime.now())
    is_published = BooleanField(validators=OPTIONAL)
    submit = SubmitField("Submit")


class ContactForm(FlaskForm):
    name = StringField(validators=OPTIONAL, description="Optional")
    email = StringField(validators=OPTIONAL, description="Optional")
    message = TextAreaField(validators=[InputRequired(), Length(4, 1024)])
    submit = SubmitField("Submit")
