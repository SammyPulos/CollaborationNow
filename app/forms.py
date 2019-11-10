from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, IntegerField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Length, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
	username = StringField('Name', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Register')

	#Note that I must check usernames for uniqueness as they are required for the pages' url
	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Please use a different username')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('There is already an account registered to the provided email.')

class EditProfileForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
	submit = SubmitField('Submit')

	def __init__(self, original_username, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.original_username = original_username

	def validate_username(self, username):
		if username.data != self.original_username:
			user = User.query.filter_by(username=self.username.data).first()
			if user is not None:
				raise ValidationError('Please use a different username.')

class CreateListingForm(FlaskForm):
	title = TextAreaField('Title', validators=[
		DataRequired(), Length(min=1, max=64)])
	body = TextAreaField('Description', validators=[
		DataRequired(), Length(min=1, max=1024)])
	desired_size = IntegerField('Desired group size', validators=[
		DataRequired()])
	submit = SubmitField('Submit')
