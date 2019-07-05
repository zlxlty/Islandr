from flask import current_app
from threading import Thread
from app import search
from .models import User, Post, Group

def update_index(option):
    app = current_app._get_current_object()
    thr = Thread(target=_async_update_index, args=[app, option])
    thr.start()
    return thr

def _async_update_index(app, option):
    with app.app_context():
        print('started')
        search.update_index(option)