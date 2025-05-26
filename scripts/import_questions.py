import os
import re
import sys
import logging
from datetime import datetime
from pathlib import Path

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

def parse_qa_file(file_path, domain, question_type):
    """Parse a Q&A text file and return a list of question dictionaries."""
    questions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into question blocks (Q1, Q2, etc.)
        question_blocks = re.split(r'(?=Q\d+:)', content)
        
        for block in question_blocks:
            block = block.strip()
            if not block:
                continue
                
            # Extract question number and text
            q_match = re.match(r'Q\d+:(.*?)A\d+:(.*?)(?=Q\d+:|\Z)', block, re.DOTALL)
            if not q_match:
                continue
                
            question_text = q_match.group(1).strip()
            answer_text = q_match.group(2).strip()
            
            # Determine difficulty based on question number (simple heuristic)
            q_num = int(re.search(r'Q(\d+)', block).group(1))
            if q_num <= 30:
                difficulty = 'easy'
            elif q_num <= 70:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
            
            questions.append({
                'domain': domain,
                'question_text': question_text,
                'answer_text': answer_text,
                'question_type': question_type,
                'difficulty': difficulty,
                'category': domain
            })
            
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {str(e)}", exc_info=True)
    
    return questions

def import_questions():
    """Import questions from text files into the database."""
    # Define the files and their corresponding domains and types
    files = [
        ('FullStackDeveloper_QA.txt', 'FullStackDeveloper', 'technical'),
        ('AIEngineer_QA.txt', 'AIEngineer', 'technical'),
        ('DataAnalyst_QA.txt', 'DataAnalyst', 'technical'),
        ('BehavioralAnalysis_QA.txt', 'Behavioral', 'behavioral')
    ]
    
    total_added = 0
    
    # Create app and context
    app = create_app()
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            for filename, domain, q_type in files:
                file_path = os.path.join(os.path.dirname(__file__), '..', filename)
                
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                logger.info(f"Processing {domain} questions from {filename}...")
                questions = parse_qa_file(file_path, domain, q_type)
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
                                
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error adding question: {str(e)}")
                        continue
                
                # Final commit for remaining questions
                db.session.commit()
                logger.info(f"Added {added_count} {domain} questions to the database.")
                total_added += added_count
                
        except Exception as e:
            db.session.rollback()
            logger.critical(f"Fatal error: {str(e)}", exc_info=True)
            return False
        
    logger.info(f"\nSuccessfully added {total_added} questions to the question bank.")
    return True

if __name__ == '__main__':
    try:
        logger.info("Starting question import...")
        if import_questions():
            logger.info("Question import completed successfully.")
            sys.exit(0)
        else:
            logger.error("Question import failed.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)
