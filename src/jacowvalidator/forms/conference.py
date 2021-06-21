from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, HiddenField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from jacowvalidator.models import Conference


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
