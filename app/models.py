from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime, timedelta
import random
import secrets

registrations = db.Table('registrations',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'))
)

class Join(db.Model):
    __tablename__ = 'joins'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                         primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                         primary_key=True)
    is_approved = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Join %r %r>' % (self.group_id, self.user_id)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __searchable__ = ['email', 'username', 'skills']

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    skills = db.Column(db.String(128), index=True, default='Enter your skill set (separate with \',\')')
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    #Message
    msgs = db.relationship('Message', backref='user',
                                    lazy='dynamic')

    #Group
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

    # user profile page info
    profile_pic = db.Column(db.String(64), nullable=False, default='default.jpg')
    name = db.Column(db.String(128), default=' / ')
    location = db.Column(db.String(128), default=' / ')
    user_hex = db.Column(db.String(16), default=secrets.token_hex(8))
    about_me = db.Column(db.Text(), default='Nothing here yet...')

    #Join
    groups = db.relationship('Join',
                             foreign_keys=[Join.user_id],
                             backref=db.backref('member', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')

    #follow events
    followings = db.relationship('Post',
                                   secondary=registrations,
                                   backref=db.backref('followers', lazy='dynamic'),
                                   lazy='dynamic')
    def get_skills(self):
        return [x.strip() for x in self.skills.split(',')]

    def get_joined_group(self):
        joined_groups = []
        joins = self.groups.filter_by(is_approved=1).all()
        for join in joins:
            group = Group.query.get(join.group_id)
            joined_groups.append(group)

        return joined_groups

    def been_approved(self, group):
        if group.id == None:
            return False
        return self.groups.filter_by(group_id=group.id).first().is_approved == 1

    def has_joined(self, group):
        if group.id == None:
            return False
        return self.groups.filter_by(group_id=group.id).first() is not None

    def is_following(self, post):
        if post.id == None:
            return False
        return post in self.followings.all()

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

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    # Message
    def add_msg(self, msg):
        m = Message(user=self, role=msg['role'], name=msg['name'], content=msg['content'])
        db.session.add(m)
        db.session.commit()
        return m

    def count_msg(self):
        return self.msgs.filter_by(is_read=False).count()

    def clear_msg(self):
        for msg in self.msgs.filter_by(is_read=False).all():
            msg.is_read = True
        db.session.commit()

    def __repr__(self):
        return '<User %r>' % self.username

class Group(db.Model):
    __tablename__ = 'groups'
    __searchable__ = ['groupname']

    id = db.Column(db.Integer, primary_key=True)

    # relationship with Post
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # relationship with User
    owner = db.relationship('User', backref=db.backref("my_group", uselist=False))

    # relationship with Moment
    moments = db.relationship('Moment', backref='from_group', lazy='dynamic')

    #Join
    members = db.relationship('Join',
                             foreign_keys=[Join.group_id],
                             backref=db.backref('group', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')

    #basic info
    create_date = db.Column(db.DateTime(), default=datetime.now)
    groupname = db.Column(db.String(64), index=True)
    about_us = db.Column(db.Text, default='Nothing here yet...')
    logo = db.Column(db.String(64), default='default.jpg')
    background = db.Column(db.String(64), default='default.jpg')
    is_approved = db.Column(db.Integer, default=0)
    reject_msg = db.Column(db.Text)

    @staticmethod
    def get_explore_groups():
        explore_groups = {
            'latest':[],
            'popular':[],
            'random':[]
        }

        groups = Group.query.filter_by(is_approved=1)
        groups_list = groups.all()
        groups_num = groups.count()
        explore_groups['latest'] = groups.order_by(Group.create_date.desc()).all()[:6]
        groups_list.sort(key=Group.member_count, reverse=True)
        explore_groups['popular'] = groups_list[:6]

        amount = 6
        if groups_num < 6:
            amount = groups_num
        for i in random.sample(range(groups_num), amount):
            explore_groups['random'].append(groups_list[i])

        return explore_groups

    def member_count(self):
        return self.members.count()

    def __repr__(self):
        return '<Group %r>' % self.groupname


class Post(db.Model):
    __tablename__ = 'posts'
    __searchable__ = ['title', 'tag']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)
    location = db.Column(db.String(64), index=True)
    tag = db.Column(db.String(20), index=True)
    datetime_from = db.Column(db.DateTime(), default=datetime.now, index=True)
    datetime_to = db.Column(db.DateTime(), default=datetime.now)
    last_modified = db.Column(db.DateTime(), default=datetime.now)
    post_html = db.Column(db.Text)
    reject_msg = db.Column(db.Text)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    is_approved = db.Column(db.Integer, default=0, index=True) # -1=reject, 0=pending, 1=approved
    cover = db.Column(db.String(64), default='default.jpg')

    # relationship with Moment: one-to-many
    moments = db.relationship('Moment', backref='from_post', lazy='dynamic')

    @staticmethod
    def get_week_posts():
        week_posts = {
            'Mon':[],
            'Tue':[],
            'Wed':[],
            'Thr':[],
            'Fri':[],
            'Sat':[],
            'Sun':[],
        }

        today_begin = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_begin.replace(hour=23, minute=59, second=59)
        current_weekday = today_begin.isoweekday()

        for i, key in enumerate(week_posts.keys(), start=1):
            delta = timedelta(days=i-current_weekday)
            that_day_begin = today_begin + delta
            that_day_end = today_end + delta
            week_posts[key] = Post.query.filter_by(is_approved=1).filter(Post.datetime_from >= that_day_begin, Post.datetime_from <= that_day_end).all()

        return week_posts

    def has_passed(self):
        return self.datetime_from < datetime.now()

    def duration(self):
        return self.datetime_to - self.datetime_from

    def __repr__(self):
        return '<Post %r>' % self.title

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(64), index=True)
    name = db.Column(db.String(128), index=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(), default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    #relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def get_time(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self):
        return '<Message %r>' % self.name

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Moment(db.Model):
    __tablename__ = 'moments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    pictures = db.Column(db.String(), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
