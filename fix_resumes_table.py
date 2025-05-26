import sqlite3
from sqlite3 import Error

def fix_resumes_table():
    try:
        # Connect to the database
        db_path = 'instance/mock_interview.db'
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Check if we need to rename file_name to filename
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'file_name' in columns and 'filename' not in columns:
            print("Renaming 'file_name' column to 'filename'...")
            # SQLite doesn't support direct column renaming, so we need to create a new table
            cursor.executescript("""
                -- Create a new table with the correct schema
                CREATE TABLE new_resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    domain VARCHAR(50) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(255) NOT NULL,
                    file_type VARCHAR(10) NOT NULL,
                    file_size INTEGER NOT NULL,
                    is_parsed BOOLEAN DEFAULT 0,
                    parsed_data JSON,
                    created_at DATETIME,
                    updated_at DATETIME,
                    content TEXT,
                    uploaded_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                -- Copy data from old table to new table
                INSERT INTO new_resumes (
                    id, user_id, domain, filename, stored_filename, file_path, 
                    file_type, file_size, is_parsed, parsed_data, 
                    created_at, updated_at, content, uploaded_at
                ) SELECT 
                    id, user_id, domain, file_name, file_name, file_path, 
                    file_type, file_size, is_parsed, parsed_data, 
                    created_at, updated_at, content, uploaded_at
                FROM resumes;
                
                -- Drop the old table
                DROP TABLE resumes;
                
                -- Rename the new table
                ALTER TABLE new_resumes RENAME TO resumes;
                
                -- Recreate indexes and triggers if needed
                CREATE INDEX ix_resumes_user_id ON resumes (user_id);
            """)
            print("Successfully renamed 'file_name' to 'filename'")
        
        # Check if stored_filename column exists
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'stored_filename' not in columns:
            print("Adding 'stored_filename' column...")
            cursor.execute("""
                ALTER TABLE resumes ADD COLUMN stored_filename VARCHAR(255) NOT NULL DEFAULT '';
                
                -- Update existing rows to set stored_filename from filename
                UPDATE resumes SET stored_filename = filename;
            """)
            print("Successfully added 'stored_filename' column")
        
        # Commit changes
        conn.commit()
        print("Database schema updated successfully!")
        
    except Error as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    fix_resumes_table()
