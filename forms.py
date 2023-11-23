from datetime import datetime

from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash
from wtforms.fields import (BooleanField, DateField, DateTimeField, EmailField,
                            MultipleFileField, PasswordField, StringField,
                            SubmitField, TextAreaField)
from wtforms.validators import InputRequired, Length, Optional, ValidationError

from db import get_user_by_username


def get_fields(model, form):
    """Return a dict with all the model keys and form values."""
    d = {}
    for k in model.__mapper__.columns.keys():
        if k in form.data:
            d[k] = form[k].data
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
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=2, max=128)])
    password = PasswordField(validators=[InputRequired(), Length(min=2, max=128)])
    submit = SubmitField('Submit')

    def validate_password(self, field):
        user = get_user_by_username(self.username.data)
        
        # fail fast
        if not user or not user.username or not user.password:
            raise ValidationError('Incorrect Credentials')
        
        if not check_password_hash(user.password, self.password.data):
            raise ValidationError('Incorrect Credentials')


class PostForm(FlaskForm):
    published_date = DateField(validators=OPTIONAL, default=datetime.now())
    title = StringField(validators=MAIN_VALIDATORS)
    text = CKEditorField(validators=OPTIONAL)
    files = MultipleFileField(validators=OPTIONAL, description='These are files for users to download.')
    tags = TextAreaField(description='Comma separated tag list', validators=OPTIONAL)
    last_modified_date = DateField(validators=OPTIONAL, default=datetime.now())
    is_published = BooleanField(validators=OPTIONAL)
    submit = SubmitField('Submit')

