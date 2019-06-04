from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, Length


class DateTimeForm(FlaskForm):
    datetime_from = DateTimeField('From', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    datetime_to = DateTimeField('To', format='%Y-%m-%d %H:%M', validators=[DataRequired()])

class EditorForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 64)])
    editor = TextAreaField('Content', id='content')
    submit = SubmitField('Submit')
