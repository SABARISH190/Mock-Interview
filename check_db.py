import sqlite3
from sqlite3 import Error

def check_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check question_bank table
        print("\nQuestion Bank:")
        try:
            cursor.execute("SELECT domain, question_type, COUNT(*) as count FROM question_bank GROUP BY domain, question_type")
            qb_stats = cursor.fetchall()
            if qb_stats:
                for domain, q_type, count in qb_stats:
                    print(f"- {domain} > {q_type}: {count} questions")
            else:
                print("No questions found in the question bank.")
        except Error as e:
            print(f"Error accessing question_bank: {e}")
            
        # Check interviews and questions
        print("\nInterviews and Questions:")
        try:
            cursor.execute("""
                SELECT i.id, i.domain, i.status, COUNT(q.id) as question_count 
                FROM interviews i
                LEFT JOIN questions q ON i.id = q.interview_id
                GROUP BY i.id
                ORDER BY i.created_at DESC
                LIMIT 5
            """)
            interviews = cursor.fetchall()
            if interviews:
                for int_id, domain, status, q_count in interviews:
                    print(f"- Interview {int_id} ({domain}): {q_count} questions, Status: {status}")
            else:
                print("No interviews found in the database.")
        except Error as e:
            print(f"Error accessing interviews: {e}")
            
        # Close the connection
        conn.close()
        
    except Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_database()
