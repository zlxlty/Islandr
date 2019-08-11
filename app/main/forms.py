'''
@Description: Forms for Main blueprint
@Author: Tianyi Lu
@Date: 2019-08-09 16:16:12
@LastEditors: Tianyi Lu
@LastEditTime: 2019-08-09 16:28:43
'''
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, BooleanField, TextAreaField, DateTimeField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, ValidationError
from ..models import User


class DateTimeForm(FlaskForm):
    datetime_from = DateTimeField('From', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    datetime_to = DateTimeField('To', format='%Y-%m-%d %H:%M', validators=[DataRequired()])

class EditorForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 64)])
    editor = TextAreaField('Content', id='content')
    submit = SubmitField('Submit')

def username_check(form, username):  # 'form' parameter here serves the same purpose as self.
    if username.data != current_user.username:
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken.")

class UpdateAccountForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(1, 64)])
    username = StringField("Username", validators=[DataRequired(), Length(1, 64), username_check])
    location = StringField("Hometown", validators=[DataRequired(), Length(1, 128)])
    grade = SelectField("Grade", validators=[DataRequired()], choices=[("FP", "FP"), ("DP1", "DP1"), ("DP2", "DP2"), ("Faculty", "Faculty")], default=1)
    wechat_id = StringField("Wechat", validators=[Length(1, 64)])
    skills = StringField("Skills", validators=[DataRequired(), Length(1, 128)])
    about_me = TextAreaField("About Me", validators=[DataRequired()])
    profile_pic = FileField("Update Profile Picture", validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Update Account Info')
