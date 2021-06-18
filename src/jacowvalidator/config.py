import os
basedir = os.path.abspath(os.path.dirname(__file__))

"""
Default configuration
Use docker-compose or env var to override
"""


class Config:
    # DEBUG = True
    SECRET_KEY = "8W3CzDhs_UwDJZhYC"
    BUILD_ENVS = os.environ.get('BUILD_ENVS') or 'build_envs.txt'

    UPLOADS_DEFAULT_DEST = os.environ.get("UPLOADS_DEFAULT_DEST", "/var/tmp")
    JACOW_REFERENCES_PATH = os.environ.get("JACOW_REFERENCES_PATH", "./spms")

    db_host = os.environ.get("API_DB_HOST") or 'localhost'
    db_port = os.environ.get("API_DB_PORT") or '5432'
    db_user = os.environ.get("API_DB_USER") or 'jacow'
    db_pass = os.environ.get("API_DB_PASS") or 'docker'
    db_name = os.environ.get("API_DB_NAME") or 'jacow'
    SQLALCHEMY_DATABASE_URI = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

