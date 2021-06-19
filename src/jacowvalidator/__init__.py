import os
from flask import Flask
from flask_uploads import UploadSet, configure_uploads
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

document_docx = UploadSet("document", "docx")
document_tex = UploadSet("document", "tex")

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config.from_object('jacowvalidator.config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

configure_uploads(app, (document_docx, document_tex))

from jacowvalidator.routes import main, admin, errors
from jacowvalidator import spms_cli

