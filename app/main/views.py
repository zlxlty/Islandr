'''
@Description: View file for main blueprint
@Author: Tianyi Lu
@Date: 2019-07-05 17:27:28
@LastEditors  : Tianyi Lu
@LastEditTime : 2020-01-08 11:21:55
'''

from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort, send_file, make_response, jsonify
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
from ..job import send_test_bulletin
from ..search_index import update_index
from ..image_saver import saver, deleter
from flask_sqlalchemy import get_debug_queries
import os

from ..faker import test_user

time_format = '%Y-%m-%d-%H:%M'

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = str(request.form['search'])
        return redirect(url_for('main.m_search', keyword=keyword))

    posts = Post.get_week_posts()

    groups = Group.get_explore_groups()

    return render_template('index.html', groups=groups, posts=posts)

@main.route('/about_us')
def about_us():
    return render_template('about_us.html')

@main.route('/getting_started')
def getting_started():
    return render_template('getting_started.html')

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
        pending_joins_list = pending_joins.all()
        for join in pending_joins_list:
            applicant = User.query.get(join.user_id)
            applicants.append(applicant)
    elif ctype in current_app.config['MSG_TYPE']:
        msgs = msg_model.filter_by(role=ctype).order_by(Message.timestamp.desc()).all()
    else:
        abort(404)
    return render_template('message.html', ctype=ctype, msgs=msgs, msg_model=msg_model, applicants=applicants, joins=pending_joins)

@main.route('/imageuploader', methods=['GET', 'POST'])
@login_required
def imageuploader():
    file = request.files.get('file')
    if file:
        filename = file.filename.lower()
        fn, ext = filename.split('.')
        filename = fn + '.' + ext
        if ext in ['jpg', 'gif', 'png', 'jpeg']:
            img_fullpath = os.path.join(current_app.config['UPLOADED_PATH'], filename)
            file.save(img_fullpath)
            return jsonify({'location' : filename})

    # fail, image did not upload
    output = make_response(404)
    output.headers['Error'] = 'Image failed to upload'
    return output

@main.route('/search', methods=['GET', 'POST'])
@login_required
def m_search():

    if request.method == 'POST':
        keyword = str(request.form['search'])
        option = str(request.form['option'])
        return redirect(url_for('main.m_search', keyword=keyword, option=option))

    keyword = request.args.get('keyword') or ' '
    keyword_list = keyword.split(' ')
    option = request.args.get('option') or 'event'
    page = request.args.get('page', 1, type=int)

    if option == 'group':
        pagination = Group.query.msearch(keyword_list, fields=['groupname']).filter_by(is_approved=1).order_by(Group.create_date.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out = False)
    elif option == 'user':
        pagination = User.query.msearch(keyword_list, fields=['username','email','skills']).filter_by(confirmed=True).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out = False)
    else:
        pagination = Post.query.msearch(keyword_list, fields=['title','tag']).filter_by(is_approved=1).order_by(Post.last_modified.desc()).paginate(
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
            flash('Please fill in all forms!', 'danger')
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
        flash('You already have a group!', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        if not request.form['groupname']:
            flash('Please fill in the name!', 'danger')
            return redirect(url_for('.group_creater'))

        if not request.files['proposal']:
            flash('Please upload Team Proposal!', 'danger')
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
                      vision_goal=request.form['vision'],
                      routine_events=request.form['routine'],
                      look_for=request.form['join'],
                      logo=logo_filename,
                      background=background_filename)

        current_user.my_group = group
        join = Join(group=group, member=current_user, is_approved=1)
        db.session.add(group)
        db.session.add(join)
        db.session.commit()

        # save proposal file
        if request.files['proposal']:
            proposal_file = request.files['proposal']
            _, ext = os.path.splitext(proposal_file.filename)
            proposal_filename = str(group.id) + '_UWCCSC_TEAM_PROPOSAL' + str(ext)
            dir = os.path.join(current_app.root_path, 'static', 'files', str(group.id))
            if not os.path.isdir(dir):
                os.mkdir(dir)
            proposal_dir = os.path.join(dir, proposal_filename)
            proposal_file.save(proposal_dir)
            group.proposal_file = proposal_filename
            db.session.add(group)
            db.session.commit()

        update_index(Group)
        return redirect(url_for('group.group_profile',id=group.id))
    _group = Group()
    return render_template('creater.html', old_group=_group)

@main.route('/download_file/<filename>')
@login_required
def download_file(filename):
    folder = filename.split('_')[0]
    path = os.path.join(current_app.root_path, 'static', 'files', folder, str(filename))
    if os.path.isfile(path):
        return send_file(path, as_attachment=True)
    else:
        flash("File does not exist!", "warning")
        return redirect(url_for('main.index'))

# @main.route('/upload_file')
# @login_required
# def upload_file():
#     pass


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
        user.wechat_id = form.wechat_id.data
        user.skills = form.skills.data
        user.grade = form.grade.data
        user.about_me = form.about_me.data

        db.session.commit()
        update_index(User)
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account', user_id=user.id))

    form.name.data = user.name
    form.username.data = user.username
    form.location.data = user.location
    form.wechat_id.data = user.wechat_id
    form.skills.data = user.skills
    form.grade.data = user.grade
    form.about_me.data = user.about_me

    return render_template('edit_account.html', form=form)

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
                    (query.statement, query.parameters, query.duration, query.context))
    return response

# test bulletin function
@main.route('/send_test_bulletin', methods=['GET', 'POST'])
def test_bulletin():
    send_test_bulletin(current_app._get_current_object())
    return "bulletin sent"

@main.route('/add_test_user', methods=['GET', 'POST'])
def add_user():
    test_user()
    return "ok"

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
