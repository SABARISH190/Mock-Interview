from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.user import User
from app.routes.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, OTPVerificationForm
from app.services.email import send_verification_email, send_reset_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os
from datetime import datetime, timedelta
import random
import string

auth = Blueprint('auth', __name__)

def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered. Please use a different email or login.', 'danger')
            return redirect(url_for('auth.login'))
            
        # Create new user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            is_verified=False
        )
        
        # Generate OTP
        otp = generate_otp()
        user.otp = otp
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email with OTP
        try:
            send_verification_email(user)
            flash('A verification OTP has been sent to your email. Please verify your account.', 'info')
            return redirect(url_for('auth.verify_otp', email=user.email))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error sending verification email: {str(e)}')
            flash('Failed to send verification email. Please try again later.', 'danger')
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/verify-otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for('main.dashboard'))
        
    user = User.query.filter_by(email=email).first_or_404()
    
    # Check if OTP is expired
    if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
        flash('OTP has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.resend_otp', email=email))
    
    form = OTPVerificationForm()
    
    if form.validate_on_submit():
        if form.otp.data == user.otp:
            user.is_verified = True
            user.otp = None
            user.otp_expires_at = None
            db.session.commit()
            login_user(user)
            flash('Your account has been verified and you are now logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('auth/verify_otp.html', title='Verify Email', form=form, email=email)

@auth.route('/resend-otp/<email>', methods=['GET'])
def resend_otp(email):
    user = User.query.filter_by(email=email).first_or_404()
    
    # Generate new OTP
    otp = generate_otp()
    user.otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    # Resend verification email
    try:
        send_verification_email(user)
        flash('A new verification OTP has been sent to your email.', 'info')
    except Exception as e:
        current_app.logger.error(f'Error resending verification email: {str(e)}')
        flash('Failed to resend verification email. Please try again later.', 'danger')
    
    return redirect(url_for('auth.verify_otp', email=email))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            # Skip OTP verification for admin and demo users
            if not user.is_verified and not (user.email in ['admin@mockinterview.com', 'demo@mockinterview.com']):
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for('auth.verify_otp', email=user.email))
            
            # If user is not verified but is admin/demo, mark as verified
            if not user.is_verified:
                user.is_verified = True
                db.session.commit()
                
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('You have been logged in!', 'success')
            if next_page:
                return redirect(next_page)
            elif user.is_admin:
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_request.html', title='Reset Password', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_token.html', title='Reset Password', form=form)
