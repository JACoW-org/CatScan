import os
import json
from datetime import datetime
from subprocess import run
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from TexSoup import TexSoup
from flask import redirect, render_template, request, url_for, flash
from flask_uploads import UploadNotAllowed
from jacowvalidator import app, document_docx, document_tex, db
from jacowvalidator.utils import json_serialise
from jacowvalidator.docutils.page import (check_tracking_on, TrackingOnError)
from jacowvalidator.docutils.doc import create_upload_variables, create_spms_variables, create_upload_variables_latex, \
    AbstractNotFoundError
from jacowvalidator.spms import get_conference_path, PaperNotFoundError
from flask_login import current_user, login_user, logout_user, login_required
from jacowvalidator.models import AppUser, Conference, Log
from jacowvalidator.forms.login import LoginForm, RegistrationForm
from jacowvalidator.routes.admin import is_admin

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
def main():
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


@app.route('/user/<username>')
@login_required
def user_profile(username):
    app_user = AppUser.query.filter_by(username=username).first_or_404()
    logs = Log.query.filter_by(app_user_id=app_user.id).all()
    return render_template('profile.html', user=app_user, logs=logs)


# helper functions below
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
