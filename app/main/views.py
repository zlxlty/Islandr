from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post
from ..email import send_email
from . import main
from .forms import EditorForm
from ..decorators import admin_required
from datetime import datetime

time_format = '%Y-%m-%d-%H:%M'

@main.route('/', methods=['GET', 'POST'])
def index():
    posts = Post.query.all()
    
    return render_template('index.html', posts=posts)

@main.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():

    if request.method == 'POST':
        if not request.form['content'] or not request.form['title'] or not request.form['datetime_from'] or not request.form['datetime_to']:
            flash('Please fill in all forms!')
            return redirect(url_for('.editor'))

        post = Post(title=request.form['title'],
                    location=request.form['location'],
                    tag=request.form['tag'],
                    datetime_from = datetime.strptime(request.form['datetime_from'], time_format),
                    datetime_to = datetime.strptime(request.form['datetime_to'], time_format),
                    author=current_user,
                    post_html=request.form['content'].replace('\r\n', '')
        )
        print(request.form['tag'])
        print(type(request.form['tag']))
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('event.post', id=post.id))
    _post = Post(title='', location='', post_html='')
    return render_template('editor.html', old_post=_post, old_time_from='', old_time_to='')

@main.route('/approve', methods=['GET', 'POST'])
@login_required
@admin_required
def approve():
    posts = Post.query.all()
    return render_template('approve.html', posts=posts)