from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.models.question_bank import QuestionBank
from app.forms.question_forms import ImportQuestionsForm
from app import db

admin_questions = Blueprint('admin_questions', __name__)

@admin_questions.route('/')
@login_required
def question_list():
    """List all questions in the question bank"""
    if not current_user.is_admin:
        abort(403)
    
    # Get filter parameters
    domain = request.args.get('domain')
    question_type = request.args.get('type')
    search = request.args.get('search')
    
    # Start with base query
    query = QuestionBank.query
    
    # Apply filters
    if domain:
        query = query.filter_by(domain=domain)
    if question_type:
        query = query.filter_by(question_type=question_type)
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                QuestionBank.question_text.ilike(search_term),
                QuestionBank.answer_text.ilike(search_term)
            )
        )
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get paginated results
    questions = query.order_by(QuestionBank.domain, QuestionBank.question_type).paginate(page=page, per_page=per_page)
    
    # Get unique domains and question types for filters
    domains = db.session.query(QuestionBank.domain).distinct().all()
    question_types = db.session.query(QuestionBank.question_type).distinct().all()
    
    return render_template('admin/questions/list.html',
                         questions=questions,
                         domains=[d[0] for d in domains],
                         question_types=[t[0] for t in question_types],
                         current_domain=domain,
                         current_type=question_type,
                         search=search)

@admin_questions.route('/add', methods=['GET', 'POST'])
@login_required
def add_question():
    """Add a new question to the question bank"""
    if not current_user.is_admin:
        abort(403)
    
    if request.method == 'POST':
        # Get form data
        domain = request.form.get('domain')
        question_text = request.form.get('question_text')
        answer_text = request.form.get('answer_text')
        question_type = request.form.get('question_type')
        difficulty = request.form.get('difficulty')
        category = request.form.get('category')
        
        # Validate required fields
        if not all([domain, question_text, answer_text, question_type]):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)
        
        try:
            # Create new question
            question = QuestionBank(
                domain=domain,
                question_text=question_text,
                answer_text=answer_text,
                question_type=question_type,
                difficulty=difficulty or None,
                category=category or None
            )
            
            db.session.add(question)
            db.session.commit()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('admin_questions.question_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding question: {str(e)}', 'danger')
            return redirect(request.url)
    
    # For GET request, show the form
    domains = db.session.query(QuestionBank.domain).distinct().all()
    return render_template('admin/questions/form.html', 
                         title='Add Question',
                         domains=[d[0] for d in domains],
                         question=None)

@admin_questions.route('/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit an existing question"""
    if not current_user.is_admin:
        abort(403)
    
    question = QuestionBank.query.get_or_404(question_id)
    
    if request.method == 'POST':
        # Update question with form data
        question.domain = request.form.get('domain', question.domain)
        question.question_text = request.form.get('question_text', question.question_text)
        question.answer_text = request.form.get('answer_text', question.answer_text)
        question.question_type = request.form.get('question_type', question.question_type)
        question.difficulty = request.form.get('difficulty', question.difficulty)
        question.category = request.form.get('category', question.category)
        
        try:
            db.session.commit()
            flash('Question updated successfully!', 'success')
            return redirect(url_for('admin_questions.question_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating question: {str(e)}', 'danger')
    
    # For GET request, show the form with current data
    domains = db.session.query(QuestionBank.domain).distinct().all()
    return render_template('admin/questions/form.html', 
                         title='Edit Question',
                         domains=[d[0] for d in domains],
                         question=question)

@admin_questions.route('/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question from the question bank"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    question = QuestionBank.query.get_or_404(question_id)
    
    try:
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Question deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_questions.route('/import', methods=['GET', 'POST'])
@login_required
def import_questions():
    """Import questions from a file"""
    form = ImportQuestionsForm()
    
    # Get unique domains for the domain dropdown
    domains = [d[0] for d in db.session.query(QuestionBank.domain).distinct().all()]
    form.domain.choices = [(d, d) for d in domains] + [('_add_new', '+ Add New Domain')]
    
    if form.validate_on_submit():
        domain = form.domain.data
        question_type = form.question_type.data
        
        # Handle new domain
        if domain == '_add_new':
            new_domain = request.form.get('new_domain', '').strip()
            if new_domain:
                domain = new_domain
            else:
                flash('Please enter a domain name', 'danger')
                return redirect(url_for('admin_questions.import_questions'))
        
        file = form.file.data
        if file:
            try:
                content = file.read().decode('utf-8')
                questions = parse_questions_file(content, domain, question_type)
                
                # Add questions to database
                for q in questions:
                    question = QuestionBank(
                        question_text=q['question'],
                        answer_text=q['answer'],
                        domain=domain,
                        question_type=question_type,
                        difficulty=q.get('difficulty', 'medium')
                    )
                    db.session.add(question)
                
                db.session.commit()
                flash(f'Successfully imported {len(questions)} questions', 'success')
                return redirect(url_for('admin_questions.question_list'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing questions: {str(e)}', 'danger')
    
    # For GET request or form validation errors, show the import form
    return render_template('admin/questions/import.html', 
                         form=form, 
                         domains=domains,
                         recent_imports=[])

def parse_questions_file(content, domain, question_type):
    """Parse a text file with questions and answers"""
    questions = []
    current_q = None
    current_a = None
    is_question = True
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Q:') or line.startswith('Q '):
            # Save previous question if exists
            if current_q is not None and current_a is not None:
                questions.append({
                    'domain': domain,
                    'question_text': current_q,
                    'answer_text': current_a,
                    'question_type': question_type,
                    'difficulty': 'medium'
                })
            
            # Start new question
            current_q = line[2:].strip()
            current_a = ''
            is_question = True
            
        elif line.startswith('A:') or line.startswith('A '):
            current_a = line[2:].strip()
            is_question = False
            
        else:
            # Continue current question or answer
            if is_question:
                current_q = f"{current_q} {line}".strip()
            else:
                current_a = f"{current_a} {line}".strip()
    
    # Add the last question
    if current_q is not None and current_a is not None:
        questions.append({
            'domain': domain,
            'question_text': current_q,
            'answer_text': current_a,
            'question_type': question_type,
            'difficulty': 'medium'
        })
    
    return questions
