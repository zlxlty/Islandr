import os
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Post, Group, Join, Message
import json

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Post=Post, Group=Group, Join=Join, Message=Message)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

# 这里应该重构一下，不知道放哪好
@app.template_filter() # Jinja2 custom filter
def str_to_dic(str):
    return json.loads(str)

@app.template_filter() # Jinja2 custom filter: remove ".jpg" part or any extension of a file
def remove_ext(file_name):
    components = file_name.split(".")
    return components[0]
