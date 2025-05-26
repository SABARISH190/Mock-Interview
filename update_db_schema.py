"""Script to update the database schema to include the last_seen column."""
from app import create_app, db
from app.models.user import User

def update_schema():
    """Update the database schema to include the last_seen column."""
    app = create_app()
    with app.app_context():
        try:
            # This will create the last_seen column if it doesn't exist
            # by reflecting the current model changes to the database
            db.create_all()
            print("Database schema updated successfully.")
            
            # Verify the column was added
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('users')]
            
            if 'last_seen' in columns:
                print("Success: last_seen column exists in the users table.")
            else:
                print("Error: last_seen column was not added to the users table.")
                
        except Exception as e:
            print(f"Error updating database schema: {e}")

if __name__ == '__main__':
    update_schema()
