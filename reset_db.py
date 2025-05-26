import os
from app import create_app, db
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import Interview, Question, Response
from app.models.analysis import Analysis

def reset_database():
    print("Initializing database...")
    
    # Create the application context
    app = create_app()
    app.app_context().push()
    
    # Delete existing database file if it exists
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create all database tables
    print("Creating database tables...")
    db.create_all()
    
    print("Database reset and initialized successfully!")

if __name__ == '__main__':
    reset_database()
