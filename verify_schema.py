from app import create_app, db
from sqlalchemy import inspect

def verify_schema():
    print("Verifying database schema...")
    
    # Create the application context
    app = create_app()
    app.app_context().push()
    
    # Get the inspector
    inspector = inspect(db.engine)
    
    # Check if questions table exists
    if 'questions' not in inspector.get_table_names():
        print("❌ 'questions' table does not exist!")
        return
    
    # Get columns for questions table
    columns = inspector.get_columns('questions')
    
    print("\nColumns in 'questions' table:")
    print("-" * 50)
    for col in columns:
        print(f"Column: {col['name']}, Type: {col['type']}, Nullable: {col['nullable']}, Default: {col.get('default')}")
    
    # Check if source column exists
    source_column = [col for col in columns if col['name'] == 'source']
    if source_column:
        print("\n✅ 'source' column exists in the questions table")
        print(f"   - Type: {source_column[0]['type']}")
        print(f"   - Nullable: {source_column[0]['nullable']}")
        print(f"   - Default: {source_column[0].get('default')}")
    else:
        print("\n❌ 'source' column is missing from the questions table")

if __name__ == '__main__':
    verify_schema()
