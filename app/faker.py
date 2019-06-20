from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post
from flask import current_app

def _get_key (dict , value):
    return str([k for k, v in dict.items() if v == value][0])

def test_user():
    u = User(email='skylty01@gmail.com',
             username='Sky',
             password='123',
             confirmed=True,)
    db.session.add(u)
    db.session.commit()

def users(count=100):
    fake = Faker('en_US')
    i = 0
    while i < count:
        u = User(email=fake.email(),
                 username=fake.user_name(),
                 password='password',
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city())
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()

def posts(count=100):
    fake = Faker('en_US')
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(title='Activity %d' % i, 
                 location=fake.city(),
                 tag=_get_key(current_app.config['TAGS'], randint(0, 5)),
                 post_html=fake.text(),
                 author=u)
        db.session.add(p)
    db.session.commit()