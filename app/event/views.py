from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post
from ..email import send_email
from . import event
from ..decorators import admin_required
from datetime import datetime
from ..image_saver import saver, deleter

time_format = '%Y-%m-%d-%H:%M'

@event.route('/<int:id>')
@login_required
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
    db.session.commit()
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
    db.session.commit()
    return render_template('post_rejected.html')

@event.route('<int:id>/followers')
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
    post.followers.append(current_user)
    db.session.commit()
    return redirect(url_for('.post', id=id))

@event.route('/<int:id>/unfollow')
@login_required
def post_unfollow(id):
    post = Post.query.get_or_404(id)
    if not current_user in post.followers.all():
        return redirect(url_for('.post', id=id))
    post.followers.remove(current_user)
    db.session.commit()
    return redirect(url_for('.post', id=id))

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
            flash('Write Something!')
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
        old_post.datetime_from = datetime.strptime(request.form['datetime_from'], time_format)
        old_post.datetime_to = datetime.strptime(request.form['datetime_to'], time_format)
        old_post.last_modified = datetime.utcnow()
        old_post.is_approved = 0
        db.session.add(old_post)
        db.session.commit()
        return redirect(url_for('event.post', id=id))
    return render_template('editor.html', old_post=old_post, old_time_from=strtime_from, old_time_to=strtime_to)
