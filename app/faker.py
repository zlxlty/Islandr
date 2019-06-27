from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post, Group
from flask import current_app
from app import search

def _get_key (dict , value):
    return str([k for k, v in dict.items() if v == value][0])

def test_user():
    u = User(email='skylty01@gmail.com',
             username='Sky',
             password='123',
             confirmed=True,
             is_admin=True)
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

def groups():
    fake = Faker('en_US')
    user_count = User.query.count()
    for i in range(user_count):
        u = User.query.offset(i).first()
        g = Group(groupname=fake.name(),
                  tag=_get_key(current_app.config['TAGS'], randint(0, 5)),
                  about_us=fake.text())
        u.my_group = g
        g.members.append(u)
        db.session.add(u)
        db.session.add(g)
    db.session.commit()

def followers(post, count=10):
    fake = Faker('en_US')
    i=0
    for user in User.query.all():
        if i >= count:
            break
        if user.is_following(post):
            continue
        post.followers.append(user)
        i += 1
    db.session.commit()

def posts(count=100):
    fake = Faker('en_US')
    group = Group.query.filter_by(is_approved=1)
    group_count = group.count()
    for i in range(count):
        g = group.offset(randint(0, group_count - 1)).first()
        p = Post(title='Activity %d' % i, 
                 location=fake.city(),
                 tag=_get_key(current_app.config['TAGS'], randint(0, 5)),
                 post_html=fake.text(),
                 author=g)
        db.session.add(p)
    db.session.commit()
    search.update_index()
