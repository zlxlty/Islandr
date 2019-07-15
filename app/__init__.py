from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_avatars import Avatars
from .flask_msearch import Search
from config import config
from flask_apscheduler import APScheduler


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
avatars = Avatars()
search = Search(db=db)
login_manager.login_view = 'auth.login'
scheduler =APScheduler()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)

    avatars.init_app(app)
    search.init_app(app)
    
    scheduler.start()
    from .job import send_bulletin
    from flask import current_app
    with app.app_context():
        send_bulletin(current_app._get_current_object())


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .event import event as event_blueprint
    app.register_blueprint(event_blueprint, url_prefix='/event')

    from .group import group as group_blueprint
    app.register_blueprint(group_blueprint, url_prefix='/group')

    return app

