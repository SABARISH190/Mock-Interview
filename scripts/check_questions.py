import sys
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, select

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Import config
from config import Config

def check_question_bank():
    # Create a database engine
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Reflect the database
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Check if question_bank table exists
    if 'question_bank' not in metadata.tables:
        print("Error: 'question_bank' table does not exist in the database.")
        return False
    
    # Get the question_bank table
    question_bank = Table('question_bank', metadata, autoload_with=engine)
    
    # Connect to the database
    with engine.connect() as connection:
        # Count total questions
        count_query = select([question_bank.c.id]).select_from(question_bank)
        result = connection.execute(count_query)
        total_questions = result.rowcount
        
        # Get questions by domain
        domain_query = select([question_bank.c.domain, question_bank.c.question_type, question_bank.c.difficulty, question_bank.c.question_text])\
                        .select_from(question_bank)
        
        print(f"\nFound {total_questions} questions in the question bank.")
        print("\nSample questions:")
        print("-" * 80)
        
        # Print sample questions
        sample_query = select([question_bank]).limit(5)
        result = connection.execute(sample_query)
        
        for row in result:
            print(f"Domain: {row.domain}")
            print(f"Type: {row.question_type}")
            print(f"Difficulty: {row.difficulty}")
            print(f"Question: {row.question_text[:100]}...")
            print("-" * 80)
    
    return True

if __name__ == '__main__':
    print("Checking question bank database...")
    if check_question_bank():
        print("\nDatabase check completed successfully.")
    else:
        print("\nDatabase check failed.")
