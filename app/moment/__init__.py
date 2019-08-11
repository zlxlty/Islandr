from flask import Blueprint

moment = Blueprint('moment', __name__)

from . import views
