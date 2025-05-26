import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app, db
from app.models.question_bank import QuestionBank

def check_database():
    print("Checking database connection and models...")
    
    # Create app and push context
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    
    try:
        # Check if we can connect to the database
        print("\nTesting database connection...")
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        print("✅ Database connection successful")
        
        # Check if QuestionBank model is properly set up
        print("\nChecking QuestionBank model...")
        if hasattr(QuestionBank, '__tablename__'):
            print(f"✅ Found table: {QuestionBank.__tablename__}")
            
            # Try to query the table
            try:
                count = db.session.query(QuestionBank).count()
                print(f"✅ Found {count} questions in the database")
                
                # Show sample questions
                if count > 0:
                    print("\nSample questions:")
                    questions = db.session.query(QuestionBank).limit(3).all()
                    for i, q in enumerate(questions, 1):
                        print(f"\n{i}. {q.domain} - {q.question_text[:80]}...")
                        print(f"   Type: {q.question_type}, Difficulty: {q.difficulty}")
            except Exception as e:
                print(f"❌ Error querying QuestionBank: {str(e)}")
        else:
            print("❌ QuestionBank model does not have a table name")
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
    finally:
        # Clean up the application context
        app_context.pop()
        print("\nDatabase check complete.")

if __name__ == "__main__":
    check_database()
