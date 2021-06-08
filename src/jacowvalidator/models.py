from datetime import datetime
from jacowvalidator import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return AppUser.query.get(int(id))

class AppUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean(), nullable=False, default=False, server_default='false')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(25))
    report = db.Column(db.Text())
    conference_id = db.Column(db.Integer, db.ForeignKey('conference.id'), nullable=True)
    conference = db.relationship('Conference', backref=db.backref('logs', lazy='dynamic'))
    app_user_id = db.Column(db.Integer, db.ForeignKey('app_user.id'), nullable=True)
    app_user = db.relationship('AppUser', backref=db.backref('logs', lazy='dynamic'))

    def __repr__(self):
        return '<Log {} {}>'.format(self.filename, self.timestamp)


class Conference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    url = db.Column(db.String(50), nullable=False)
    path = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')

    def __repr__(self):
        return '<Conference {}>'.format(self.name)
