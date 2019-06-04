from flask import Blueprint

event = Blueprint('event', __name__)

from . import views
