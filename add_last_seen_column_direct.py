"""Script to directly add the last_seen column to the users table."""
import sqlite3

def add_last_seen_column():
    """Add last_seen column to the users table if it doesn't exist."""
    db_path = 'instance/mock_interview.db'
    print(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_seen' not in columns:
            print("Adding last_seen column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_seen DATETIME 
                DEFAULT CURRENT_TIMESTAMP
            """)
            conn.commit()
            print("Successfully added last_seen column to users table.")
        else:
            print("last_seen column already exists in users table.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_last_seen_column()
