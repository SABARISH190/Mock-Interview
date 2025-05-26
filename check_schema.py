import sqlite3

def check_schema():
    try:
        # Connect to the database
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Tables in database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 8))
            
            # Get table info
            try:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                if columns:
                    for col in columns:
                        # col[1] is the column name, col[2] is the data type
                        print(f"  - {col[1]}: {col[2]}")
                else:
                    print("  No columns found")
            except sqlite3.Error as e:
                print(f"  Error getting columns: {e}")
        
        # Close the connection
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_schema()
