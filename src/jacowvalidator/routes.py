import os
import json
from datetime import datetime
from subprocess import run
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from TexSoup import TexSoup
from flask import redirect, render_template, request, url_for, send_file, abort, flash
from flask_uploads import UploadNotAllowed
from sqlalchemy import func
from jacowvalidator import app, document_docx, document_tex, db
from .utils import json_serialise
from jacowvalidator.docutils.page import (check_tracking_on, TrackingOnError)
from jacowvalidator.docutils.doc import create_upload_variables, create_spms_variables, create_upload_variables_latex, \
    AbstractNotFoundError
from .test_utils import replace_identifying_text
from .spms import get_conference_path, PaperNotFoundError
from flask_login import current_user, login_user, logout_user, login_required
from jacowvalidator.models import AppUser, Conference, Log
from jacowvalidator.forms.login import LoginForm, RegistrationForm, ConferenceForm

try:
    p = run(['git', 'log', '-1', '--format=%h,%at'], capture_output=True, text=True, check=True)
    commit_sha, commit_date = p.stdout.split(',')
    commit_date = datetime.fromtimestamp(int(commit_date))
except Exception:
    commit_sha, commit_date = None, None


@app.context_processor
def inject_commit_details():
    return dict(commit_sha=commit_sha, commit_date=commit_date)


@app.context_processor
def inject_debug():
    debug = app.env == 'development' or app.debug
    return dict(debug=debug)


@app.template_filter('tick_cross2')
def tick_cross2(s):
    return "✓" if s else "✗"


@app.template_filter('tick_cross')
def tick_cross(s):
    if s == 1 or s is True:
        return '<span class="background-dark-tick">✓</span>'
    elif s == 2:
        return '<span class="background-dark-question"><i class="fas fa-question"></i></span>'
    else:
        return '<span class="background-dark-cross">✗</span>'


@app.template_filter('pastel_background_style')
def pastel_background_style(s):
    if s == 1 or s is True:
        return 'background-jacow-tick'
    elif s == 2:
        return 'background-jacow-question'
    else:
        return "background-jacow-cross"


@app.template_filter('display_report')
def display_report(s):
    report = json.loads(s)
    return report


@app.template_filter('dict_to_list')
def dict_to_list(s):
    return [value for index, value in s.items()]


@app.template_filter('first_value_in_dict')
def first_value_in_dict(s):
    return [value for index, value in s.items()][0]


@app.route("/")
def hello():
    return redirect(url_for('upload'))


@app.route("/upload", methods=["GET", "POST"])
def upload():
    documents = document_docx
    args = {'extension': '*.docx', 'description': 'Word', 'action': 'upload'}
    return upload_common(documents, args)


@app.route("/upload_latex", methods=["GET", "POST"])
def upload_latex():
    documents = document_tex
    args = {'extension': '*.tex', 'description': 'Latex', 'action': 'upload_latex'}
    return upload_common(documents, args)


@app.route("/resources", methods=["GET"])
def resources():
    admin = 'DEV_DEBUG' in os.environ and os.environ['DEV_DEBUG'] == 'True'
    return render_template("resources.html", admin=admin)


def get_summary_latex(part, title):
    if part and part.string:
        return {'text': part.string, 'title': title, 'ok': True, 'extra_info': f'{title}: {part.string}'}
    elif part and part.contents:
        # TODO join if multiple contents
        for i, p in enumerate(part.contents):
            return {'text': p, 'title': title, 'ok': True, 'extra_info': f'{title}: {p}'}
    else:
        return {'text': '', 'title': title, 'ok': False, 'extra_info': f'No {title} found'}
    return {}


def upload_common(documents, args):
    admin = 'DEV_DEBUG' in os.environ and os.environ['DEV_DEBUG'] == 'True'
    conferences = [conference.short_name for conference in Conference.query.filter_by(is_active=True).order_by(Conference.display_order.asc()).all()]
    if request.method == "POST" and documents.name in request.files:
        try:
            filename = documents.save(request.files[documents.name])
            paper_name = os.path.splitext(filename)[0]
        except UploadNotAllowed:
            return render_template(
                "upload.html",
                error=f"Wrong file extension. Please upload {args['extension']} files only",
                admin=admin,
                args=args)
        full_path = documents.path(filename)
        # set a default
        conference_id = False  # next(iter(conferences))
        conference_path = ''
        if 'conference_id' in request.form and request.form["conference_id"] in conferences:
            conference_id = request.form["conference_id"]
            conference_path = get_conference_path(conference_id)
        try:
            if args['description'] == 'Word':
                doc = Document(full_path)
                parse_type = 'docx'
                metadata = doc.core_properties

                # check whether tracking on
                result = check_tracking_on(doc)

                # get variables to pass to template
                summary, authors, title = create_upload_variables(doc)

                if conference_id:
                    spms_summary, reference_csv_details = \
                        create_spms_variables(paper_name, authors, title, conference_path, conference_id)
                    if spms_summary:
                        summary.update(spms_summary)
            elif args['description'] == 'Latex':
                doc = TexSoup(open(full_path, encoding="utf8"))
                summary, authors, title = create_upload_variables_latex(doc)
                metadata = []
                if conference_id:
                    spms_summary, reference_csv_details = \
                        create_spms_variables(paper_name, authors, title, conference_path, conference_id)
                    if spms_summary:
                        summary.update(spms_summary)

            save_log(filename, conference_id, 'OK', locals())

            return render_template("upload.html", processed=True, **locals())
        except (PackageNotFoundError, ValueError):
            save_log(filename, conference_id, 'PackageNotFoundError', locals())
            return render_template(
                "upload.html",
                filename=filename,
                conferences=conferences,
                error=f"Failed to open document {filename}. Is it a valid {args['description']} document?",
                admin=admin,
                args=args)
        except TrackingOnError as err:
            save_log(filename, conference_id, 'TrackingOnError', locals())
            return render_template(
                "upload.html",
                filename=filename,
                conferences=conferences,
                error=err,
                admin=admin,
                args=args)
        except OSError:
            save_log(filename, conference_id, 'OSError', locals())
            return render_template(
                "upload.html",
                filename=filename,
                conferences=conferences,
                error=f"It seems the file {filename} is corrupted",
                admin=admin,
                args=args)
        except PaperNotFoundError:
            save_log(filename, conference_id, 'PaperNotFoundError', locals())
            return render_template(
                "upload.html",
                processed=True,
                **locals(),
                error=f"It seems the file {filename} has no corresponding entry in the SPMS ({conference_id}) references list. "
                      f"Is your filename the same as your Paper name?")
        except AbstractNotFoundError as err:
            save_log(filename, conference_id, 'AbstractNotFoundError', locals())
            return render_template(
                "upload.html",
                filename=filename,
                conferences=conferences,
                error=err,
                admin=admin,
                args=args)
        except Exception:
            # TODO work out why there is an OK log followed by an Exception one.
            save_log(filename, conference_id, 'Exception', locals())
            if app.debug:
                raise
            else:
                app.logger.exception("Failed to process document")
                return render_template(
                    "upload.html",
                    error=f"Failed to process document: {filename}",
                    conferences=conferences,
                    args=args)
        finally:
            os.remove(full_path)

    return render_template("upload.html", admin=admin, args=args, conferences=conferences)


def save_log(filename, conference_id, status, args):
    upload_log = Log()
    upload_log.filename = filename
    if current_user.is_authenticated:
        upload_log.app_user_id = current_user.id
    if conference_id:
        conference = Conference.query.filter_by(short_name=conference_id).first()
        if conference:
            upload_log.conference_id = conference.id
    upload_log.status = status
    upload_log.report = json.dumps(json_serialise(args))
    db.session.add(upload_log)
    db.session.commit()

# TODO change to decorator
def is_admin():
    return current_user.is_authenticated and current_user.is_admin

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    form = LoginForm()
    error_message = ''
    if form.validate_on_submit():
        user = AppUser.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            error_message = 'Invalid username or password'
            #return redirect(url_for('login'))
        else:
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('upload'))
    return render_template('login.html', title='Sign In', form=form, message=error_message)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('upload'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # stop this route for the moment, since is_admin is on the form
    # TODO check if logged in and is_admin and then allow is_admin to be set for others
    admin = is_admin()

    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = AppUser(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, admin=admin)


@app.route('/conference', methods=['GET', 'POST'])
@login_required
def conference():
    admin = is_admin()
    if not admin:
        abort(403)

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
def conference_update(id):
    admin = is_admin()
    if not admin:
        abort(403)

    conference = Conference.query.filter_by(id=id).first_or_404()
    form = ConferenceForm(obj=conference)
    if form.validate_on_submit():
        form.populate_obj(conference)
        db.session.commit()

    conferences = Conference.query.all()
    return render_template('conference.html', title='Conference', form=form, conferences=conferences, mode='update')


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    admin = is_admin()
    if not admin:
        abort(403)

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
    return render_template('users.html', title='Users', form=form, users=users, admin=admin)


@app.route('/users/update/<id>', methods=['GET', 'POST'])
@login_required
def user_update(id):
    admin = is_admin()
    if not admin:
        abort(403)

    user = AppUser.query.filter_by(id=id).first_or_404()
    form = RegistrationForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()

    users = AppUser.query.all()
    return render_template('users.html', title='Users', form=form, users=users, mode='update')


@app.route("/convert", methods=["GET", "POST"])
@login_required
def convert():
    admin = is_admin()
    if not admin:
        abort(403)

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

    return render_template("convert.html", admin=admin, action='convert')


@app.route("/summary", methods=["GET"])
@login_required
def summary():
    admin = is_admin()
    if not admin:
        abort(403)

    logs = Log.query.order_by(Log.timestamp.desc()).all()
    # countLogs is an array of tuples
    countLogs = Log.query.with_entities(Log.filename, func.count(Log.filename)).group_by(Log.filename).all()

    return render_template("summary.html", logs=logs, countLogs=countLogs, admin=admin)

@app.route("/log", methods=["GET"])
@login_required
def log():
    admin = is_admin()
    if not admin:
        abort(403)

    logs = []
    if 'SQLALCHEMY_DATABASE_URI' in app.config:
        logs = Log.query.all()
    return render_template("logs.html", logs=logs, admin=admin)
