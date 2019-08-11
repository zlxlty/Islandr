'''
@Description: Update index for search function
@Author: Tianyi Lu
@Date: 2019-07-05 14:57:18
@LastEditTime: 2019-07-07 17:54:23
@LastEditors: Tianyi Lu
'''

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