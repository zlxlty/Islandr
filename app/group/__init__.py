from flask import Blueprint

group = Blueprint('group', __name__)

from . import views
