from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import Config

def check_question_bank():
    # Create database engine
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Create a configured "Session" class
    Session = sessionmaker(bind=engine)
    
    # Create a Session
    session = Session()
    
    try:
        # Get total count of questions
        total_questions = session.execute(text("SELECT COUNT(*) FROM question_bank")).scalar()
        print(f"Total questions in database: {total_questions}")
        
        # Get count by domain
        print("\nQuestions by domain:")
        domain_counts = session.execute("""
            SELECT domain, COUNT(*) as count 
            FROM question_bank 
            GROUP BY domain
        """)
        for domain, count in domain_counts:
            print(f"- {domain}: {count} questions")
            
        # Get sample questions
        print("\nSample questions:")
        sample_questions = session.execute("""
            SELECT domain, question_text, question_type, difficulty
            FROM question_bank 
            LIMIT 5
        """)
        
        for domain, question, q_type, difficulty in sample_questions:
            print(f"\nDomain: {domain} ({q_type}, {difficulty})")
            print(f"Question: {question[:100]}...")
            
    except Exception as e:
        print(f"Error checking question bank: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_question_bank()
