"""Script to directly add the last_seen column to the users table."""
import sqlite3

def add_column():
    """Add the last_seen column to the users table."""
    db_path = 'instance/mock_interview.db'
    print(f"Connecting to database at: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add the column
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN last_seen DATETIME 
            DEFAULT CURRENT_TIMESTAMP
        """)
        
        # Commit the changes
        conn.commit()
        print("Successfully added last_seen column to users table.")
        
    except sqlite3.Error as e:
        print(f"Error adding column: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_column()
