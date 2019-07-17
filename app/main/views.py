'''
@Description: View file for main blueprint
@Author: Tianyi Lu
@Date: 2019-07-05 17:27:28
@LastEditors: Tianyi Lu
@LastEditTime: 2019-07-12 15:17:53
'''

from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from threading import Thread
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post, Group, Join, Message
from ..email import send_email
from . import main
from .forms import EditorForm, UpdateAccountForm
from ..decorators import admin_required, owner_required
from datetime import datetime
from app import search
from ..search_index import update_index
from ..job import add_job, sending_emails
from ..image_saver import saver, deleter

time_format = '%Y-%m-%d-%H:%M'

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = str(request.form['search'])
        return redirect(url_for('main.m_search', keyword=keyword))

    posts = Post.query.filter_by(is_approved=1).order_by(Post.last_modified.desc()).all()
    posts = posts[0:6]

    groups = Group.query.filter_by(is_approved=1).all()
    groups.sort(key=Group.post_count, reverse=True)
    groups = groups[0:4]

    return render_template('index.html', groups=groups, posts=posts)

@main.route('/about_us')
def about_us():
    return render_template('about_us.html')

@main.route('/message')
@login_required
def message():
    ctype = request.args.get('ctype') or 'notification'

    if ctype=='my_group' and not current_user.my_group:
        abort(403)

    if current_user.my_group:
        pending_joins = current_user.my_group.members.filter_by(is_approved=0)
    else:
        pending_joins = []

    current_user.clear_msg()

    applicants = []
    msgs = []
    msg_model = current_user.msgs

    # add different ctype with different msgs
    if ctype == 'my_group':
        if not current_user.my_group:
            abort(403)
        pending_joins_list = pending_joins.all()
        for join in pending_joins_list:
            applicant = User.query.get(join.user_id)
            applicants.append(applicant)
    elif ctype in current_app.config['MSG_TYPE']:
        msgs = msg_model.filter_by(role=ctype).order_by(Message.timestamp.desc()).all()
    else:
        abort(404)
    return render_template('message.html', ctype=ctype, msgs=msgs, msg_model=msg_model, applicants=applicants, joins=pending_joins)

@main.route('/search', methods=['GET', 'POST'])
@login_required
def m_search():

    if request.method == 'POST':
        keyword = str(request.form['search'])
        option = str(request.form['option'])
        return redirect(url_for('main.m_search', keyword=keyword, option=option))

    keyword = request.args.get('keyword') or ' '
    option = request.args.get('option') or 'event'

    page = request.args.get('page', 1, type=int)

    if option == 'group':
        pagination = Group.query.msearch(keyword, fields=['groupname','tag']).filter_by(is_approved=1).order_by(Group.create_date.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out = False)
    elif option == 'user':
        pagination = User.query.msearch(keyword, fields=['username','email','skills']).filter_by(confirmed=True).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out = False)
    else:
        pagination = Post.query.msearch(keyword, fields=['title','tag']).filter_by(is_approved=1).order_by(Post.last_modified.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out = False)

    items = pagination.items
    return render_template('search.html', pagination=pagination, items=items, keyword=keyword, option=option)

@main.route('/editor', methods=['GET', 'POST'])
@login_required
@owner_required
def post_editor():

    if not current_user.my_group:
        abort(403)

    if request.method == 'POST':
        if not request.form['content'] or not request.form['title'] or not request.form['datetime_from'] or not request.form['datetime_to']:
            flash('Please fill in all forms!')
            return redirect(url_for('.post_editor'))
        print("IN POST")

        if request.files['cover']:
            cover = request.files['cover']
            cover_filename = saver('post_cover_pic', cover)
        else:
            cover_filename = "default.jpg"

        post = Post(author=current_user.my_group,
                    title=request.form['title'],
                    location=request.form['location'],
                    tag=request.form['tag'],
                    datetime_from = datetime.strptime(request.form['datetime_from'], time_format),
                    datetime_to = datetime.strptime(request.form['datetime_to'], time_format),
                    post_html=request.form['content'].replace('\r\n', ''),
                    cover=cover_filename
        )
        post.followers.append(current_user)
        db.session.add(post)
        db.session.commit()

        #update search index
        update_index(Post)

        return redirect(url_for('event.post', id=post.id))
    _post = Post(title='', location='', post_html='')
    return render_template('editor.html', old_post=_post, old_time_from='', old_time_to='')

# TODO: upload profile picture
# TODO: upload background picture

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

        if request.files['logo']:
            logo = request.files['logo']
            logo_filename = saver('group_logo', logo)
        else:
            logo_filename = "default.jpg"

        if request.files['background']:
            background = request.files['background']
            background_filename = saver('group_background', background)
        else:
            background_filename = "default.jpg"

        group = Group(groupname=request.form['groupname'],
                      tag=request.form['tag'],
                      about_us=request.form['aboutus'],
                      logo=logo_filename,
                      background=background_filename)

        current_user.my_group = group
        join = Join(group=group, member=current_user, is_approved=1)
        db.session.add(group)
        db.session.add(join)
        db.session.commit()
        update_index(Group)
        return redirect(url_for('group.group_profile',id=group.id))
    _group = Group()
    return render_template('creater.html', old_group=_group)

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
        pagination = user.groups.filter_by(is_approved=1).paginate(
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
            if user.profile_pic != 'default.jpg':
                deleter('user_profile_pic', user.profile_pic)
            file_name = saver('user_profile_pic', form.profile_pic.data, user)
            user.profile_pic = file_name

        user.name = form.name.data
        user.username = form.username.data
        user.location = form.location.data
        user.skills = form.skills.data
        user.about_me = form.about_me.data

        update_index(User)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account', user_id=user.id))

    form.name.data = user.name
    form.username.data = user.username
    form.location.data = user.location
    form.skills.data = user.skills
    form.about_me.data = user.about_me

    return render_template('edit_account.html', form=form)
