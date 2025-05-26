"""Script to add last_seen column to users table."""
from app import create_app, db
from app.models.user import User

def add_last_seen_column():
    """Add last_seen column to users table."""
    app = create_app()
    with app.app_context():
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('users')]
        
        if 'last_seen' not in columns:
            # Add the column using raw SQL
            with db.engine.connect() as conn:
                conn.execute('ALTER TABLE users ADD COLUMN last_seen DATETIME DEFAULT CURRENT_TIMESTAMP')
                conn.commit()
            print("Successfully added last_seen column to users table.")
        else:
            print("last_seen column already exists in users table.")

if __name__ == '__main__':
    add_last_seen_column()
