"""Simple script to add last_seen column to users table."""
import sqlite3

def add_last_seen():
    """Add last_seen column to users table if it doesn't exist."""
    try:
        # Connect to the SQLite database
        db_path = 'instance/mock_interview.db'  # Updated database path
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_seen' not in columns:
            # Add the column
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_seen DATETIME 
                DEFAULT CURRENT_TIMESTAMP
            """)
            conn.commit()
            print("Successfully added last_seen column to users table.")
        else:
            print("last_seen column already exists in users table.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_last_seen()
