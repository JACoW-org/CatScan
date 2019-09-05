import os
from flask import Flask
from flask_uploads import UploadSet, configure_uploads
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

document_docx = UploadSet("document", "docx")
document_tex = UploadSet("document", "tex")

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config.update(
    dict(
        UPLOADS_DEFAULT_DEST=os.environ.get("UPLOADS_DEFAULT_DEST", "/var/tmp"),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

configure_uploads(app, (document_docx, document_tex))

from jacowvalidator import routes
from jacowvalidator import spms_cli

