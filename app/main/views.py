from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post
from ..email import send_email
from . import main
from .forms import EditorForm, UpdateAccountForm
from ..decorators import admin_required
from datetime import datetime
import secrets
import os
from PIL import Image


time_format = '%Y-%m-%d-%H:%M'

@main.route('/', methods=['GET', 'POST'])
def index():
    posts = Post.query.filter_by(is_approved=1).order_by(Post.last_modified).all()
    posts = posts[0:6]
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
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return render_template('approve.html', posts=posts, pagination=pagination, title='Approve', valid_num = 0)

@main.route('/<tag>')
@login_required
def tag_events(tag):

    tag = str(tag).capitalize()
    if not tag in current_app.config['TAGS'].keys():
        abort(404)

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(tag=tag).order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return render_template('approve.html', posts=posts, pagination=pagination, title=tag, valid_num = 1)


@main.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()

    if form.validate_on_submit():

        if form.profile_pic.data:
            file_name = save_profile_pic(form.profile_pic.data)
            current_user.profile_pic = file_name

        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.location = form.location.data

        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))

    form.name.data = current_user.name
    form.username.data = current_user.username
    form.location.data = current_user.location

    profile_pic = url_for('static', filename='profile_pic/' + current_user.profile_pic)
    print("pic=", profile_pic)

    return render_template('account.html', form=form, profile_pic=profile_pic)


def save_profile_pic(form_picture):

    # generate a random file name at standard length
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_file_name = random_hex + file_extension

    # crop to square and resize the picutre
    i = Image.open(form_picture)

    width, height = i.size
    new_size = min(width, height)

    left = (width - new_size)/2
    top = (height - new_size)/2
    right = (width + new_size)/2
    bottom = (height + new_size)/2

    i = i.crop((left, top, right, bottom))
    i.thumbnail([100, 100])

    # save it to static folder
    picture_path = os.path.join(current_app.root_path, 'static/profile_pic', picture_file_name)
    i.save(picture_path)

    return picture_file_name
