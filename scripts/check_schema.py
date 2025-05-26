import sqlite3
from pathlib import Path

def check_schema():
    # Path to the database
    db_path = Path('instance/mock_interview.db')
    if not db_path.exists():
        db_path = Path('mock_interview.db')
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return
    
    print(f"Checking database schema at: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nTables in database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * 50)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Columns:")
            for column in columns:
                print(f"  {column[1]} ({column[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\n  Rows: {count}")
            
            # Show sample data if table is not empty
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                row = cursor.fetchone()
                print("\n  Sample row:")
                for i, column in enumerate(columns):
                    col_name = column[1]
                    col_value = row[i] if i < len(row) else None
                    print(f"    {col_name}: {str(col_value)[:100]}" + ("..." if col_value and len(str(col_value)) > 100 else ""))
        
    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_schema()
