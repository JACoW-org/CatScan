from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField, SelectField
from wtforms.validators import Optional
from jacowvalidator.models import AppUser, Conference
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class SearchForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=(Optional(),))
    end_date = DateField('End Date', format='%Y-%m-%d', validators=(Optional(),))
    # conference = SelectField('Conference', choices=[(row.id, row.short_name) for row in Conference.query.filter_by(is_active=True).order_by(Conference.display_order.asc()).all()])
    # app_user = SelectField('User', choices=[(row.id, row.username) for row in AppUser.query.all()])
    conference_id = QuerySelectField(
        query_factory=lambda: Conference.query.filter_by(is_active=True).order_by(Conference.display_order.asc()),
        allow_blank=True
    )
    app_user_id = QuerySelectField(
        query_factory=lambda: AppUser.query,
        allow_blank=True
    )
    submit = SubmitField('Search')


