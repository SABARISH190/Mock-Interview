from app import create_app, db
from app.models.question_bank import QuestionBank
import os

def check_database_structure():
    """Check if the question_bank table exists and has the correct structure."""
    app = create_app()
    
    with app.app_context():
        # Check if the database file exists
        db_path = os.path.join('instance', 'mock_interview.db')
        if not os.path.exists(db_path):
            print(f"Database file not found at: {db_path}")
            return False
        
        # Check if the table exists
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tables in database:", tables)
        
        if 'question_bank' not in tables:
            print("Error: 'question_bank' table does not exist in the database.")
            return False
        
        # Check the columns in the question_bank table
        columns = [col['name'] for col in inspector.get_columns('question_bank')]
        print("Columns in question_bank table:", columns)
        
        required_columns = [
            'id', 'domain', 'question_text', 'answer_text', 
            'question_type', 'difficulty', 'category', 'created_at', 'updated_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            print(f"Error: Missing columns in question_bank table: {missing_columns}")
            return False
        
        print("Database structure is correct!")
        return True

if __name__ == "__main__":
    check_database_structure()
