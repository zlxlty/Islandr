from flask import current_app, render_template
from . import scheduler
from .email import send_simple_email, reminder_email, bulletin_email

#testing function 
def add_job():
    scheduler.add_job('job1', job_1, trigger='interval', seconds=2)

def sending_emails():
    scheduler.add_job('email', send_simple_email, args=[current_app._get_current_object()])

def job_1():
    print('123')

#official working function 
def add_reminder(id, app, to, info, time):
    scheduler.add_job(id=id, func=reminder_email, args=[app,to], kwargs=[info], trigger='cron', ) 

def send_bulletin(app, info):
    scheduler.add_job(id='send_bullentin', func=bulletin_email, args=[app], kwargs=[info], trigger='cron', ) 