import sqlite3
from sqlite3 import Error

def check_schema():
    try:
        # Try to connect to the SQLite database
        db_paths = [
            'instance/mock_interview.db',
            'mock_interview.db',
            'instance/app.db',
            'app.db'
        ]
        
        conn = None
        for db_path in db_paths:
            try:
                print(f"Trying to connect to database at: {db_path}")
                conn = sqlite3.connect(db_path)
                print(f"Successfully connected to: {db_path}")
                break
            except Error as e:
                print(f"Could not connect to {db_path}: {str(e)}")
        
        if not conn:
            print("Error: Could not connect to any database")
            return
            
        cursor = conn.cursor()
        
        # Check if resumes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resumes';")
        if not cursor.fetchone():
            print("\nError: 'resumes' table does not exist in the database")
            return
        
        # Get table info for resumes
        cursor.execute("PRAGMA table_info(resumes)")
        columns = cursor.fetchall()
        
        print("\nColumns in 'resumes' table:")
        print("-" * 50)
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, Not Null: {col[3]}, Default: {col[4]}, Primary Key: {col[5]}")
        
        # Check for required columns
        required_columns = ['filename', 'stored_filename', 'file_path', 'file_size', 'file_type']
        existing_columns = [col[1] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print("\nMissing required columns:")
            for col in missing_columns:
                print(f"- {col}")
        else:
            print("\nAll required columns are present in the 'resumes' table")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_schema()
