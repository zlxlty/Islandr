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
def add_reminder(id, time, app):
    print(id, scheduler.get_job(str(id))) #for testing
    if scheduler.get_job(str(id)) == None:
        scheduler.add_job(id=str(id), func=reminder_email, kwargs={'app':app, 'post_id':id}, trigger='cron', year=time[0], month=time[1], day=time[2]-1, hour=8)
    else:
        scheduler.modify_job(id=str(id), func=reminder_email, kwargs={'app':app, 'post_id':id}, trigger='cron', year=time[0], month=time[1], day=time[2]-1, hour=8)

def send_bulletin(app):
    if scheduler.get_job('send_bullentin') == None:
        scheduler.add_job(id='send_bullentin', func=bulletin_email, args=[app], trigger='cron', day_of_week='sun', hour=8)
    else:
        scheduler.modify_job(id='send_bullentin', func=bulletin_email, args=[app], trigger='cron', day_of_week='sun', hour=8)