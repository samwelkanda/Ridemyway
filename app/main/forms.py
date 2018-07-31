from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import User

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    car_details = TextAreaField('Car details', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class RideForm(FlaskForm):
    start = StringField('Start', validators=[DataRequired()])
    destination = StringField('Destination', validators=[DataRequired()])
    time = StringField('Time', validators=[DataRequired()])
    seats = IntegerField('Seats', validators=[DataRequired()])
    cost = IntegerField('Cost', validators=[DataRequired()])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    q = StringField(('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)