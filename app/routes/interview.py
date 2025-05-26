from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session, abort
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from app.models.interview import Interview, Question, Response
from app.models.analysis import Analysis
from app.models.question_bank import QuestionBank
from app.models.resume import Resume
from app.models.question_bank import QuestionBank
from app.services.resume_parser import ResumeParser
from app.services.ai_interviewer import AIInterviewer
from app.utils.question_selector import QuestionSelector
from app import db, csrf
import os
import json
import random
import secrets
from werkzeug.utils import secure_filename
from datetime import datetime

# Initialize question selector
question_selector = QuestionSelector()

# Constants for question selection
QUESTIONS_PER_DOMAIN = {
    'technical': 5,       # 5 technical questions
    'behavioral': 3,      # 3 behavioral questions
    'situational': 2      # 2 situational questions
}

interview = Blueprint('interview', __name__)

@interview.route('/')
@login_required
def index():
    """Show list of user's non-cancelled interviews with statistics"""
    # Get all non-cancelled interviews for the current user
    interviews = Interview.query.filter(
        Interview.user_id == current_user.id,
        Interview.status != 'cancelled'
    ).order_by(Interview.created_at.desc()).all()
    
    # Get current time
    now = datetime.utcnow()
    
    # Calculate statistics
    completed_interviews = [i for i in interviews if i.status == 'completed']
    completed_count = len(completed_interviews)
    
    # Calculate average score from analysis
    if completed_count > 0:
        avg_score = db.session.query(
            db.func.avg(Analysis.overall_score)
        ).join(Interview).filter(
            Interview.user_id == current_user.id,
            Interview.status == 'completed',
            Analysis.overall_score.isnot(None)
        ).scalar() or 0
    else:
        avg_score = 0
    
    stats = {
        'upcoming_count': len([i for i in interviews if i.status == 'pending' and i.started_at is None]),
        'completed_count': completed_count,
        'avg_score': avg_score
    }
    
    # Separate interviews into upcoming and recent
    upcoming_interviews = [i for i in interviews if i.status == 'pending' and i.started_at is None]
    recent_interviews = [i for i in interviews if i not in upcoming_interviews][:5]  # Show 5 most recent
    
    return render_template('interview/index.html',
                         upcoming_interviews=upcoming_interviews,
                         recent_interviews=recent_interviews,
                         stats=stats,
                         now=now)

@interview.route('/admin/import-questions', methods=['GET', 'POST'])
@login_required
def import_questions():
    """Import questions from text files into the database"""
    # Only allow admins to access this route
    if not current_user.is_admin:
        abort(403)
    
    if request.method == 'POST':
        try:
            # Run the populate_question_bank script
            script_path = os.path.join(current_app.root_path, '..', 'scripts', 'populate_question_bank.py')
            
            # Check if the script exists
            if not os.path.exists(script_path):
                flash('Question import script not found!', 'danger')
                return redirect(url_for('interview.import_questions'))
            
            # Import the script and run the populate function
            import importlib.util
            import sys
            
            # Add the project root to the Python path
            project_root = os.path.join(current_app.root_path, '..')
            sys.path.append(project_root)
            
            # Import the module
            spec = importlib.util.spec_from_file_location("populate_question_bank", script_path)
            populate_module = importlib.util.module_from_spec(spec)
            sys.modules["populate_question_bank"] = populate_module
            spec.loader.exec_module(populate_module)
            
            # Call the populate function
            with current_app.app_context():
                populate_module.populate_question_bank()
            
            flash('Questions imported successfully!', 'success')
            return redirect(url_for('interview.import_questions'))
            
        except Exception as e:
            current_app.logger.error(f"Error importing questions: {str(e)}", exc_info=True)
            flash(f'Error importing questions: {str(e)}', 'danger')
    
    # Get question counts by domain
    question_counts = db.session.query(
        QuestionBank.domain,
        db.func.count(QuestionBank.id)
    ).group_by(QuestionBank.domain).all()
    
    return render_template('admin/import_questions.html', question_counts=question_counts)

@interview.route('/new', methods=['GET', 'POST'])
@login_required
def new_interview():
    """Create a new interview session"""
    from app.routes.forms import ScheduleInterviewForm
    
    form = ScheduleInterviewForm()
    
    # Populate resume choices
    form.resume_id.choices = [(str(resume.id), resume.filename) 
                            for resume in current_user.resumes]
    
    if form.validate_on_submit():
        domain = form.domain.data
        title = form.title.data or f"{domain} Interview"
        
        # Create new interview
        interview = Interview(
            user_id=current_user.id,
            domain=domain,
            title=title,
            difficulty=form.difficulty.data,
            scheduled_at=form.scheduled_at.data,
            notes=form.notes.data,
            status='scheduled'
        )
        
        db.session.add(interview)
        
        # Add questions to the interview
        try:
            add_questions_to_interview(interview)
            db.session.commit()
            flash('Interview scheduled successfully!', 'success')
            return redirect(url_for('interview.prepare', interview_id=interview.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating interview: {str(e)}")
            flash('Error creating interview. Please try again.', 'danger')
    
    # Get available categories from questions for the domain dropdown
    categories = db.session.query(Question.category).distinct().all()
    form.domain.choices = [(c[0], c[0]) for c in categories if c[0]]
    
    # If no categories found, provide some default options
    if not form.domain.choices:
        form.domain.choices = [
            ('Software Development', 'Software Development'),
            ('Data Science', 'Data Science'),
            ('Product Management', 'Product Management'),
            ('UX/UI Design', 'UX/UI Design')
        ]
    
    return render_template('interview/new.html', form=form)

def add_questions_to_interview(interview):
    """
    Add random questions to an interview from the question bank.
    
    Args:
        interview: The interview object to add questions to
        
    Returns:
        bool: True if questions were added successfully, False otherwise
    """
    try:
        current_app.logger.info(f"Starting to add questions for interview {interview.id} in domain: {interview.domain}")
        
        # Map domain from interview to match question bank format
        domain_mapping = {
            'Full Stack Developer': 'FullStackDeveloper',
            'AI Engineer': 'AIEngineer',
            'Data Analyst': 'DataAnalyst',
            'Behavioral': 'Behavioral'
        }
        
        # Get the mapped domain or use the original if not found
        question_domain = domain_mapping.get(interview.domain, interview.domain)
        
        # Define question types and counts based on requirements
        # 25-35 domain-specific questions (technical + situational)
        # 15 behavioral questions
        questions_per_type = {
            'technical': random.randint(15, 25),  # 15-25 technical questions
            'situational': 10,                   # 10 situational questions
            'behavioral': 15                     # 15 behavioral questions
        }
        
        # Log available domains and question types for debugging
        available_domains = [d[0] for d in db.session.query(QuestionBank.domain).distinct().all()]
        available_types = [t[0] for t in db.session.query(QuestionBank.question_type).distinct().all()]
        
        current_app.logger.info(f"Available domains in question bank: {', '.join(available_domains) if available_domains else 'None'}")
        current_app.logger.info(f"Available question types in question bank: {', '.join(available_types) if available_types else 'None'}")
        
        questions_added = 0
        
        # Get questions based on domain and type
        all_questions = []
        
        try:
            for q_type, count in questions_per_type.items():
                current_app.logger.info(f"Looking for {count} {q_type} questions for domain: {question_domain}")
                
                # For behavioral questions, we want to get them regardless of domain
                if q_type == 'behavioral':
                    query = QuestionBank.query.filter(
                        QuestionBank.question_type == 'behavioral'
                    )
                else:
                    # For technical and situational questions, use the interview domain
                    query = QuestionBank.query.filter(
                        QuestionBank.domain == question_domain,
                        QuestionBank.question_type == q_type
                    )
                
                # Get the actual count of available questions
                available_count = query.count()
                
                if available_count == 0:
                    current_app.logger.warning(
                        f"No {q_type} questions found for domain: {question_domain}. "
                        f"Available domains: {', '.join(available_domains) if available_domains else 'None'}. "
                        f"Available types: {', '.join(available_types) if available_types else 'None'}"
                    )
                    continue
                    
                # If we don't have enough questions, log a warning and use what we have
                questions_to_take = min(count, available_count)
                if available_count < count:
                    current_app.logger.warning(
                        f"Only {available_count} {q_type} questions available (requested {count}) "
                        f"for domain: {question_domain}. Using all available questions."
                    )
                
                # Get random questions of this type
                questions = query.order_by(func.random()).limit(questions_to_take).all()
                all_questions.extend(questions)
                current_app.logger.info(f"Found {len(questions)} {q_type} questions for domain: {question_domain}")
            
            # Add all collected questions to the interview
            for q in all_questions:
                try:
                    question = Question(
                        interview_id=interview.id,
                        question_text=q.question_text,
                        question_type=q.question_type,
                        difficulty=q.difficulty or 'medium',
                        category=q.category or question_domain,  # Use domain as category if not specified
                        created_at=datetime.utcnow()
                    )
                    db.session.add(question)
                    questions_added += 1
                    current_app.logger.debug(f"Added question: {q.question_text[:50]}...")
                except Exception as q_error:
                    current_app.logger.error(f"Error adding question: {str(q_error)}", exc_info=True)
                    db.session.rollback()
                    continue  # Continue with next question
            
            db.session.commit()
                    
        except Exception as e:
            current_app.logger.error(f"Error in question selection: {str(e)}", exc_info=True)
            db.session.rollback()
        
        if questions_added == 0:
            current_app.logger.error(f"No questions were added to interview {interview.id}. Check if the question bank is properly populated.")
            return False
            
        current_app.logger.info(f"Successfully added {questions_added} questions to interview {interview.id}")
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding questions to interview {interview.id}: {str(e)}", exc_info=True)
        return False

@interview.route('/<int:interview_id>', methods=['GET'])
@login_required
def interview_page(interview_id):
    """Interview page - redirects to prepare or start"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user owns this interview
    if interview.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    # Redirect to preparation page first
    return redirect(url_for('interview.prepare', interview_id=interview_id))

@interview.route('/<int:interview_id>/start', methods=['GET', 'POST'])
@login_required
def start_interview(interview_id):
    """Start or resume an interview session"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user owns this interview
    if interview.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Get current question (first unanswered question in order)
    current_question = Question.query.outerjoin(Response).filter(
        Question.interview_id == interview_id,
        Response.id.is_(None)
    ).order_by(Question.id).first()
    
    # If no unanswered questions, check if there are any questions at all
    if not current_question:
        questions = Question.query.filter_by(interview_id=interview_id).count()
        if questions == 0:
            # No questions at all, add questions from question bank
            try:
                add_questions_to_interview(interview)
                db.session.commit()
                return redirect(url_for('interview.start', interview_id=interview_id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error adding questions to interview: {str(e)}")
                flash('Error preparing interview questions. Please try again.', 'danger')
                return redirect(url_for('interview.index'))
        else:
            # All questions answered, mark as complete
            interview.status = 'completed'
            interview.completed_at = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('interview.view', interview_id=interview_id))
    
    # Get all questions for progress tracking
    questions = Question.query.filter_by(interview_id=interview_id).order_by(Question.id).all()
    
    # Calculate progress
    total_questions = len(questions)
    answered = sum(1 for q in questions if q.responses)
    progress = int((answered / total_questions) * 100) if total_questions > 0 else 0
    
    # Get question types for UI
    question_types = {}
    for q in questions:
        if q.question_type not in question_types:
            question_types[q.question_type] = 0
        question_types[q.question_type] += 1
    
    # Convert questions to a JSON-serializable format
    questions_json = [{
        'id': q.id,
        'question_text': q.question_text,
        'question_type': q.question_type,
        'responses': [r.answer_text for r in q.responses] if q.responses else []
    } for q in questions]
    
    return render_template('interview/session.html',
                         interview=interview,
                         questions=questions,
                         questions_json=questions_json,
                         question_types=question_types,
                         progress=progress)

@interview.route('/<int:interview_id>/question', methods=['POST'])
@login_required
def add_question(interview_id):
    """Add a question to the interview"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user owns this interview
    if interview.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    question_text = data.get('question')
    if not question_text:
        return jsonify({'error': 'Question text is required'}), 400
    
    # Create new question with current timestamp
    new_question = Question(
        question_text=question_text,
        interview_id=interview_id,
        question_type='technical',  # Default type
        created_at=datetime.utcnow()
    )
    
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({
        'id': new_question.id,
        'question_text': new_question.question_text,
        'created_at': new_question.created_at.isoformat()
    }), 201

@interview.route('/<int:interview_id>/add-sample-questions', methods=['POST'])
@login_required
def add_sample_questions(interview_id):
    """Add sample questions to an interview (for testing)"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user owns this interview
    if interview.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    sample_questions = [
        "Can you tell me about yourself?",
        "What are your greatest strengths?",
        "What is your greatest weakness?",
        "Why do you want to work here?",
        "Where do you see yourself in 5 years?"
    ]
    
    added_questions = []
    for q in sample_questions:
        question = Question(
            question_text=q,
            interview_id=interview_id,
            question_type='general',
            created_at=datetime.utcnow()
        )
        db.session.add(question)
        added_questions.append({
            'id': question.id,
            'question_text': question.question_text
        })
    
    db.session.commit()
    
    return jsonify({
        'message': f'Added {len(added_questions)} questions',
        'questions': added_questions
    }), 201

@interview.route('/<int:interview_id>/question/<int:question_id>/response', methods=['POST'])
@login_required
@csrf.exempt  # Temporarily disable CSRF for this endpoint to test
# @csrf.required  # Uncomment this line after testing if you want to enable CSRF
def save_response(interview_id, question_id):
    """Save user's response to a question"""
    current_app.logger.info(f'=== START save_response ===')
    current_app.logger.info(f'Attempting to save response for interview {interview_id}, question {question_id}')
    current_app.logger.info(f'Request data: {request.data}')
    current_app.logger.info(f'Request JSON: {request.get_json(silent=True)}')
    current_app.logger.info(f'Current user ID: {current_user.id if current_user.is_authenticated else "Not authenticated"}')
    
    try:
        # Get interview and question with error handling
        try:
            interview = Interview.query.get_or_404(interview_id)
            question = Question.query.get_or_404(question_id)
        except Exception as e:
            current_app.logger.error(f'Database query failed: {str(e)}')
            return jsonify({'error': 'Failed to load interview or question data'}), 404
        
        current_app.logger.info(f'Interview user: {interview.user_id}, Current user: {current_user.id}')
        current_app.logger.info(f'Question interview_id: {question.interview_id}, Requested interview_id: {interview_id}')
        
        # Check if user owns this interview and question belongs to interview
        if interview.user_id != current_user.id:
            current_app.logger.warning(f'Access denied: User {current_user.id} does not own interview {interview_id}')
            return jsonify({'error': 'Access denied'}), 403
            
        if question.interview_id != interview_id:
            current_app.logger.warning(f'Question {question_id} does not belong to interview {interview_id}')
            return jsonify({'error': 'Invalid question for this interview'}), 400
        
        # Get and validate request data
        try:
            data = request.get_json()
            if not data:
                current_app.logger.error('No JSON data provided in request')
                return jsonify({'error': 'No data provided'}), 400
                
            response_text = data.get('response')
            if not response_text:
                current_app.logger.error('No response text provided')
                return jsonify({'error': 'Response text is required'}), 400
                
        except Exception as e:
            current_app.logger.error(f'Error parsing request data: {str(e)}')
            return jsonify({'error': 'Invalid request data'}), 400
        
        try:
            current_app.logger.info('Checking for existing response...')
            # Check if a response already exists
            existing_response = Response.query.filter_by(question_id=question_id).first()
            
            if existing_response:
                current_app.logger.info('Found existing response, updating...')
                existing_response.answer_text = response_text
                existing_response.updated_at = datetime.utcnow()
                current_app.logger.info(f'Updated response: {existing_response}')
            else:
                current_app.logger.info('No existing response, creating new one...')
                new_response = Response(
                    answer_text=response_text,
                    question_id=question_id,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_response)
                current_app.logger.info(f'Created new response: {new_response}')
            
            current_app.logger.info('Committing to database...')
            db.session.commit()
            current_app.logger.info('Database commit successful')
            
            response_data = {
                'success': True, 
                'message': 'Response saved successfully',
                'question_id': question_id,
                'interview_id': interview_id
            }
            current_app.logger.info(f'Returning success response: {response_data}')
            return jsonify(response_data), 200
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Database error: {str(e)}', exc_info=True)
            return jsonify({'error': f'Database error: {str(e)}'}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@interview.route('/<int:interview_id>/complete', methods=['POST'])
@login_required
@csrf.exempt  # We're handling CSRF manually
@login_required
def complete_interview(interview_id):
    """Mark an interview as complete"""
    try:
        # Verify CSRF token from headers
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token or csrf_token != request.cookies.get('X-CSRFToken'):
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
            
        interview = Interview.query.get_or_404(interview_id)
        
        # Check if user owns this interview
        if interview.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if interview is already completed
        if interview.status == 'completed':
            return jsonify({
                'success': True,
                'redirect_url': url_for('interview.view', interview_id=interview_id, _external=False)
            })
        
        interview.status = 'completed'
        interview.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Return success response with redirect URL
        return jsonify({
            'success': True,
            'redirect_url': url_for('interview.view', interview_id=interview_id, _external=False)
        })
    except Exception as e:
        current_app.logger.error(f'Error completing interview: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@interview.route('/<int:interview_id>/prepare')
@login_required
def prepare(interview_id):
    """Prepare for an interview"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user owns this interview
    if interview.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Get question count for this interview
    question_count = Question.query.filter_by(interview_id=interview_id).count()
    
    # Prepare some tips based on the interview domain
    tips = [
        f"Review common {interview.domain} interview questions.",
        "Practice explaining your thought process clearly.",
        "Prepare examples from your experience that demonstrate your skills.",
        "Research the company and role you're interviewing for.",
        "Prepare questions to ask the interviewer about the role and company."
    ]
    
    return render_template('interview/prepare.html',
                         interview=interview,
                         question_count=question_count,
                         tips=tips,
                         now=datetime.utcnow())

@interview.route('/<int:interview_id>/view')
@login_required
def view(interview_id):
    """View completed interview with responses"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user owns this interview
    if interview.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('interview.index'))
    
    questions = Question.query.filter_by(interview_id=interview_id).order_by(Question.created_at.asc()).all()
    
    # Get analysis if it exists
    analysis = Analysis.query.filter_by(interview_id=interview_id).first()
    
    return render_template('interview/view.html', 
                         interview=interview, 
                         questions=questions,
                         analysis=analysis)

@interview.route('/<int:interview_id>/cancel', methods=['POST'])
@login_required
def cancel_interview(interview_id):
    """Cancel a scheduled interview"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Check if user is the owner or admin
    if interview.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    try:
        # Update interview status
        interview.status = 'cancelled'
        interview.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Interview has been cancelled successfully.', 'success')
        return jsonify({'success': True, 'message': 'Interview cancelled successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error cancelling interview: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to cancel interview'}), 500


@interview.route('/upload-resume', methods=['POST'])
@login_required
def upload_resume():
    """Handle resume upload and processing"""
    current_app.logger.info("Starting resume upload process")
    
    try:
        if 'resume' not in request.files:
            current_app.logger.warning("No file part in request")
            flash('No file part', 'danger')
            return redirect(url_for('main.dashboard'))
            
        file = request.files['resume']
        domain = request.form.get('domain', 'Full Stack Developer')  # Default domain
        current_app.logger.info(f"Processing resume for domain: {domain}")
        
        if file.filename == '':
            current_app.logger.warning("No file selected")
            flash('No file selected', 'danger')
            return redirect(url_for('main.dashboard'))
            
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
        file_ext = file.filename.lower().rsplit('.', 1)[1] if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            current_app.logger.warning(f"Invalid file extension: {file_ext}")
            flash('File type not allowed. Please upload a PDF, DOC, DOCX, or TXT file.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Read file content
        try:
            file_content = file.read()
            current_app.logger.info(f"Read {len(file_content)} bytes from uploaded file")
            
            # Try to decode if it's text (for txt files)
            text_content = None
            if file_ext == 'txt':
                try:
                    text_content = file_content.decode('utf-8')
                    current_app.logger.debug(f"Decoded text content (first 200 chars): {text_content[:200]}")
                except UnicodeDecodeError as e:
                    current_app.logger.error(f"Failed to decode text content: {str(e)}")
                    flash('Error reading text content from file', 'danger')
                    return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            current_app.logger.error(f"Error reading file: {str(e)}", exc_info=True)
            flash('Error reading uploaded file', 'danger')
            return redirect(url_for('main.dashboard'))
                
        # Generate a secure filename with a random prefix to avoid collisions
        random_hex = secrets.token_hex(8)
        filename = f"{random_hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the file
        try:
            with open(filepath, 'wb') as f:
                f.write(file_content)
            current_app.logger.info(f"Saved file to {filepath}")
            
            # Create resume record
            resume = Resume(
                user_id=current_user.id,
                domain=domain,
                file_path=filepath,
                file_name=filename,
                file_type=file_ext,
                file_size=len(file_content),
                content=text_content,  # Store text content if available
                uploaded_at=datetime.utcnow()
            )
            
            db.session.add(resume)
            db.session.commit()
            current_app.logger.info(f"Successfully created resume record with ID: {resume.id}")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during file save or database operation: {str(e)}", exc_info=True)
            flash('Error processing your resume. Please try again.', 'danger')
            
            # Clean up the uploaded file if something went wrong
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as cleanup_error:
                current_app.logger.error(f"Error cleaning up file {filepath}: {str(cleanup_error)}")
                
            return redirect(url_for('main.dashboard'))
        
        # If we couldn't extract text earlier, try to parse it now
        if not text_content or len(text_content.strip()) < 50:  # If text is too short, try parsing
            try:
                current_app.logger.info("Attempting to parse resume file")
                from app.services.resume_parser import parse_resume
                parsed_data = parse_resume(filepath)
                if parsed_data and 'raw_text' in parsed_data:
                    text_content = parsed_data['raw_text']
                    resume.content = parsed_data['raw_text']
                    resume.is_parsed = True
                    resume.parsed_data = parsed_data
                    db.session.commit()
                    current_app.logger.info("Successfully parsed resume content")
                else:
                    current_app.logger.warning("No text content found in parsed resume")
                    
            except Exception as e:
                current_app.logger.error(f"Error parsing resume: {str(e)}", exc_info=True)
                flash('Error parsing resume content. Some features may be limited.', 'warning')
        
        # If we have text content, analyze it for skills and experience
        if text_content and len(text_content.strip()) > 50:
            try:
                current_app.logger.info("Starting resume analysis...")
                from app.services.resume_parser import ResumeParser
                parser = ResumeParser()
                
                # Log the first 200 chars of the text content for debugging
                current_app.logger.debug(f"Resume text sample: {text_content[:200]}...")
                
                # Validate domain is in skills database
                available_domains = list(parser.skills_by_domain.keys())
                if not available_domains:
                    raise ValueError("No skill domains are configured in the system")
                    
                # If domain not in available domains, use the first available one
                if domain not in available_domains:
                    original_domain = domain
                    domain = available_domains[0]
                    current_app.logger.warning(
                        f"Domain '{original_domain}' not found. "
                        f"Using default domain: {domain}"
                    )
                
                current_app.logger.debug(f"Analyzing for domain: {domain}")
                
                # Analyze skills
                skills_analysis = parser.analyze_skills(text_content, domain)
                current_app.logger.debug(f"Skills analysis completed: {bool(skills_analysis)}")
                
                # Extract experience
                experience = parser.extract_experience(text_content)
                current_app.logger.debug(f"Experience extracted: {len(experience)} entries")
                
                # Combine results
                resume_analysis = {
                    'skills_analysis': skills_analysis,
                    'experience': experience,
                    'domain': domain
                }
                
                if resume_analysis:
                    resume.parsed_data = resume_analysis
                    db.session.commit()
                    current_app.logger.info("Resume analysis completed successfully")
                    
            except ImportError as e:
                current_app.logger.error(f"Import error in resume analysis: {str(e)}", exc_info=True)
                flash('Error: Required dependencies for resume analysis are missing', 'warning')
            except Exception as e:
                current_app.logger.error(f"Error analyzing resume: {str(e)}", exc_info=True)
                flash('Error analyzing resume content. Some features may be limited.', 'warning')
        
        flash('Resume uploaded and analyzed successfully!', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading resume: {str(e)}")
        flash('An error occurred while uploading your resume. Please try again.', 'danger')
        return redirect(url_for('main.dashboard'))
