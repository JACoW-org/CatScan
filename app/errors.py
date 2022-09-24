from flask import render_template
from flask import Blueprint

errors = Blueprint('errors', __name__)

@errors.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@errors.errorhandler(401)
def not_authorised_401_error(error):
    return render_template('403.html'), 401


@errors.errorhandler(403)
def not_authorised_error(error):
    return render_template('403.html'), 403


@errors.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
