import os
import time
from app import create_app, db

def check_db_connection():
    """Check if we can connect to the database and list all tables."""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to connect to the database
            print("Attempting to connect to the database...")
            db.engine.connect()
            print("Successfully connected to the database!")
            
            # List all tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print("\nTables in the database:")
            for table in tables:
                print(f"- {table}")
                
            # Check if question_bank table exists
            if 'question_bank' in tables:
                print("\nQuestion bank table exists. Checking columns...")
                columns = [col['name'] for col in inspector.get_columns('question_bank')]
                print("Columns in question_bank table:", ", ".join(columns))
            
            return True
            
        except Exception as e:
            print(f"\nError connecting to the database: {e}")
            print("\nPlease make sure no other processes are using the database file.")
            print("Check for any running Python processes or database tools that might have the file open.")
            return False

if __name__ == "__main__":
    check_db_connection()
