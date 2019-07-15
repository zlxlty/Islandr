from flask import render_template, abort, url_for, request, redirect, flash, current_app
from flask_login import login_required, current_user
from . import group
from .. import db
from ..models import Group, Post, User, Join
from ..decorators import admin_required
from ..image_saver import saver, deleter

@group.route('/<int:id>')
@login_required
def group_profile(id):
    group = Group.query.get_or_404(id)
    if group.is_approved != 1 and current_user.id != group.owner[0].id and current_user.is_admin == False:
        abort(403)
    page = request.args.get('page', 1, type=int)
    if not current_user.id == group.owner[0].id:
        group.posts = group.posts.filter_by(is_approved=1)
    pagination = group.posts.order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    users=[]
    joins = group.members.filter_by(is_approved=1).all()
    for join in joins:
        user = User.query.get_or_404(join.user_id)
        users.append(user)
    posts = pagination.items
    logo = url_for('static', filename="group_logo/"+group.logo)
    background = url_for('static', filename="group_background_pic/"+group.background)
    return render_template('group_profile.html', users=users, group=group, posts=posts,logo=logo, background=background, pagination=pagination)

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

        if request.files['logo']:
            logo = request.files['logo']
            if old_group.logo != 'default.jpg':
                deleter('group_logo', old_group.logo)
            new_logo_filename = saver('group_logo', logo)
            old_group.logo = new_logo_filename

        if request.files['background']:
            background = request.files['background']
            if old_group.background != 'default.jpg':
                deleter('group_background', old_group.background)
            new_background_filename = saver('group_background', background)
            old_group.background = new_background_filename

        old_group.groupname = request.form['groupname']
        old_group.tag = request.form['tag']
        old_group.about_us = request.form['aboutus']

        db.session.add(old_group)
        db.session.commit()

        return redirect(url_for('.group_profile', id=old_group.id))
    return render_template('creater.html', old_group=old_group)

@group.route('/<int:id>/join')
@login_required
def group_join(id):
    group = Group.query.get_or_404(id)
    join = Join(group=group, member=current_user)
    group.owner[0].has_msg = True
    db.session.add(join)
    db.session.commit()
    return redirect(url_for('group.group_profile', id=id))

@group.route('/<int:id>/leave')
@login_required
def group_leave(id):
    group = Group.query.get_or_404(id)
    join = Join.query.filter_by(group_id=group.id).first()
    db.session.delete(join)
    db.session.commit()
    return redirect(url_for('group.group_profile', id=id))

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

@group.route('/application/<int:group_id>/<int:user_id>/approve')
@login_required
def application_approve(group_id, user_id):
    join = Join.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not join:
        abort(404)
    if join.group.owner[0].id != current_user.id:
        abort(403)
    join.is_approved = 1
    join.member.has_msg = True
    db.session.commit()
    return redirect(url_for('main.message'))

@group.route('/application/<int:group_id>/<int:user_id>/reject')
@login_required
def application_reject(group_id, user_id):
    join = Join.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not join:
        abort(404)
    if join.group.owner[0].id != current_user.id:
        abort(403)
    join.member.has_msg = True
    db.session.delete(join)
    db.session.commit()
    return redirect(url_for('main.message'))

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

@group.route('<int:id>/members')
@login_required
def group_members(id):
    group = Group.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = group.members.filter_by(is_approved=1).paginate(page, per_page=12, error_out=False)
    users = []
    for item in pagination.items:
        user = User.query.get_or_404(item.user_id)
        users.append(user)
    member_amount = len(users)
    return render_template('group_members.html', group=group, pagination=pagination, users=users, member_amount=member_amount)
