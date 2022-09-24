from flask import Flask
from app.routes import routes
from app.errors import errors
from app.filters import blueprint


app = Flask(__name__)
app.register_blueprint(routes)
app.register_blueprint(errors)
app.register_blueprint(blueprint)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
