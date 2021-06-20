from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from jacowvalidator.models import AppUser, Conference


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    id = HiddenField('ID')
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = StringField('Email')
    password = PasswordField('Password')
    password2 = PasswordField('Repeat Password')
    is_admin = BooleanField('Is Admin')
    is_editor = BooleanField('Is Editor')
    is_active = BooleanField('Is Active')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = None
        if self.id.data:
            # if there is an id, must be an update
            user = AppUser.query.filter(AppUser.username == username.data, AppUser.id != self.id.data).first()
        else:
            user = AppUser.query.filter_by(username=username.data).first()

        if user is not None:
            raise ValidationError('Username must be unique, Please use a different username.')

    def validate_password(self, password):
        # only need to check if add new user
        if not self.id.data and password == '':
            raise ValidationError('Password is required')

    def validate_password2(self, password2):
        if not self.id.data and password2.data != self.password.data:
            raise ValidationError(f'Passwords must match')

class ConferenceForm(FlaskForm):
    id = HiddenField('ID')
    name = StringField('Full Name', validators=[DataRequired()])
    short_name = StringField('Short Name', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired()])
    path = StringField('Path', validators=[DataRequired()])
    display_order = IntegerField('Display Order')
    is_active = BooleanField('Is Active')
    submit = SubmitField('Add')

    def validate_short_name(self, short_name):
        conference = None
        if self.id.data:
            conference = Conference.query.filter(Conference.short_name == short_name.data, Conference.id != self.id.data).first()
        else:
            conference = Conference.query.filter_by(short_name=short_name.data).first()

        if conference is not None:
            raise ValidationError('Short Name must be unique, Please use a different name')



