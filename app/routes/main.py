from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.interview import Interview
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.forms import ResumeUploadForm
from sqlalchemy import func, desc
from datetime import datetime as dt, timedelta
import os
import uuid

main = Blueprint('main', __name__)

@main.route('/')
def home():
    """Render the home page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html', title='AI-Powered Mock Interviews')

@main.route('/dashboard')
@login_required
def dashboard():
    """Render the user dashboard."""
    current_app.logger.info('=== RENDERING DASHBOARD ===')
    current_app.logger.info(f'Current user ID: {current_user.id}')
    
    # Get all non-cancelled interviews for this user
    all_user_interviews = Interview.query.filter(
        Interview.user_id == current_user.id,
        Interview.status != 'cancelled'
    ).all()
    current_app.logger.info(f'Found {len(all_user_interviews)} non-cancelled interviews for user {current_user.id}')
    
    # Log all non-cancelled interviews for debugging
    for i, interview in enumerate(all_user_interviews):
        current_app.logger.info(f'Interview {i+1}: ID={interview.id}, Status={interview.status}, ' 
                              f'Started={interview.started_at}, Completed={interview.completed_at}, ' 
                              f'Title={interview.title}')
    
    # Get current UTC time
    now = dt.utcnow()
    
    # Get upcoming interviews (scheduled or in progress, not cancelled)
    upcoming_interviews = Interview.query.filter(
        Interview.user_id == current_user.id,
        Interview.status.in_(['scheduled', 'in_progress']),
        Interview.status != 'cancelled',
        (Interview.started_at >= now) | (Interview.started_at.is_(None))
    ).order_by(Interview.started_at.asc()).limit(5).all()
    
    current_app.logger.info(f'Found {len(upcoming_interviews)} upcoming interviews')
    
    # Get past interviews (completed, not cancelled)
    past_interviews = Interview.query.filter(
        Interview.user_id == current_user.id,
        Interview.status == 'completed',
        Interview.status != 'cancelled'
    ).order_by(Interview.completed_at.desc()).limit(5).all()
    
    current_app.logger.info(f'Found {len(past_interviews)} past interviews')
    
    # Log the interview data for debugging
    for i, interview in enumerate(upcoming_interviews):
        current_app.logger.info(f'Upcoming interview {i+1}: ID={interview.id}, Title={interview.title}, ' 
                              f'Status={interview.status}, Started={interview.started_at}')
    
    # Get user's latest resume
    latest_resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).first()
    
    # Get statistics
    total_interviews = Interview.query.filter_by(user_id=current_user.id).count()
    completed_interviews = Interview.query.filter_by(user_id=current_user.id, status='completed').count()
    
    # Calculate average score if there are completed interviews
    avg_score = None
    if completed_interviews > 0:
        avg_score = db.session.query(func.avg(Analysis.overall_score))\
            .join(Interview, Interview.id == Analysis.interview_id)\
            .filter(Interview.user_id == current_user.id,
                   Interview.status == 'completed')\
            .scalar()
        
        # Format average score to 2 decimal places
        avg_score = round(avg_score, 2) if avg_score else None
    
    # Create upload form
    upload_form = ResumeUploadForm()
    
    # Prepare stats dictionary for the template
    stats = {
        'total_interviews': total_interviews,
        'completed_interviews': completed_interviews,
        'avg_score': avg_score
    }
    
    # If user is admin, add admin-specific stats
    if current_user.is_admin:
        from app.models.question_bank import QuestionBank
        
        # Get admin stats
        stats.update({
            'total_users': User.query.count(),
            'total_questions': QuestionBank.query.count(),
            'active_users_today': User.query.filter(
                User.last_seen >= (datetime.utcnow() - timedelta(days=1))
            ).count()
        })
        
        # Get recent users for admin
        recent_users = User.query.order_by(User.last_seen.desc()).limit(5).all()
        
        # Get recent activity (simplified for now)
        recent_activity = []
        
        return render_template('dashboard/dashboard.html',
                           title='Admin Dashboard',
                           stats=stats,
                           recent_users=recent_users,
                           recent_activity=recent_activity,
                           is_admin=True)
    else:
        return render_template('dashboard/dashboard.html',
                           title='Dashboard',
                           stats=stats,
                           upcoming_interviews=upcoming_interviews,
                           past_interviews=past_interviews,
                           latest_resume=latest_resume,
                           upload_form=upload_form,
                           is_admin=current_user.is_admin)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile."""
    from app.routes.forms import UpdateAccountForm
    
    form = UpdateAccountForm()
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        
        # Handle profile picture upload
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
    
    image_file = url_for('static', filename=f'profile_pics/{current_user.image_file}')
    return render_template('dashboard/profile.html', 
                         title='Profile',
                         form=form,
                         image_file=image_file)

def save_picture(form_picture):
    """Save uploaded profile picture."""
    import secrets
    import os
    from PIL import Image
    
    # Generate a random filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Create directory if it doesn't exist
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Resize and save the image
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    # Delete old profile picture if it's not the default
    if current_user.image_file != 'default.jpg':
        old_picture_path = os.path.join(current_app.root_path, 'static/profile_pics', current_user.image_file)
        if os.path.exists(old_picture_path):
            os.remove(old_picture_path)
    
    return picture_fn

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    from app.routes.forms import ChangePasswordForm, NotificationSettingsForm
    
    password_form = ChangePasswordForm()
    notification_form = NotificationSettingsForm()
    
    # Handle password change
    if password_form.submit_password.data and password_form.validate_on_submit():
        if current_user.verify_password(password_form.current_password.data):
            current_user.password = password_form.new_password.data
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('main.settings'))
        else:
            flash('Incorrect current password. Please try again.', 'danger')
    
    # Handle notification settings update
    if notification_form.submit_notifications.data and notification_form.validate_on_submit():
        # Update notification preferences here
        # This is a simplified example
        current_user.email_notifications = notification_form.email_notifications.data
        current_user.sms_notifications = notification_form.sms_notifications.data
        db.session.commit()
        flash('Your notification settings have been updated!', 'success')
        return redirect(url_for('main.settings'))
    
    # Set form data for notification settings
    if request.method == 'GET':
        notification_form.email_notifications.data = current_user.email_notifications
        notification_form.sms_notifications.data = current_user.sms_notifications
    
    return render_template('dashboard/settings.html',
                         title='Settings',
                         password_form=password_form,
                         notification_form=notification_form)

@main.route('/help')
def help():
    """Help and support page."""
    return render_template('help.html', title='Help & Support')

@main.route('/about')
def about():
    """About page."""
    return render_template('main/about.html', title='About Us')

@main.route('/upload_resume', methods=['POST'])
@login_required
def upload_resume():
    """Handle resume upload."""
    form = ResumeUploadForm()
    if form.validate_on_submit():
        if 'resume' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('main.dashboard'))
            
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('main.dashboard'))
            
        if file:
            try:
                # Generate a unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Create uploads directory if it doesn't exist
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes', str(current_user.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save file
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Delete any existing resume for this user
                existing_resume = Resume.query.filter_by(user_id=current_user.id).first()
                if existing_resume:
                    existing_resume.delete_file()
                    db.session.delete(existing_resume)
                
                # Save to database
                resume = Resume(
                    filename=filename,
                    stored_filename=unique_filename,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=file_ext,
                    user_id=current_user.id
                )
                db.session.add(resume)
                db.session.commit()
                
                flash('Resume uploaded successfully!', 'success')
                current_app.logger.info(f'Resume uploaded for user {current_user.id}: {filename}')
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error uploading resume: {str(e)}')
                flash('An error occurred while uploading your resume. Please try again.', 'danger')
    else:
        flash_errors(form)
    
    return redirect(url_for('main.dashboard'))

def flash_errors(form):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'danger')

@main.route('/download/resume/<int:resume_id>')
@login_required
def download_resume(resume_id):
    """Download a resume file."""
    resume = Resume.query.get_or_404(resume_id)
    
    # Check if the resume belongs to the current user or if the user is an admin
    if resume.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Check if the file exists
    if not os.path.exists(resume.file_path):
        flash('The requested file does not exist.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Send the file for download
        return send_from_directory(
            os.path.dirname(resume.file_path),
            os.path.basename(resume.file_path),
            as_attachment=True,
            download_name=resume.filename
        )
    except Exception as e:
        current_app.logger.error(f"Error downloading resume: {str(e)}")
        flash('An error occurred while downloading the file.', 'danger')
        return redirect(url_for('main.dashboard'))

@main.route('/resume/<int:resume_id>/delete', methods=['POST'])
@login_required
def delete_resume(resume_id):
    """Delete a user's resume."""
    resume = Resume.query.get_or_404(resume_id)
    
    # Check if the resume belongs to the current user or if the user is an admin
    if resume.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    try:
        # Delete the file from the filesystem
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        # Delete the database record
        db.session.delete(resume)
        db.session.commit()
        
        flash('Your resume has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting resume: {str(e)}")
        flash('An error occurred while deleting your resume. Please try again.', 'danger')
    
    return redirect(url_for('main.dashboard'))
