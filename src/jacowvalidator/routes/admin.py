import os
from docx import Document
from flask import render_template, request, send_file, abort
from sqlalchemy import func
from functools import wraps
from jacowvalidator import app, document_docx, db
from flask_login import current_user, login_required
from jacowvalidator.models import AppUser, Conference, Log
from jacowvalidator.forms.login import RegistrationForm, ConferenceForm

def is_admin():
    return current_user and current_user.is_authenticated and current_user.is_admin


def admin_required(func):
    wraps(func)
    def wrapper(*args, **kwargs):
        if is_admin():
            return func(*args, **kwargs)
        else:
            # raise Exception('Not Authorised', 403)
            abort(403)
    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/conference', methods=['GET', 'POST'])
@login_required
@admin_required
def conference():
    form = ConferenceForm()
    if form.validate_on_submit():
        conference = Conference()
        form.populate_obj(conference)
        if conference.id == '':
            conference.id = None
        db.session.add(conference)
        db.session.commit()

        # TODO work out how to reset form
        form = ConferenceForm()


    conferences = Conference.query.all()
    return render_template('conference.html', title='Conference', form=form, conferences=conferences)


@app.route('/conference/update/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def conference_update(id):
    conference = Conference.query.filter_by(id=id).first_or_404()
    form = ConferenceForm(obj=conference)
    if form.validate_on_submit():
        form.populate_obj(conference)
        db.session.commit()

    conferences = Conference.query.all()
    return render_template('conference.html', title='Conference', form=form, conferences=conferences, mode='update')


@app.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = AppUser(username=form.username.data,
          is_admin=form.is_admin.data or form.is_admin.data=='on',
          is_editor=form.is_editor.data or form.is_editor.data=='on',
          is_active=form.is_active.data or form.is_active.data=='on')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

    users = AppUser.query.all()
    return render_template('users.html', title='Users', form=form, users=users)


@app.route('/users/update/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_update(id):
    user = AppUser.query.filter_by(id=id).first_or_404()
    form = RegistrationForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()

    users = AppUser.query.all()
    return render_template('users.html', title='Users', form=form, users=users, mode='update')


@app.route("/convert", methods=["GET", "POST"])
@login_required
@admin_required
def convert():
    documents = document_docx
    if request.method == "POST" and documents.name in request.files:
        filename = documents.save(request.files[documents.name])
        full_path = documents.path(filename)
        try:
            doc = Document(full_path)
            new_doc_path = documents.path('test_'+filename)
            replace_identifying_text(doc, new_doc_path)
            # send_file should handle the open read and close
            return send_file(
                new_doc_path,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                attachment_filename=filename
            )

        finally:
            os.remove(full_path)
            # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: '/var/tmp\\document\\test_THPMK148_2.docx'
            # only happens on windows I think.
            # os.remove(new_doc_path)

    return render_template("convert.html", action='convert')


@app.route("/summary", methods=["GET"])
@login_required
@admin_required
def summary():
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    # countLogs is an array of tuples
    countLogs = Log.query.with_entities(Log.filename, func.count(Log.filename)).group_by(Log.filename).all()

    return render_template("summary.html", logs=logs, countLogs=countLogs)


@app.route("/log", methods=["GET"])
@login_required
@admin_required
def log():
    logs = []
    if 'SQLALCHEMY_DATABASE_URI' in app.config:
        logs = Log.query.all()
    return render_template("logs.html", logs=logs)