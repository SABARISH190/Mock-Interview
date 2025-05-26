import sqlite3
from pathlib import Path

def check_database():
    # Path to the SQLite database
    db_path = Path('instance/mock_interview.db')
    if not db_path.exists():
        db_path = Path('mock_interview.db')
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return
    
    print(f"Checking database at: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if question_bank table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_bank';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("\nTable 'question_bank' exists!")
            
            # Get table info
            cursor.execute("PRAGMA table_info(question_bank)")
            columns = cursor.fetchall()
            
            print("\nTable structure:")
            print("-" * 50)
            for column in columns:
                print(f"{column[1]}: {column[2]}")
                
            # Count rows
            cursor.execute("SELECT COUNT(*) FROM question_bank")
            count = cursor.fetchone()[0]
            print(f"\nTotal rows: {count}")
            
            # Show sample data
            if count > 0:
                cursor.execute("SELECT * FROM question_bank LIMIT 5")
                rows = cursor.fetchall()
                
                print("\nSample data:")
                print("-" * 50)
                for row in rows:
                    print(f"ID: {row[0]}")
                    print(f"Domain: {row[1]}")
                    print(f"Question: {row[2][:50]}...")
                    print(f"Answer: {row[3][:50]}..." if row[3] else "No answer")
                    print("-" * 30)
        else:
            print("\nTable 'question_bank' does not exist.")
            
            # List all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("\nAvailable tables:")
            for table in tables:
                print(f"- {table[0]}")
        
    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database()
