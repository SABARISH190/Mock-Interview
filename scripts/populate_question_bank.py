import os
import re
import sys
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('question_import.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Import Flask app and models after path is set
from app import create_app, db
from app.models.question_bank import QuestionBank

# Create app and context
app = create_app()

def parse_qa_file(file_path, domain, question_type):
    """Parse a Q&A text file and return a list of (question, answer) tuples."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content into Q&A pairs
    qa_pairs = re.split(r'\n\s*\n', content.strip())
    
    questions = []
    for qa in qa_pairs:
        # Split into question and answer parts
        match = re.match(r'Q\d+:\s*(.*?)\s*A\d+:\s*(.*)', qa, re.DOTALL)
        if match:
            question = match.group(1).strip()
            answer = match.group(2).strip()
            
            # Determine difficulty based on question number (simple heuristic)
            q_num = int(re.search(r'Q(\d+)', qa).group(1))
            if q_num <= 30:
                difficulty = 'easy'
            elif q_num <= 70:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
                
            # Determine category based on domain
            category = domain
            if domain in ['FullStackDeveloper', 'AIEngineer', 'DataAnalyst']:
                question_type = 'technical'
            else:
                question_type = 'behavioral'
            
            questions.append({
                'domain': domain,
                'question_text': question,
                'answer_text': answer,
                'question_type': question_type,
                'difficulty': difficulty,
                'category': category
            })
    
    return questions

def process_qa_file(file_path, domain, question_type):
    """Process a single Q&A file and return the number of questions added."""
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return 0
    
    logger.info(f"Processing {domain} questions from {os.path.basename(file_path)}...")
    
    try:
        questions = parse_qa_file(file_path, domain, question_type)
        added_count = 0
        
        for qa in questions:
            try:
                # Check if question already exists
                exists = db.session.query(QuestionBank).filter_by(
                    question_text=qa['question_text'],
                    domain=qa['domain']
                ).first()
                
                if not exists:
                    question = QuestionBank(**qa)
                    db.session.add(question)
                    added_count += 1
                    
                    # Commit in batches of 10
                    if added_count % 10 == 0:
                        db.session.commit()
                        
            except IntegrityError:
                db.session.rollback()
                logger.warning(f"Duplicate question found: {qa['question_text'][:50]}...")
                continue
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error adding question: {str(e)}")
                continue
        
        # Final commit for remaining questions
        db.session.commit()
        logger.info(f"Added {added_count} {domain} questions to the database.")
        return added_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
        return 0

def populate_question_bank():
    """Populate the question bank from the provided text files."""
    # Define the files and their corresponding domains and types
    files = [
        ('FullStackDeveloper_QA.txt', 'FullStackDeveloper', 'technical'),
        ('AIEngineer_QA.txt', 'AIEngineer', 'technical'),
        ('DataAnalyst_QA.txt', 'DataAnalyst', 'technical'),
        ('BehavioralAnalysis_QA.txt', 'Behavioral', 'behavioral')
    ]
    
    total_added = 0
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            for filename, domain, q_type in files:
                file_path = os.path.join(os.path.dirname(__file__), '..', filename)
                added = process_qa_file(file_path, domain, q_type)
                total_added += added
            
            logger.info(f"\nSuccessfully added {total_added} questions to the question bank.")
            return total_added
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fatal error in populate_question_bank: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    logger.info("Starting question bank population...")
    
    try:
        # Create application context
        with app.app_context():
            logger.info("Creating database tables if they don't exist...")
            db.create_all()  # Create tables if they don't exist
            
            # Check if question_bank table exists
            if not db.engine.dialect.has_table(db.engine, 'question_bank'):
                logger.error("question_bank table does not exist in the database.")
                sys.exit(1)
                
            logger.info("Starting to populate question bank...")
            
            # Populate the question bank
            total_added = populate_question_bank()
            
            logger.info(f"Successfully added {total_added} questions to the question bank.")
            
    except Exception as e:
        logger.error(f"Error populating question bank: {str(e)}", exc_info=True)
        sys.exit(1)
    
    logger.info("Question bank population completed successfully.")
