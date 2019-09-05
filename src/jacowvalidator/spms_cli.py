import click
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from TexSoup import TexSoup
from jacowvalidator import app
from jacowvalidator.docutils.page import (check_tracking_on, TrackingOnError)
from jacowvalidator.docutils.doc import create_upload_variables, create_spms_variables, create_upload_variables_latex, \
    AbstractNotFoundError
from .spms import PaperNotFoundError


@app.cli.command("upload")
def upload():
    print('hello')


@app.cli.command("upload_from_spms")
@click.argument("paper_name")
@click.argument("parse_type")
def upload_from_spms(paper_name, parse_type):
    base_path = 'C:\\\\Users\Hawke\\\\PycharmProjects\\\\jacow_files\\\\IPAC19 Test Files\\\\'
    try:
        spms_summary = ''
        full_path = base_path+paper_name+'.'+parse_type
        conference_path = 'C:\\\\Users\\\\Hawke\\\\PycharmProjects\\\\References_ipac19.csv'
        if parse_type == 'docx':
            doc = Document(full_path)
            # check whether tracking on (will  raise an error if it is)
            check_tracking_on(doc)
            # get variables
            summary, authors, title = create_upload_variables(doc)
            spms_summary, reference_csv_details = create_spms_variables(paper_name, authors, title, conference_path)
        elif parse_type == 'tex':
            doc = TexSoup(open(full_path, encoding="utf8"))
            summary, authors, title = create_upload_variables_latex(doc)
            spms_summary, reference_csv_details = create_spms_variables(paper_name, authors, title, conference_path)
        print(spms_summary)
        return spms_summary

    except (PackageNotFoundError, ValueError):
        message = f"Failed to open document. Is it a valid {parse_type} document?"
    except TrackingOnError as err:
        message = err
    except OSError:
        message = f"It seems the file {paper_name} is corrupted"
    except PaperNotFoundError:
        message = f"It seems the file {paper_name} has no corresponding entry in the SPMS ({conference_path}) " \
            f"references list. Is your filename the same as your Paper name?"
    except AbstractNotFoundError as err:
        message = err
    except Exception:
        app.logger.exception("Failed to process document")
        message = f"Failed to process document: {paper_name}"

    print(message)
    return message

