"""Script to fix the last_seen column in the users table."""
from app import create_app, db

def fix_last_seen():
    """Add last_seen column to users table if it doesn't exist."""
    app = create_app()
    with app.app_context():
        try:
            # Add the column using raw SQL
            with db.engine.connect() as conn:
                conn.execute("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS last_seen DATETIME 
                    DEFAULT CURRENT_TIMESTAMP
                """)
                conn.commit()
            print("Successfully added last_seen column to users table.")
            return True
        except Exception as e:
            print(f"Error adding last_seen column: {e}")
            return False

if __name__ == '__main__':
    fix_last_seen()
