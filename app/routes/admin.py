from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.interview import Interview, Question
from app.models.resume import Resume
from app.models.analysis import Analysis
from app.models.question_bank import QuestionBank
from app.utils.decorators import admin_required
from sqlalchemy import func, desc, asc, or_
from datetime import datetime, timedelta
import json
import os

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Import and register the question management blueprint
from app.routes import admin_questions
admin.register_blueprint(admin_questions.admin_questions, url_prefix='/questions')

# Test route to verify URL prefix
@admin.route('/test-route')
def test_route():
    return "TEST: Admin route is working!"


@admin.route('/test-dashboard')
@login_required
@admin_required
def test_dashboard():
    """Test admin dashboard template rendering."""
    return render_template('admin/test_dashboard.html')

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with overview statistics."""
    # Get basic statistics
    total_users = User.query.count()
    total_interviews = Interview.query.count()
    total_questions = QuestionBank.query.count()
    
    # Get active users today
    today = datetime.utcnow().date()
    active_users_today = User.query.filter(
        func.date(User.last_seen) == today
    ).count()
    
    # Question statistics
    # Domain statistics
    domain_stats = db.session.query(
        QuestionBank.domain,
        func.count(QuestionBank.id).label('count')
    ).group_by(QuestionBank.domain).all()
    
    # Calculate domain coverage
    all_domains = ['Data Science', 'Software Engineering', 'Product Management', 'UX/UI Design', 'Data Analysis']
    covered_domains = len(set(d[0] for d in domain_stats))
    domain_coverage = int((covered_domains / len(all_domains)) * 100) if all_domains else 0
    
    # Format domain data for the table/chart
    domain_table = [{
        'domain': domain,
        'count': count,
        'percentage': round((count / total_questions) * 100, 1) if total_questions > 0 else 0
    } for domain, count in domain_stats]
    
    # Sort domains by count (descending)
    domain_table.sort(key=lambda x: x['count'], reverse=True)
    
    # Question type statistics
    type_stats = dict(db.session.query(
        QuestionBank.question_type,
        func.count(QuestionBank.id)
    ).group_by(QuestionBank.question_type).all())
    
    # Difficulty statistics
    difficulty_stats = dict(db.session.query(
        QuestionBank.difficulty,
        func.count(QuestionBank.id)
    ).filter(
        QuestionBank.difficulty.isnot(None)
    ).group_by(QuestionBank.difficulty).all())
    
    # Get recent users (last 5)
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent interviews (last 5) with usernames
    recent_interviews = db.session.query(
        Interview,
        User.username
    ).join(
        User, Interview.user_id == User.id
    ).order_by(
        Interview.created_at.desc()
    ).limit(5).all()
    
    # Get weekly interview data for the chart (last 8 weeks)
    eight_weeks_ago = datetime.utcnow() - timedelta(weeks=8)
    weekly_data = db.session.query(
        func.strftime('%Y-%W', Interview.created_at).label('week'),
        func.count(Interview.id).label('count')
    ).filter(
        Interview.created_at >= eight_weeks_ago
    ).group_by('week').order_by('week').all()
    
    # Format weekly data for the chart
    weekly_stats = [{
        'week': f"Week {i+1}",
        'count': count
    } for i, (week, count) in enumerate(weekly_data)]
    
    # Calculate completion rate
    completed_interviews = Interview.query.filter_by(status='completed').count()
    completion_rate = int((completed_interviews / total_interviews) * 100) if total_interviews > 0 else 0
    
    # Get total questions count for the stats
    total_questions_count = total_questions  # This was already calculated earlier
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_interviews=total_interviews,
                         total_questions=total_questions,
                         question_count=total_questions_count,  # Add this line
                         active_users_today=active_users_today,
                         domain_coverage=domain_coverage,
                         domain_table=domain_table,
                         domain_stats=dict(domain_stats),
                         type_stats=type_stats,
                         difficulty_stats=difficulty_stats,
                         recent_users=recent_users,
                         recent_interviews=recent_interviews,
                         weekly_data=weekly_stats,
                         completion_rate=completion_rate)

@admin.route('/users')
@login_required
@admin_required
def users():
    """Manage users."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    
    users = User.query.order_by(asc(User.username)).paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html',
                         title='User Management',
                         users=users)

@admin.route('/users/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """View user details and activity."""
    user = User.query.get_or_404(user_id)
    
    # User interviews
    interviews = Interview.query.filter_by(user_id=user.id).order_by(desc(Interview.created_at)).all()
    
    # User resumes
    resumes = Resume.query.filter_by(user_id=user.id).order_by(desc(Resume.created_at)).all()
    
    # Performance statistics
    completed_interviews = Interview.query.filter_by(user_id=user.id, status='completed').all()
    
    performance_data = []
    for interview in completed_interviews:
        analysis = Analysis.query.filter_by(interview_id=interview.id).first()
        if analysis:
            performance_data.append({
                'interview_id': interview.id,
                'domain': interview.domain,
                'date': interview.completed_at,
                'technical_score': analysis.technical_score,
                'communication_score': analysis.communication_score,
                'problem_solving_score': analysis.problem_solving_score,
                'overall_score': analysis.overall_score
            })
    
    return render_template('admin/view_user.html',
                         title=f'User: {user.username}',
                         user=user,
                         interviews=interviews,
                         resumes=resumes,
                         performance_data=performance_data)

from app.forms.user_forms import EditUserForm

@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details."""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    # Set initial values for checkboxes
    form.is_admin.data = user.is_admin
    form.is_verified.data = user.is_verified
    
    if form.validate_on_submit():
        # Update user details
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data or None
        user.last_name = form.last_name.data or None
        
        # Handle admin and verification status toggle if current user is not the same as the user being edited
        if current_user.id != user.id:
            user.is_admin = form.is_admin.data
            user.is_verified = form.is_verified.data
        
        # Handle password change if provided
        if form.new_password.data:
            user.set_password(form.new_password.data)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.user_details', user_id=user.id))
    
    return render_template('admin/edit_user.html', 
                         title=f'Edit User: {user.username}',
                         user=user,
                         form=form)

@admin.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activate or deactivate a user account."""
    user = User.query.get_or_404(user_id)
    
    # Don't allow admin to deactivate their own account
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin_status(user_id):
    """Grant or revoke admin privileges."""
    user = User.query.get_or_404(user_id)
    
    # Don't allow admin to revoke their own admin privileges
    if user.id == current_user.id:
        flash('You cannot revoke your own admin privileges.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted admin privileges' if user.is_admin else 'revoked admin privileges'
    flash(f'User {user.username} has been {status}.', 'success')
    
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user account."""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting your own account
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Get username before deletion for flash message
    username = user.username
    
    # Delete related records first to avoid foreign key constraint issues
    # This assumes you have backrefs or relationships set up in your models
    Interview.query.filter_by(user_id=user.id).delete()
    Resume.query.filter_by(user_id=user.id).delete()
    
    # Now delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/interviews')
@login_required
@admin_required
def interviews():
    """Manage non-cancelled interviews."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    
    # Get all interviews except cancelled ones
    interviews = Interview.query.filter(
        Interview.status != 'cancelled'
    ).order_by(desc(Interview.created_at)).paginate(page=page, per_page=per_page)
    
    return render_template('admin/interviews.html',
                         title='Interview Management',
                         interviews=interviews)

@admin.route('/interviews/<int:interview_id>')
@login_required
@admin_required
def interview_details(interview_id):
    """View interview details with optimized queries."""
    from flask_wtf.csrf import generate_csrf
    from sqlalchemy.orm import joinedload
    
    # Get interview with user and questions in a single query
    interview = Interview.query.options(
        joinedload(Interview.user),
        joinedload(Interview.questions).joinedload(Question.responses)
    ).get_or_404(interview_id)
    
    # Get analysis in a separate query but still optimized
    analysis = Analysis.query.filter_by(interview_id=interview_id).first()
    
    # Generate CSRF token
    csrf_token = generate_csrf()
    
    return render_template('admin/interview_details.html',
                         title=f'Interview #{interview.id}',
                         interview=interview,
                         user=interview.user,  # Already loaded
                         questions=interview.questions,  # Already loaded
                         analysis=analysis,
                         csrf_token=csrf_token)

@admin.route('/interviews/<int:interview_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_interview(interview_id):
    """Cancel an interview."""
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    from sqlalchemy.orm.exc import StaleDataError
    
    try:
        # Get CSRF token from form data
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('CSRF token is missing.', 'danger')
            return redirect(url_for('admin.interview_details', interview_id=interview_id))
        
        # Validate CSRF token
        try:
            validate_csrf(csrf_token)
        except ValidationError:
            flash('Invalid CSRF token. Please try again.', 'danger')
            return redirect(url_for('admin.interview_details', interview_id=interview_id))
        
        # Get the interview
        interview = Interview.query.get_or_404(interview_id)
        
        if interview.status == 'cancelled':
            flash('This interview has already been cancelled.', 'warning')
            return redirect(url_for('admin.interview_details', interview_id=interview.id))
        
        # Update interview status
        interview.status = 'cancelled'
        interview.completed_at = datetime.utcnow()
        
        # Commit the transaction
        db.session.commit()
        
        flash('The interview has been cancelled successfully.', 'success')
        return redirect(url_for('admin.interview_details', interview_id=interview.id))
        
    except StaleDataError as e:
        db.session.rollback()
        current_app.logger.error(f'Stale data error while cancelling interview: {str(e)}')
        flash('An error occurred while processing your request. Please try again.', 'danger')
        return redirect(url_for('admin.interview_details', interview_id=interview_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error cancelling interview: {str(e)}')
        flash('An error occurred while processing your request.', 'danger')
        return redirect(url_for('admin.interview_details', interview_id=interview_id))

@admin.route('/analytics')
@login_required
@admin_required
def analytics():
    """Advanced analytics and reporting."""
    # Filter parameters
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))
    domain = request.args.get('domain', 'all')
    
    # Convert string dates to datetime objects
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
    
    # Query base - completed interviews in date range
    query = Interview.query.filter(
        Interview.status == 'completed',
        Interview.completed_at >= start_date_obj,
        Interview.completed_at <= end_date_obj
    )
    
    # Apply domain filter if specified
    if domain != 'all':
        query = query.filter(Interview.domain == domain)
    
    # Get interviews
    interviews = query.all()
    
    # Prepare data for charts
    
    # 1. Interviews by domain
    domain_counts = {}
    for interview in interviews:
        domain_counts[interview.domain] = domain_counts.get(interview.domain, 0) + 1
    
    # 2. Average scores by domain
    domain_scores = {}
    for interview in interviews:
        analysis = Analysis.query.filter_by(interview_id=interview.id).first()
        if analysis:
            if interview.domain not in domain_scores:
                domain_scores[interview.domain] = {
                    'technical': [],
                    'communication': [],
                    'problem_solving': [],
                    'overall': []
                }
            domain_scores[interview.domain]['technical'].append(analysis.technical_score)
            domain_scores[interview.domain]['communication'].append(analysis.communication_score)
            domain_scores[interview.domain]['problem_solving'].append(analysis.problem_solving_score)
            domain_scores[interview.domain]['overall'].append(analysis.overall_score)
    
    # Calculate averages
    domain_avg_scores = {}
    for domain, scores in domain_scores.items():
        domain_avg_scores[domain] = {
            'technical': sum(scores['technical']) / len(scores['technical']) if scores['technical'] else 0,
            'communication': sum(scores['communication']) / len(scores['communication']) if scores['communication'] else 0,
            'problem_solving': sum(scores['problem_solving']) / len(scores['problem_solving']) if scores['problem_solving'] else 0,
            'overall': sum(scores['overall']) / len(scores['overall']) if scores['overall'] else 0
        }
    
    # 3. User performance over time (for users with multiple interviews)
    user_performance = {}
    for interview in interviews:
        analysis = Analysis.query.filter_by(interview_id=interview.id).first()
        if analysis:
            if interview.user_id not in user_performance:
                user_performance[interview.user_id] = []
            user_performance[interview.user_id].append({
                'date': interview.completed_at,
                'overall_score': analysis.overall_score
            })
    
    # Sort by date and get users with multiple interviews
    for user_id in list(user_performance.keys()):
        performances = user_performance[user_id]
        if len(performances) < 2:
            del user_performance[user_id]
        else:
            user_performance[user_id] = sorted(performances, key=lambda x: x['date'])
    
    # Get user details for those with multiple interviews
    users_with_multiple = {}
    for user_id in user_performance:
        user = User.query.get(user_id)
        users_with_multiple[user_id] = {
            'username': user.username,
            'name': user.get_full_name() if hasattr(user, 'get_full_name') else user.username,
            'performances': user_performance[user_id]
        }
    
    # Get all available domains for filter
    all_domains = db.session.query(Interview.domain).distinct().all()
    all_domains = [d[0] for d in all_domains]
    
    return render_template('admin/analytics.html',
                         title='Analytics',
                         start_date=start_date,
                         end_date=end_date,
                         domain=domain,
                         all_domains=all_domains,
                         domain_counts=domain_counts,
                         domain_avg_scores=domain_avg_scores,
                         users_with_multiple=users_with_multiple)
