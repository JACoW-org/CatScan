from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from TexSoup import TexSoup
from flask import render_template, request
from app.docutils.page import check_tracking_on
from app.docutils.doc import create_upload_variables, create_upload_variables_latex
from app.refdb import authenticate, get_references, create_spms_variables, get_conferences
from app.upload import upload_file, delete_file, get_name, get_full_path
from flask import Blueprint

routes = Blueprint('routes', __name__)


@routes.route("/", methods=["GET"])
def upload():
    conferences = filter(lambda x: not x['isPublished'], get_conferences(authenticate()))
    return render_template("upload.html", conferences=conferences)


@routes.route("/validator", methods=["POST"])
def main():
    filename, error_or_extension = upload_file(request)

    if filename is None:
        error = error_or_extension
        return render_template("error.html", error=error), 400

    conference_id = request.form["conference_id"]
    references = []
    if conference_id != '' and conference_id.isdigit():
        references = get_references(authenticate(), conference_id)

    full_path = get_full_path(filename)
    paper_name = get_name(filename)

    try:
        metadata, summary, title = [], None, None

        if error_or_extension == 'tex':
            doc = TexSoup(open(full_path, encoding="utf8"))
            summary, authors, title = create_upload_variables_latex(doc)
        elif error_or_extension == 'docx':
            doc = Document(full_path)
            metadata = doc.core_properties
            tracking_is_on = check_tracking_on(doc)

            if tracking_is_on:
                return render_template("error.html",
                                       error="Cannot process file, tracking is turned on")

            details, error = create_upload_variables(doc)

            if details is None:
                return render_template("error.html", error=error)

            summary, authors, title = details
        else:
            return render_template("error.html", error="Unknown extension")

        if conference_id:
            reference_check_summary, reference_details = create_spms_variables(paper_name, authors, title, references)
            if reference_check_summary is not None and reference_details is not None:
                summary.update(reference_check_summary)

        delete_file(request)
        return render_template("report.html", filename=filename, summary=summary, metadata=metadata)
    except (PackageNotFoundError, ValueError):
        return render_template(
            "report.html",
            error=f"Failed to open document. Is it a valid document?")
    except OSError:
        return render_template(
            "error.html",
            error=f"File is corrupted, and cannot be read")
    finally:
        delete_file(request)
    # except Exception:
    #     print(Exception)
        # return render_template(
        #     "error.html",
        #     error=f"An unknown error occured")


@routes.route("/resources", methods=["GET"])
def resources():
    return render_template("resources.html")


