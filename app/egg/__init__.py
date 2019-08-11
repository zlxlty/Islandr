'''
@Description: Easter Egg
@Author: Tianyi Lu
@Date: 2019-08-10 10:30:29
@LastEditors: Tianyi Lu
@LastEditTime: 2019-08-10 10:36:24
'''
from flask import Blueprint

egg = Blueprint('egg', __name__)

from . import views