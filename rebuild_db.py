"""Script to rebuild the database with the updated schema."""
import os
import shutil
from datetime import datetime

from app import create_app, db
from app.models.user import User

def rebuild_database():
    """Rebuild the database with the updated schema."""
    app = create_app()
    
    # Path to the database
    db_path = 'instance/mock_interview.db'
    backup_path = 'instance/mock_interview_backup.db'
    
    try:
        print("Creating a backup of the current database...")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        shutil.copy2(db_path, backup_path)
        
        print("Backup created at:", backup_path)
        
        # Remove the existing database
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Removed existing database.")
        
        # Create all tables
        with app.app_context():
            db.create_all()
            print("Successfully created all tables with the updated schema.")
            
            # Verify the last_seen column exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('users')]
            
            if 'last_seen' in columns:
                print("Success: last_seen column exists in the users table.")
                
                # Update the last_seen column for all users
                users = User.query.all()
                for user in users:
                    user.last_seen = datetime.utcnow()
                
                db.session.commit()
                print(f"Updated last_seen for {len(users)} users.")
            else:
                print("Error: last_seen column was not added to the users table.")
    
    except Exception as e:
        print(f"Error rebuilding database: {e}")
        print("Please restore from the backup if needed.")

if __name__ == '__main__':
    rebuild_database()
