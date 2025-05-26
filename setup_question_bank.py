import os
import sys
from datetime import datetime
from pathlib import Path
import re

# Add the project root to the Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

# Import Flask app and models after path is set
from app import create_app, db
from app.models.question_bank import QuestionBank

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
                
            questions.append({
                'question_text': question,
                'answer_text': answer,
                'difficulty': difficulty,
                'domain': domain,
                'question_type': question_type,
                'category': domain  # Using domain as category for now
            })
    
    return questions

def populate_question_bank():
    """Populate the question bank from the provided text files."""
    # Map of domain to file paths
    domain_files = {
        'FullStack': 'FullStackDeveloper_QA.txt',
        'AIEngineer': 'AIEngineer_QA.txt',
        'DataAnalyst': 'DataAnalyst_QA.txt',
        'Behavioral': 'BehavioralAnalysis_QA.txt'
    }
    
    total_added = 0
    
    for domain, file_name in domain_files.items():
        file_path = os.path.join(project_root, file_name)
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue
        
        # Determine question type based on domain
        question_type = 'behavioral' if domain == 'Behavioral' else 'technical'
        
        try:
            # Parse the Q&A file
            questions = parse_qa_file(file_path, domain, question_type)
            
            # Add questions to the database
            for q_data in questions:
                question = QuestionBank(**q_data)
                db.session.add(question)
            
            db.session.commit()
            total_added += len(questions)
            print(f"Added {len(questions)} {domain} questions to the question bank.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error processing {file_path}: {str(e)}")
    
    return total_added

def init_database():
    """Initialize the database with all required tables."""
    # Ensure the instance directory exists
    instance_path = os.path.join(project_root, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Set the database URI
    db_path = os.path.join(instance_path, 'mock_interview.db')
    
    # Create the Flask application
    app = create_app()
    
    with app.app_context():
        # Drop all existing tables and create new ones
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()
        
        # Verify that all tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print("\nTables created:")
        for table in tables:
            print(f"- {table}")
        
        # Check if question_bank table exists
        if 'question_bank' in tables:
            print("\nQuestion bank table exists. Checking structure...")
            columns = [col['name'] for col in inspector.get_columns('question_bank')]
            print("Columns in question_bank table:", ", ".join(columns))
            
            # Populate the question bank
            print("\nPopulating question bank...")
            total_added = populate_question_bank()
            print(f"\nSuccessfully added {total_added} questions to the question bank!")
        else:
            print("\nError: question_bank table was not created!")
            return False
        
        print("\nDatabase initialization completed successfully!")
        return True

if __name__ == "__main__":
    print("=== Setting up Mock Interview Database ===\n")
    
    # Initialize the database
    success = init_database()
    
    if success:
        print("\nSetup completed successfully!")
    else:
        print("\nSetup failed. Please check the error messages above.")
