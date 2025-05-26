from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models.question_bank import QuestionBank
import os
import importlib.util
import sys

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/import-questions', methods=['GET', 'POST'])
@login_required
def import_questions():
    """Import questions from text files into the database"""
    # Only allow admins to access this route
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Run the populate_question_bank script
            script_path = os.path.join(current_app.root_path, '..', 'scripts', 'populate_question_bank.py')
            
            # Check if the script exists
            if not os.path.exists(script_path):
                flash('Question import script not found!', 'danger')
                return redirect(url_for('admin.import_questions'))
            
            # Import the script and run the populate function
            spec = importlib.util.spec_from_file_location("populate_question_bank", script_path)
            populate_module = importlib.util.module_from_spec(spec)
            sys.modules["populate_question_bank"] = populate_module
            spec.loader.exec_module(populate_module)
            
            # Call the populate function
            with current_app.app_context():
                populate_module.populate_question_bank()
            
            flash('Questions imported successfully!', 'success')
            return redirect(url_for('admin.import_questions'))
            
        except Exception as e:
            current_app.logger.error(f"Error importing questions: {str(e)}", exc_info=True)
            flash(f'Error importing questions: {str(e)}', 'danger')
    
    # Get question counts by domain
    question_counts = db.session.query(
        QuestionBank.domain,
        db.func.count(QuestionBank.id)
    ).group_by(QuestionBank.domain).all()
    
    return render_template('admin/import_questions.html', question_counts=question_counts)
