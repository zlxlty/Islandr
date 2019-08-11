'''
@Description: Easter egg
@Author: Tianyi Lu
@Date: 2019-08-10 10:37:23
@LastEditors: Tianyi Lu
@LastEditTime: 2019-08-10 10:40:33
'''
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class KeyTwoForm(FlaskForm):
    plaintext = StringField('Plaintext', validators=[DataRequired()])
    submit = SubmitField('Submit')