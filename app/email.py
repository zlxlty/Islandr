'''
@Description: Email Functions
@Author: Tianyi Lu
@Date: 2019-08-11 21:29:26
@LastEditors: Tianyi Lu
@LastEditTime: 2019-08-11 21:29:33
'''
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail
from . import scheduler
from . import db
from .models import User, Post

import jinja2
import datetime
import time


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
                weekdays = []
                switch_weekday = {1: 'Monday', 2: 'Tuesday', 3:'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
                
                for i in range(len(User.query.all())):
                        email = User.query.all()[i].email
                        all_emails.append(email)
                
                for i in next_week_posts:
                        weekday = i.datetime_from.isoweekday()
                        if weekday not in weekdays:
                                weekdays.append(weekday)
                msg = Message(subject="Islander weekly Bulletin", sender=app.config['FLASKY_MAIL_SENDER'],recipients=all_emails)
                msg.body = render_template('mail/bulletin.txt', posts = next_week_posts, length=range(len(next_week_posts)), weekdays=weekdays, switch_weekday=switch_weekday)
                msg.html = render_template('mail/bulletin.html', posts = next_week_posts, length=range(len(next_week_posts)), weekdays=weekdays, switch_weekday=switch_weekday)
        
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return thr


def reminder_email(app):
        from .event.views import get_post
        
        tmr_posts = get_reminder_post(app)

        with app.app_context():
                for i in tmr_posts:
        
                        post_id = i.id
                        print(post_id)
                        post = get_post(post_id)
                        users = post.followers.all()
                        follower_emails =[]

                        for a in range(len(users)):
                                email = users[a].email
                                follower_emails.append(email)
                
                        msg = Message(subject="Islander event reminder", sender=app.config['FLASKY_MAIL_SENDER'],recipients=follower_emails)
                        msg.body = render_template('mail/reminder.txt', post=post)
                        msg.html = render_template('mail/reminder.html', post=post)

                        thr = Thread(target=send_async_email, args=[app, msg])
                        thr.start()
                        time.sleep(0.1)
                
                return thr


def get_bulletin_post(app):
        now = datetime.datetime.today()
        delta_monday = datetime.timedelta(hours=16)
        delta_sunday = datetime.timedelta(days=7, hours=16)
        next_monday = now + delta_monday
        next_sunday = now + delta_sunday
        with app.app_context():
                posts = Post.query.filter(next_monday < Post.datetime_from, Post.datetime_from < next_sunday, Post.is_approved == '1').all()
        return posts


def get_reminder_post(app):
        now = datetime.datetime.today()
        delta_now = datetime.timedelta(hours=17)
        delta_tmr = datetime.timedelta(days=1, hours=17)
        begin_tmr = now + delta_now
        end_tmr = now + delta_tmr
        with app.app_context():
                posts = Post.query.filter(begin_tmr < Post.datetime_from, Post.datetime_from < end_tmr, Post.is_approved == '1').all()
        return posts

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


