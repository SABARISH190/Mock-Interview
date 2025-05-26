from app import create_app, db

def check_resumes_schema():
    print("Checking resumes table schema...")
    
    # Create the application context
    app = create_app()
    app.app_context().push()
    
    try:
        # Get the table information
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Get all columns in the resumes table
        columns = inspector.get_columns('resumes')
        
        print("\nResumes table columns:")
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
            
    except Exception as e:
        print(f"Error checking schema: {str(e)}")

if __name__ == '__main__':
    check_resumes_schema()
