from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post
from ..email import send_email
from . import event
from ..decorators import admin_required
from datetime import datetime

time_format = '%Y-%m-%d-%H:%M'

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
        old_post.title = request.form['title']
        old_post.post_html = request.form['content']
        old_post.last_modified = datetime.utcnow()
        old_post.is_approved = 0
        db.session.add(old_post)
        db.session.commit()
        return redirect(url_for('event.post', id=id))
    return render_template('editor.html', old_post=old_post, old_time_from=strtime_from, old_time_to=strtime_to) 
