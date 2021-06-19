from jacowvalidator import app, db
from flask import render_template

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(401)
def not_authorised_401_error(error):
    return render_template('403.html'), 401


@app.errorhandler(403)
def not_authorised_error(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
