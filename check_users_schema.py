"""Script to check the users table schema."""
import sqlite3

def check_schema():
    """Check the schema of the users table."""
    try:
        # Connect to the SQLite database
        db_path = 'instance/mock_interview.db'
        print(f"Connecting to database at: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        if not columns:
            print("Error: Users table not found or is empty.")
            return
            
        print("\nUsers table columns:")
        print("-" * 50)
        print(f"{'CID':<5} {'Name':<20} {'Type':<15} {'Not Null':<8} {'Default':<10} {'PK':<5}")
        print("-" * 50)
        
        for col in columns:
            print(f"{col[0]:<5} {col[1]:<20} {col[2]:<15} {bool(col[3]):<8} {str(col[4]):<10} {bool(col[5]):<5}")
        
        # Check if last_seen column exists
        last_seen_exists = any(col[1] == 'last_seen' for col in columns)
        print("\nCheck for last_seen column:", 
              "Found" if last_seen_exists else "Not found")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    check_schema()
