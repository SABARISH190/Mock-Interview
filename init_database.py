import os
from app import create_app, db
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import Interview, Question, Response
from app.models.analysis import Analysis
from app.models.question_bank import QuestionBank

def init_database():
    """Initialize the database with all required tables."""
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
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
        else:
            print("\nError: question_bank table was not created!")
            return False
        
        print("\nDatabase initialization completed successfully!")
        return True

if __name__ == "__main__":
    # Ensure the instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Delete the existing database if it exists
    db_path = os.path.join('instance', 'mock_interview.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Error removing database: {e}")
    
    # Initialize the database
    success = init_database()
    
    if success:
        print("\nYou can now run the populate_question_bank.py script to add questions to the database.")
    else:
        print("\nDatabase initialization failed. Please check the error messages above.")
