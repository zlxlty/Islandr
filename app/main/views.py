from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from threading import Thread
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post, Group, Join
from ..email import send_email
from . import main
from .forms import EditorForm, UpdateAccountForm
from ..decorators import admin_required, owner_required
from datetime import datetime
from app import search
import os
from PIL import Image

from ..job import add_job, sending_emails

time_format = '%Y-%m-%d-%H:%M'

def async_update_index(app):
    with app.app_context():
        print('started')
        search.update_index()

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = str(request.form['search'])
        return redirect(url_for('main.m_search', keyword=keyword))

    posts = Post.query.filter_by(is_approved=1).order_by(Post.last_modified.desc()).all()
    posts = posts[0:9]

    return render_template('index.html', posts=posts)

@main.route('/about_us')
def about_us():
    return render_template('about_us.html')

@main.route('/message')
@login_required
def message():
    current_user.has_msg = False
    pending_joins = current_user.my_group.members.filter_by(is_approved=0).all()
    applicants = []
    for join in pending_joins:
        applicant = User.query.get(join.user_id)
        applicants.append(applicant)
    db.session.commit()
    return render_template('message.html', applicants=applicants)


@main.route('/search', methods=['GET', 'POST'])
@login_required
def m_search():
    if request.method == 'POST':
        keyword = str(request.form['search'])
        return redirect(url_for('main.m_search', keyword=keyword))

    keyword = request.args.get('keyword')
    # if not keyword:
    #     return redirect(url_for('main.m_search', keyword='default'))

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.msearch(keyword, fields=['title']).filter_by(is_approved=1).order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return render_template('search.html', pagination=pagination, posts=posts, keyword=keyword)

@main.route('/editor', methods=['GET', 'POST'])
@login_required
@owner_required
def post_editor():

    if request.method == 'POST':
        if not request.form['content'] or not request.form['title'] or not request.form['datetime_from'] or not request.form['datetime_to']:
            flash('Please fill in all forms!')
            return redirect(url_for('.post_editor'))

        post = Post(author=current_user.my_group,
                    title=request.form['title'],
                    location=request.form['location'],
                    tag=request.form['tag'],
                    datetime_from = datetime.strptime(request.form['datetime_from'], time_format),
                    datetime_to = datetime.strptime(request.form['datetime_to'], time_format),
                    post_html=request.form['content'].replace('\r\n', '')
        )
        db.session.add(post)
        db.session.commit()
        
        #update search index
        app = current_app._get_current_object()
        thr = Thread(target=async_update_index, args=[app])
        thr.start()

        return redirect(url_for('event.post', id=post.id))
    _post = Post(title='', location='', post_html='')
    return render_template('editor.html', old_post=_post, old_time_from='', old_time_to='')

@main.route('/creater', methods=['GET', 'POST'])
@login_required
def group_creater():

    if current_user.my_group:
        flash('You already have a group!')
        return redirect(url_for('main.index')) 

    if request.method == 'POST':
        if not request.form['groupname']:
            flash('Please fill in the name!')
            return redirect(url_for('.group_creater'))

        group = Group(groupname=request.form['groupname'],
                      tag=request.form['tag'],
                      about_us=request.form['aboutus'])

        current_user.my_group = group
        join = Join(group=group, member=current_user, is_approved=1)
        db.session.add(group)
        db.session.add(join)
        db.session.commit()
        return redirect(url_for('group.group_profile',id=group.id))
    _group = Group()
    return render_template('creater.html', old_group=_group)

@main.route('/moments')
@login_required
def moments():
    #TODO
    return render_template('moments.html')

@main.route('/approve', methods=['GET', 'POST'])
@login_required
@admin_required
def approve():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(is_approved=0).order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return render_template('approve.html', posts=posts, pagination=pagination)

@main.route('/<tag>')
@login_required
def tag_events(tag):

    tag = str(tag).capitalize()
    if not tag in current_app.config['TAGS'].keys():
        abort(404)

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(tag=tag, is_approved=1).order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    tag = tag.lower()
    return render_template('tag.html', posts=posts, pagination=pagination, title=tag)

# @main.route('/my_post/<int:id>')
# @login_required
# def my_post(id):
#     page = request.args.get('page', 1, type=int)
#     user = User.query.get_or_404(id)
#     pagination = user.posts.order_by(Post.last_modified.desc()).paginate(
#         page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
#         error_out = False)
#     posts = pagination.items
#     return render_template('approve.html', posts=posts, pagination=pagination, title='My Events')


@main.route('/account/<int:user_id>', methods=['GET', 'POST'])
@login_required
def account(user_id):

    ctype = request.args.get('ctype') or 'event'
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    
    if ctype == 'event':
        pagination = user.followings.order_by(Post.datetime_from).paginate(
            page, per_page=9,
            error_out = False)
        items = pagination.items
        
    elif ctype == 'group':
        pagination = user.groups.paginate(
            page, per_page=9,
            error_out = False)
        items = []
        joins = pagination.items
        for join in joins:
            item = Group.query.get_or_404(join.group_id)
            items.append(item)
    else:
        abort(404)

    

    profile_pic = url_for('static', filename='profile_pic/' + user.profile_pic)

    return render_template('account.html', type=ctype, user=user, profile_pic=profile_pic, user_id=user_id, items=items, pagination=pagination)


@main.route('/account/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def account_edit(user_id):

    if user_id != current_user.id:
        abort(403)

    user = User.query.get(user_id)
    form = UpdateAccountForm()

    if form.validate_on_submit():

        if form.profile_pic.data:
            file_name = save_profile_pic(form.profile_pic.data, user)
            user.profile_pic = file_name

        user.name = form.name.data
        user.username = form.username.data
        user.location = form.location.data
        user.about_me = form.about_me.data

        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account', user_id=user.id))

    form.name.data = user.name
    form.username.data = user.username
    form.location.data = user.location
    form.about_me.data = user.about_me

    return render_template('edit_account.html', form=form)


def save_profile_pic(form_picture, user):

    random_hex = user.user_hex
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


#test purpose for scheduler and email, not part of actual code
@main.route('/addjob', methods=['GET', 'POST'])
def add_new_job():
    add_job()
    return 'job added'

@main.route('/send',)
def email_sent():
        try:
            sending_emails()
            test_user()
            return '发送成功，请注意查收'
        except Exception as e:
            print(e)
            return '发送失败'