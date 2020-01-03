'''
@Description: Blueprint for event
@Author: Tianyi Lu
@Date: 2019-08-09 15:41:15
@LastEditors  : Tianyi Lu
@LastEditTime : 2020-01-03 15:56:15
'''
from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort, jsonify
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post
from ..email import send_email
from . import event
from ..decorators import admin_required, owner_required
from datetime import datetime
from ..image_saver import saver, deleter

from ..job import add_reminder, send_test_reminder

import os

time_format = '%Y-%m-%d-%H:%M'

@event.route('/all', methods=['GET', 'POST'])
@login_required
def all_post():
    datetime_from = datetime_to = None
    if request.method == 'POST':
        try:
            datetime_from = datetime.strptime(request.form['datetime_from'], '%Y-%m-%d')
            datetime_to = datetime.strptime(request.form['datetime_to'], '%Y-%m-%d')
        except ValueError:
            pass
    print(datetime_from)
    page = request.args.get('page', 1, type=int)
    if not datetime_from:
        pagination = Post.query.filter_by(is_approved=1).order_by(Post.datetime_from.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    else:
        pagination = Post.query.filter_by(is_approved=1).filter(Post.datetime_from > datetime_from).filter(Post.datetime_from < datetime_to).order_by(Post.datetime_from).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('all_post.html', posts=posts, pagination=pagination)

@event.route('/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    body_html = Markup(post.post_html)
    return render_template('post.html', id=id, post=post, body_html=body_html)

@event.route('/<int:id>/approved')
@login_required
@admin_required
def post_approved(id):
    post = Post.query.get_or_404(id)
    if post.is_approved == 0:
        post.is_approved = 1
    elif post.is_approved == -1:
        return redirect(url_for('event.post_rejected', id=id))
    db.session.add(post)

    #send post approve message to post author
    post.author.owner[0].add_msg({'role': 'notification',
                                  'name': 'Event Approved',
                                  'content': 'Your event \"%s\" has been approved' % post.title})
    db.session.commit()
    post_datetime = post.datetime_from
    time = [post_datetime.year, post_datetime.month, post_datetime.day]
    return render_template('post_approved.html')

@event.route('/<int:id>/rejected', methods=['GET', 'POST'])
@login_required
@admin_required
def post_rejected(id):
    post = Post.query.get_or_404(id)
    if post.is_approved == 0:
        post.is_approved = -1
    elif post.is_approved == 1:
        return redirect(url_for('event.post_approved', id=id))

    if request.method == 'POST':
        post.reject_msg = request.form['comment']
        # print(post.reject_msg)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.approve'))

    db.session.add(post)
    post.author.owner[0].add_msg({'role': 'notification',
                                  'name': 'Event Rejected',
                                  'content': 'Sorry, your event \"%s\" has been rejected' % post.title})
    db.session.commit()
    return render_template('post_rejected.html')

@event.route('/<int:id>/followers')
@login_required
def post_followers(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.followers.paginate(page, per_page=12, error_out=False)
    users = pagination.items
    user_amount = post.followers.count()
    return render_template('followers.html', post=post, pagination=pagination, users=users, user_amount=user_amount)

@event.route('/<int:id>/follow')
@login_required
def post_follow(id):
    post = Post.query.get_or_404(id)
    if post.has_passed():
        abort(403)
    post.followers.append(current_user)
    post.author.owner[0].add_msg({'role': 'notification',
                                  'name': 'Follower',
                                  'content': '\"%s\" starts to follow your event \"%s\"' % (current_user.username, post.title)})
    db.session.commit()
    return redirect(url_for('.post', id=id))

@event.route('/<int:id>/unfollow')
@login_required
def post_unfollow(id):
    post = Post.query.get_or_404(id)
    if post.has_passed():
        abort(403)
    if not current_user in post.followers.all():
        return redirect(url_for('.post', id=id))
    post.followers.remove(current_user)
    db.session.commit()
    return redirect(url_for('.post', id=id))

@event.route('/<int:id>/delete', methods=['GET'])
@login_required
@owner_required
def post_delete(id):
    post = Post.query.get_or_404(id)
    if not post in current_user.my_group.posts.all():
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('group.group_profile', id=current_user.my_group.id))

@event.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def post_edit(id):

    old_post = Post.query.get_or_404(id)
    if old_post.author.id != current_user.group_id:
        abort(403)

    strtime_from = old_post.datetime_from.strftime(time_format)
    strtime_to = old_post.datetime_to.strftime(time_format)

    if request.method == 'POST':
        if not request.form['title'] or not request.form['content']:
            flash('Write Something!', 'danger')
            return redirect(url_for('event.post_edit', id=id))

        if request.files['cover']:
            if old_post.cover != 'default.jpg':
                deleter('post_cover_pic', old_post.cover)
            cover = request.files['cover']
            cover_filename = saver('post_cover_pic', cover)
            old_post.cover = cover_filename

        old_post.title = request.form['title']
        old_post.post_html = request.form['content']
        old_post.tag = request.form['tag']
        print()
        old_post.datetime_from = datetime.strptime(request.form['datetime_from'], time_format)
        old_post.datetime_to = datetime.strptime(request.form['datetime_to'], time_format)
        old_post.last_modified = datetime.utcnow()
        old_post.is_approved = 0
        db.session.add(old_post)
        db.session.commit()
        return redirect(url_for('event.post', id=id))
    return render_template('editor.html', old_post=old_post, old_time_from=strtime_from, old_time_to=strtime_to)

# test reminder function
@event.route('/<int:id>/send_reminder')
def post_test_reminder(id):
    post = Post.query.get_or_404(id)
    post_datetime = post.datetime_from
    # time = [post_datetime.year, post_datetime.month, post_datetime.day]
    time = datetime.now().minute
    send_test_reminder(current_app._get_current_object())
    return "send_test_reminder"

@event.route('/QR_Code', methods=['GET', 'POST'])
def qr_code():
    try:
        id = int(request.form['id'])
    except:
        id = 0
    print(id)
    if id != 0:
        print('Hello')
        print(current_app.root_path)
        qr_dir = os.path.join(current_app.root_path, 'static/QR_Code')
        print(qr_dir)
        qr_file = os.path.join(qr_dir, '%d.png' % id)
        print(qr_file)
        if not os.path.exists(qr_dir):
            os.mkdir(qr_dir)
        if not os.path.exists(qr_file):
            import qrcode

            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1
            )#设置二维码的大小
            qr.add_data(url_for("event.post", id=id, _external=True))
            qr.make(fit=True)
            img = qr.make_image()
            img.save(qr_file)

    return jsonify(QR_html=render_template('QR_Code.html', event_id=id))

# get current post attributes, used in email.py
def get_post(id):
    post = Post.query.get_or_404(id)
    return post
