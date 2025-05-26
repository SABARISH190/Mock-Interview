from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectField
from wtforms.fields.datetime import DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models.user import User
from flask_login import current_user
from datetime import datetime, timedelta

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                         validators=[DataRequired(), 
                                    Length(min=4, max=20, message='Username must be between 4 and 20 characters')])
    email = StringField('Email', 
                       validators=[DataRequired(), 
                                  Email(message='Please enter a valid email address')])
    phone = StringField('Phone Number', 
                       validators=[DataRequired(), 
                                  Length(min=10, max=15, message='Please enter a valid phone number')])
    first_name = StringField('First Name', 
                           validators=[DataRequired(), 
                                      Length(min=2, max=50, message='First name must be between 2 and 50 characters')])
    last_name = StringField('Last Name', 
                          validators=[DataRequired(), 
                                     Length(min=2, max=50, message='Last name must be between 2 and 50 characters')])
    password = PasswordField('Password', 
                           validators=[DataRequired(), 
                                      Length(min=8, message='Password must be at least 8 characters long')])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), 
                                              EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')
    
    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user:
            raise ValidationError('That phone number is already registered. Please use a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', 
                       validators=[DataRequired(), 
                                  Email(message='Please enter a valid email address')])
    password = PasswordField('Password', 
                           validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RequestResetForm(FlaskForm):
    email = StringField('Email', 
                       validators=[DataRequired(), 
                                  Email(message='Please enter a valid email address')])
    submit = SubmitField('Request Password Reset')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', 
                           validators=[DataRequired(), 
                                      Length(min=8, message='Password must be at least 8 characters long')])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), 
                                              EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

class OTPVerificationForm(FlaskForm):
    otp = StringField('Verification Code', 
                     validators=[DataRequired(), 
                                Length(min=6, max=6, message='OTP must be 6 digits')])
    submit = SubmitField('Verify Account')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                         validators=[DataRequired(), 
                                    Length(min=4, max=20, message='Username must be between 4 and 20 characters')])
    email = StringField('Email',
                       validators=[DataRequired(), 
                                  Email(message='Please enter a valid email address')])
    phone = StringField('Phone Number',
                       validators=[DataRequired(), 
                                  Length(min=10, max=15, message='Please enter a valid phone number')])
    first_name = StringField('First Name',
                           validators=[DataRequired(), 
                                      Length(min=2, max=50, message='First name must be between 2 and 50 characters')])
    last_name = StringField('Last Name',
                          validators=[DataRequired(), 
                                     Length(min=2, max=50, message='Last name must be between 2 and 50 characters')])
    submit = SubmitField('Update Profile')
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered. Please use a different one.')
    
    def validate_phone(self, phone):
        if phone.data != current_user.phone:
            user = User.query.filter_by(phone=phone.data).first()
            if user:
                raise ValidationError('That phone number is already registered. Please use a different one.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', 
                                   validators=[DataRequired()])
    new_password = PasswordField('New Password', 
                               validators=[DataRequired(), 
                                          Length(min=8, message='Password must be at least 8 characters long')])
    confirm_new_password = PasswordField('Confirm New Password', 
                                       validators=[DataRequired(), 
                                                  EqualTo('new_password', message='Passwords must match')])
    submit_password = SubmitField('Change Password')

class NotificationSettingsForm(FlaskForm):
    email_notifications = BooleanField('Email Notifications')
    sms_notifications = BooleanField('SMS Notifications')
    submit_notifications = SubmitField('Save Notification Settings')

class ScheduleInterviewForm(FlaskForm):
    title = StringField('Interview Title', 
                      validators=[DataRequired(), 
                                 Length(min=3, max=100)])
    domain = SelectField('Domain', 
                        validators=[DataRequired()],
                        choices=[
                            ('Full Stack Developer', 'Full Stack Developer'),
                            ('AI Engineer', 'AI Engineer'),
                            ('Data Analyst', 'Data Analyst')
                        ])
    difficulty = SelectField('Difficulty Level', 
                           validators=[DataRequired()],
                           choices=[
                               ('easy', 'Easy'),
                               ('medium', 'Medium'),
                               ('hard', 'Hard')
                           ])
    scheduled_at = DateTimeField('Schedule Date and Time', 
                               format='%Y-%m-%dT%H:%M',
                               validators=[DataRequired()],
                               default=datetime.utcnow() + timedelta(hours=1))
    resume_id = SelectField('Upload Resume (Optional)', 
                          validators=[Optional()],
                          choices=[])  # Will be populated in the view function
    notes = TextAreaField('Additional Notes', 
                        validators=[Optional(), 
                                   Length(max=500)])
    submit = SubmitField('Schedule Interview')

class UploadResumeForm(FlaskForm):
    title = StringField('Resume Title', 
                      validators=[DataRequired(), 
                                 Length(min=3, max=100)])
    domain = SelectField('Domain', 
                        validators=[DataRequired()],
                        choices=[
                            ('Full Stack Developer', 'Full Stack Developer'),
                            ('AI Engineer', 'AI Engineer'),
                            ('Data Analyst', 'Data Analyst')
                        ])
    resume_file = FileField('Resume File', 
                          validators=[
                              FileRequired(),
                              FileAllowed(['pdf', 'doc', 'docx', 'txt'], 'Only PDF, DOC, DOCX, and TXT files are allowed')
                          ])
    submit = SubmitField('Upload Resume')
