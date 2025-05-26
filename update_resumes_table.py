from app import create_app, db
from app.models.resume import Resume

def update_resumes_table():
    print("Updating resumes table...")
    
    # Create the application context
    app = create_app()
    app.app_context().push()
    
    try:
        # Check if the filename column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('resumes')]
        
        # Add missing columns if they don't exist
        with db.engine.connect() as conn:
            if 'filename' not in columns:
                print("Adding 'filename' column to resumes table...")
                conn.execute('ALTER TABLE resumes ADD COLUMN filename VARCHAR(255) NOT NULL DEFAULT "";')
            
            if 'stored_filename' not in columns:
                print("Adding 'stored_filename' column to resumes table...")
                conn.execute('ALTER TABLE resumes ADD COLUMN stored_filename VARCHAR(255) NOT NULL DEFAULT "";')
            
            if 'file_path' not in columns:
                print("Adding 'file_path' column to resumes table...")
                conn.execute('ALTER TABLE resumes ADD COLUMN file_path VARCHAR(500) NOT NULL DEFAULT "";')
            
            if 'file_size' not in columns:
                print("Adding 'file_size' column to resumes table...")
                conn.execute('ALTER TABLE resumes ADD COLUMN file_size INTEGER NOT NULL DEFAULT 0;')
            
            if 'file_type' not in columns:
                print("Adding 'file_type' column to resumes table...")
                conn.execute('ALTER TABLE resumes ADD COLUMN file_type VARCHAR(10) NOT NULL DEFAULT "";')
            
            conn.commit()
            
        print("Resumes table updated successfully!")
        
    except Exception as e:
        print(f"Error updating resumes table: {str(e)}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == '__main__':
    update_resumes_table()
