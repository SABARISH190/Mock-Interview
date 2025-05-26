from app import create_app, db
import os

def recreate_database():
    print("Recreating database...")
    
    # Create the application context
    app = create_app()
    app.app_context().push()
    
    # Delete the database file if it exists
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create all tables
    print("Creating database tables...")
    db.create_all()
    
    print("\n✅ Database recreated successfully!")
    print(f"Database location: {os.path.abspath(db_path)}")

if __name__ == '__main__':
    recreate_database()
