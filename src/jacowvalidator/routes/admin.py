import os
from docx import Document
from flask import render_template, request, send_file, abort
from sqlalchemy import func
from functools import wraps
from jacowvalidator import app, document_docx, db
from flask_login import current_user, login_required
from jacowvalidator.models import AppUser, Conference, Log
from jacowvalidator.forms.login import RegistrationForm, ConferenceForm
from jacowvalidator.forms.reports import SearchForm

def is_admin():
    return current_user and current_user.is_authenticated and current_user.is_admin

def is_editor():
    return current_user and current_user.is_authenticated and current_user.is_editor

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


def admin_or_editor_required(func):
    wraps(func)
    def wrapper(*args, **kwargs):
        if is_admin() or is_editor():
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


@app.route("/report/summary", methods=["GET", "POST"])
@login_required
@admin_or_editor_required
def summary():
    logs = Log.query
    form = SearchForm()
    if form.validate_on_submit():
        form, logs = get_logs_from_search(form)
    logs = logs.order_by(Log.timestamp.desc()).all()

    return render_template("summary.html", logs=logs, form=form)


@app.route("/report/count", methods=["GET", "POST"])
@login_required
@admin_or_editor_required
def count():
    # countLogs is an array of tuples
    logs = Log.query
    form = SearchForm()
    if form.validate_on_submit():
        form, logs = get_logs_from_search(form)

    logs = logs.with_entities(Log.filename, func.count(Log.filename)).group_by(Log.filename).all()

    return render_template("count.html", logs=logs, form=form)



@app.route("/report/log", methods=["GET", "POST"])
@login_required
@admin_or_editor_required
def log():
    logs = Log.query
    form = SearchForm()
    if form.validate_on_submit():
        form, logs = get_logs_from_search(form)

    return render_template("logs.html", logs=logs, form=form)


def get_logs_from_search(form):
    logs = Log.query
    if form.conference_id.data:
        logs = logs.filter_by(conference_id=form.conference_id.data.id)
    if form.app_user_id.data:
        logs = logs.filter_by(app_user_id=form.app_user_id.data.id)
    if form.filename.data:
        logs = logs.filter_by(filename=form.filename.data)

    if form.start_date.data:
        logs = logs.filter(Log.timestamp > form.start_date.data)
    else:
        # otherwise the value is the string 'None'
        form.start_date.data = ''
    if form.end_date.data:
        logs = logs.filter(Log.timestamp < form.end_date.data)
    else:
        # otherwise the value is the string 'None'
        form.end_date.data = ''
    return (form, logs)