from flask import render_template, abort, url_for, request, redirect, flash, current_app
from flask_login import login_required, current_user
from . import moment
from .. import db
from ..models import Moment, Post
from ..image_saver import saver, deleter
from datetime import datetime
import json


@moment.route('/create_moment', methods=['GET', 'POST'])
@login_required
def create_moment():
    if not current_user.my_group:
        abort(403)

    if request.method == 'POST':

        moment_text = str(request.form['body'])
        moment_pictures = request.files.getlist("pictures")
        event = request.form['link'] # User wants to link moment with this event

        if event == "None":
            flash("One moment MUST link with one event of your team.", 'danger')
            return redirect(url_for('.create_moment'))
        else:
            event = Post.query.get_or_404(int(event))

        #Make sure at 1 to 9 pictures are uploaded
        if str(moment_pictures[0]) == "<FileStorage: '' ('application/octet-stream')>":
            flash("At least ONE picture is required for a Moment.", 'danger')
            return redirect(url_for('.create_moment'))
        if len(moment_pictures) > 9:
            flash("Maximum 9 pictures are allowed for a Moment.", 'danger')
            return redirect(url_for('.create_moment'))

        # save pictures to local
        pic_names = {}
        pic_index = 0
        for picture in moment_pictures:
            pic_index += 1
            pic_names[str(pic_index)] = saver('moment', picture, current_user)

        pic_names_str = json.dumps(pic_names)

        # save text and pics to the database
        moment = Moment(body=moment_text,
                        pictures=pic_names_str,
                        from_group=current_user.my_group,
                        from_post=event)
        db.session.add(moment)
        db.session.commit()

        return redirect(url_for('.moments'))

    return render_template('create_moment.html', group=current_user.my_group)

@moment.route('/moments')
@login_required
def moments():
    page = request.args.get('page', 1, type=int)
    pagination = Moment.query.order_by(Moment.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_MOMENTS_PER_PAGE'], error_out=False)
    moments = pagination.items #moments is a list
    return render_template('moments.html', moments=moments, pagination=pagination)

@moment.route('/<int:id>/<hex>/delete')
@login_required
def delete_moment(id, hex):
    moment = Moment.query.get_or_404(id)
    if moment.from_group.owner[0].id != current_user.id:
        abort(403)

    # delete local files
    picture_dict = json.loads(moment.pictures) # convert str to dict object
    for index in range(1, len(picture_dict) + 1):
        file_name = picture_dict[str(index)]
        deleter('moment', file_name, moment_dir=moment.from_group.id)

    db.session.delete(moment)
    db.session.commit()

    flash('Your Moment has been deleted!')
    return redirect(request.referrer)
