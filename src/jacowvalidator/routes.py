import os
import json
from datetime import datetime
from subprocess import run
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from TexSoup import TexSoup
from flask import redirect, render_template, request, url_for, send_file, abort
from flask_uploads import UploadNotAllowed

from jacowvalidator import app, document_docx, document_tex
from .models import Log
from jacowvalidator.docutils.page import (check_tracking_on, TrackingOnError)
from jacowvalidator.docutils.doc import create_upload_variables, create_spms_variables, create_upload_variables_latex, \
    AbstractNotFoundError
from .test_utils import replace_identifying_text
from .spms import PaperNotFoundError


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
        return '<span style="color:darkgreen">✓</span>'
    elif s == 2:
        return '<span style="color:darkorange"><i class="fas fa-question"></i></span>'
    else:
        return '<span style="color:darkred">✗</span>'


@app.template_filter('background_style')
def background_style(s):
    return "has-background-success" if s else "has-background-danger"


@app.template_filter('pastel_background_style')
def pastel_background_style(s):
    if s == 1 or s is True:
        return 'DDFFDD'
    elif s == 2:
        return 'ffedcc' #ffedcc
    else:
        return "FFDDDD"


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
        fullpath = documents.path(filename)

        try:
            if args['description'] == 'Word':
                doc = Document(fullpath)
                parse_type = 'docx'
                metadata = doc.core_properties

                # check whether tracking on
                result = check_tracking_on(doc)

                # get variables to pass to template
                summary, authors, title = create_upload_variables(doc)
                spms_summary, reference_csv_details = create_spms_variables(paper_name, authors, title)
                if spms_summary:
                    summary.update(spms_summary)
            elif args['description'] == 'Latex':
                doc = TexSoup(open(fullpath, encoding="utf8"))
                summary, authors, title = create_upload_variables_latex(doc)
                metadata = []
                spms_summary, reference_csv_details = create_spms_variables(paper_name, authors, title)
                if spms_summary:
                    summary.update(spms_summary)

            if 'DATABASE_URL' in os.environ:
                upload_log = Log()
                upload_log.filename = filename
                # upload_log.report = json.dumps(json_serialise(locals()))
                # db.session.add(upload_log)
                # db.session.commit()

            return render_template("upload.html", processed=True, **locals())
        except (PackageNotFoundError, ValueError):
            return render_template(
                "upload.html",
                filename=filename,
                error=f"Failed to open document {filename}. Is it a valid {args['description']} document?",
                admin=admin,
                args=args)
        except TrackingOnError as err:
            return render_template(
                "upload.html",
                filename=filename,
                error=err,
                admin=admin,
                args=args)
        except OSError:
            return render_template(
                "upload.html",
                filename=filename,
                error=f"It seems the file {filename} is corrupted",
                admin=admin,
                args=args)
        except PaperNotFoundError:
            return render_template(
                "upload.html",
                processed=True,
                **locals(),
                error=f"It seems the file {filename} has no corresponding entry in the SPMS references list. "
                      f"Is your filename the same as your Paper name?")
        except AbstractNotFoundError as err:
            return render_template(
                "upload.html",
                filename=filename,
                error=err,
                admin=admin,
                args=args)
        except Exception:
            if app.debug:
                raise
            else:
                app.logger.exception("Failed to process document")
                return render_template(
                    "upload.html",
                    error=f"Failed to process document: {filename}",
                    admin=admin,
                    args=args)
        finally:
            os.remove(fullpath)

    return render_template("upload.html", admin=admin, args=args)


@app.route("/convert", methods=["GET", "POST"])
def convert():
    admin = 'DEV_DEBUG' in os.environ and os.environ['DEV_DEBUG'] == 'True'
    documents = document_docx
    if not admin:
        abort(403)

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


@app.route("/resources", methods=["GET"])
def resources():
    admin = 'DEV_DEBUG' in os.environ and os.environ['DEV_DEBUG'] == 'True'
    return render_template("resources.html", admin=admin)


@app.route("/log", methods=["GET"])
def log():
    admin = 'DEV_DEBUG' in os.environ and os.environ['DEV_DEBUG'] == 'True'
    if not admin:
        abort(403)
    logs = [] #Log.query.all()
    return render_template("logs.html", logs=logs, admin=admin)
