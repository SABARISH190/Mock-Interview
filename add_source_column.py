from app import create_app, db
from app.models.interview import Question

def add_source_column():
    print("Adding 'source' column to questions table...")
    
    # Create the application context
    app = create_app()
    app.app_context().push()
    
    # Use SQLAlchemy's text() to execute raw SQL
    from sqlalchemy import text
    
    try:
        # Check if the column already exists
        conn = db.engine.connect()
        result = conn.execute(
            text("PRAGMA table_info(questions)")
        )
        columns = [row[1] for row in result]
        
        if 'source' not in columns:
            # Add the source column
            print("Adding 'source' column...")
            with db.engine.connect() as connection:
                connection.execute(
                    text('ALTER TABLE questions ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT "default"')
                )
                connection.commit()
            print("✅ Successfully added 'source' column")
        else:
            print("✅ 'source' column already exists")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_source_column()
