from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from jacowvalidator.models import AppUser, Conference


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    id = HiddenField('ID')
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Is Admin')
    is_editor = BooleanField('Is Editor')
    is_active = BooleanField('Is Active')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = AppUser.query.filter(username == username.data, id != self.id).first()
        if user is not None:
            raise ValidationError('Username must be unique, Please use a different username.')


class ConferenceForm(FlaskForm):
    id = HiddenField('ID')
    name = StringField('Full Name', validators=[DataRequired()])
    short_name = StringField('Short Name', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired()])
    path = StringField('Path', validators=[DataRequired()])
    is_active = BooleanField('Is Active')
    submit = SubmitField('Add')

    def validate_short_name(self, short_name):
        conference = Conference.query.filter(short_name == short_name.data, id != self.id).first()
        if conference is not None:
            raise ValidationError('Short Name must be unique, Please use a different name')
