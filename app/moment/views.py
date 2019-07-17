from flask import render_template, abort, url_for, request, redirect, flash, current_app
from flask_login import login_required, current_user
from . import moment
from .. import db
from ..models import Moment
from ..image_saver import saver
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

        #Make sure at 1 to 9 pictures are uploaded
        if not request.files["pictures"]:
            flash("At least ONE picture is required for a Moment.")
            return redirect(url_for('.create_moment'))
        if len(moment_pictures) > 9:
            flash("Maximum 9 pictures are allowed for a Moment.")
            return redirect(url_for('.create_moment'))

        # save pictures to local
        pic_names = {}
        pic_index = 0
        for picture in moment_pictures:
            print(picture, '\n')
            pic_index += 1
            pic_names[str(pic_index)] = saver('moment', picture, current_user)

        print("Before DUMPS:", pic_names)
        pic_names_str = json.dumps(pic_names)
        print("STRING:", pic_names_str)

        # save text and pics to the database
        moment = Moment(body=moment_text,
                        pictures=pic_names_str,
                        from_group=current_user.my_group)
        db.session.add(moment)
        db.session.commit()

        return redirect(url_for('.moments'))

    return render_template('create_moment.html')

@moment.route('/moments')
@login_required
def moments():
    moments = Moment.query.order_by(Moment.timestamp.desc())
    return render_template('moments.html', moments=moments)

@moment.route('/<int:id>/<hex>/delete')
@login_required
def delete_moment(id, hex):
    moment = Moment.query.get_or_404(id)

    if moment.from_group.owner[0].id != current_user.id:
        abort(403)

    db.session.delete(moment)
    db.session.commit()

    flash('Your Moment has been deleted!')
    return redirect(request.referrer)
