from flask import render_template, abort, url_for, request, redirect, flash, current_app
from flask_login import login_required, current_user
from . import group
from .. import db
from ..models import Group, Post
from ..decorators import admin_required

@group.route('/<int:id>')
@login_required
def group_profile(id):
    group = Group.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    if not current_user.id == group.owner[0].id:
        group.posts = group.posts.filter_by(is_approved=1)
    pagination = group.posts.order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return render_template('group_profile.html', group=group, posts=posts, pagination=pagination)

@group.route('/approve')
@login_required
def group_approve():
    group = Group.query.filter_by(is_approved=0).order_by(Group.create_date.desc())
    page = request.args.get('page', 1, type=int)
    pagination = group.paginate(page, per_page=12, error_out=False)
    groups = pagination.items
    return render_template('group_approve.html', groups=groups, pagination=pagination)

@group.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def group_profile_edit(id):
    old_group = Group.query.get_or_404(id)

    if old_group.owner[0].id != current_user.id:
        abort(403)

    if request.method == 'POST':
        if not request.form['groupname']:
            flash("Please fill in the name!")
            return redirect(url_for('.group_profile_edit'))
    
        old_group.groupname = request.form['groupname']
        old_group.tag = request.form['tag']
        old_group.about_us = request.form['aboutus']

        db.session.add(old_group)
        db.session.commit()

        return redirect(url_for('.group_profile', id=old_group.id))
    return render_template('creater.html', old_group=old_group)

@group.route('/<int:id>/approved')
@login_required
@admin_required
def group_approved(id):
    group = Group.query.get_or_404(id)
    if group.is_approved == 0:
        group.is_approved = 1
    elif group.is_approved == -1:
        return redirect(url_for('group.group_rejected', id=id))
    db.session.add(group)
    db.session.commit()
    return render_template('group_approved.html')

@group.route('/<int:id>/rejected', methods=['GET', 'POST'])
@login_required
@admin_required
def group_rejected(id):
    group = Group.query.get_or_404(id)
    if group.is_approved == 0:
        group.is_approved = -1
    elif group.is_approved == 1:
        return redirect(url_for('group.group_approved', id=id))

    if request.method == 'POST':
        group.reject_msg = request.form['comment']
        # print(post.reject_msg)
        db.session.add(group)
        db.session.commit()
        return redirect(url_for('group.group_approve'))

    db.session.add(group)
    db.session.commit()
    return render_template('group_rejected.html')


@group.route('/<int:id>/delete')
@login_required
def group_delete(id):
    old_group = Group.query.get_or_404(id)

    if old_group.owner[0].id != current_user.id:
        abort(403)

    for post in old_group.posts:
        db.session.delete(post)

    db.session.delete(old_group)
    db.session.commit()

    flash('Your group %s has been deleted!' % str(old_group.groupname))
    return redirect(url_for('main.index'))
