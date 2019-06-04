from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)
    location = db.Column(db.String(64), index=True)
    tag = db.Column(db.String(20), index=True)
    datetime_from = db.Column(db.DateTime(), default=datetime.utcnow)
    datetime_to = db.Column(db.DateTime(), default=datetime.utcnow)
    last_modified = db.Column(db.DateTime(), default=datetime.utcnow)
    post_html = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_approved = db.Column(db.Integer, default=0)

    def duration(self):
        return self.datetime_to - self.datetime_from

    def __repr__(self):
        return '<Post %r>' % self.title

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


