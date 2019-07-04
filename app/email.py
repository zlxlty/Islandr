from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail
from . import scheduler
from . import db
from .models import User, Post

import jinja2
import datetime


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

def send_simple_email(app):
        message = Message(subject='hello flask-mail',sender=app.config['FLASKY_MAIL_SENDER'], recipients=['multyxu@gmail.com','islandr-csc@outlook.com'],body='flask-mail code forrewqrq trrrreqy')
        thr = Thread(target=send_async_email, args=[app, message])
        thr.start()
        return thr


#official email function for scheduler (modify needed)
def bulletin_email(app,  **kwargs):
        next_week_posts = get_bulletin_post(app)
        with app.app_context():
                all_emails = []
                for i in range(len(User.query.all())):
                        email = User.query.all()[i].email
                        all_emails.append(email)
        msg = Message(subject="Islander weekly Bulletin", sender=app.config['FLASKY_MAIL_SENDER'],recipients=all_emails)
        msg.body = render_without_request('mail/bulletin.txt', posts = next_week_posts, length=range(len(next_week_posts)))
        msg.html = render_without_request('mail/bulletin.html', posts = next_week_posts, length=range(len(next_week_posts)))
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return thr


def reminder_email(app, post_id, **kwargs):
        from .event.views import get_post
        with app.app_context():
                post = get_post(post_id)
                users = post.followers.all()
                follower_emails =[]
                for i in range(len(users)):
                        email = users[i].email
                        follower_emails.append(email)
        msg = Message(subject="Islander envent reminder", sender=app.config['FLASKY_MAIL_SENDER'],recipients=follower_emails)
        msg.body = render_without_request('mail/reminder.txt', post=post)
        msg.html = render_without_request('mail/reminder.html', post=post)
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        print(post.title, type(post))#test
        scheduler.remove_job(str(post_id))
        return thr

#using jinjia2 html without app context in flask
def render_without_request(template_name, **context):
    """
    用法同 flask.render_template:

    render_without_request('template.html', var1='foo', var2='bar')
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('app')
    )
    template = env.get_template(template_name)
    return template.render(**context)

def get_bulletin_post(app):
        now = datetime.datetime.today()
        delta_monday = datetime.timedelta(hours=16)
        delta_sunday = datetime.timedelta(days=7, hours=16)
        next_monday = now + delta_monday
        next_sunday = now + delta_sunday
        with app.app_context():
                posts = Post.query.filter(next_monday < Post.datetime_from, Post.datetime_from < next_sunday, Post.is_approved == '1').all()
        return posts