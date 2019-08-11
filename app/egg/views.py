'''
@Description: Easter Egg
@Author: Tianyi Lu
@Date: 2019-08-10 10:31:33
@LastEditors: Tianyi Lu
@LastEditTime: 2019-08-10 12:45:24
'''
from flask import render_template, flash
from . import egg
from .. import db
from .forms import KeyTwoForm
from flask_login import current_user, login_required

# Key two
@egg.route('/53034e497ab12775af2b8366a5e70610', methods=['GET', 'POST'])
@login_required
def key_two():
    current_user.egg = 1
    db.session.commit()
    form = KeyTwoForm()
    passed = False
    if form.validate_on_submit():
        if form.plaintext.data == 'Hello':
            current_user.egg = 2
            db.session.commit()
            flash('Pass!', 'success')
            passed = True
        return render_template('egg/key_two.html', form=form, passed=passed)
    return render_template('egg/key_two.html', form=form, passed=passed)

    