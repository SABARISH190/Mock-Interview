"""
Test script for the QuestionSelector class.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.utils.question_selector import QuestionSelector

def test_question_selector():
    print("=" * 80)
    print("TESTING QUESTION SELECTOR")
    print("=" * 80)
    
    # Initialize the question selector
    selector = QuestionSelector()
    
    # Test getting questions for each domain
    domains = ['Full Stack Developer', 'AI Engineer', 'Data Analyst']
    
    for domain in domains:
        print("\n" + "-" * 80)
        print(f"DOMAIN: {domain.upper()}")
        print("-" * 80)
        
        try:
            print(f"\nReading questions from: {selector.domain_files.get(domain, 'Unknown')}")
            
            # Get questions
            questions = selector.get_interview_questions(
                domain=domain,
                tech_count=3,  # Get fewer questions for testing
                behavioral_count=2
            )
            
            # Print technical questions
            print("\nTECHNICAL QUESTIONS:")
            print("-" * 80)
            if not questions['technical']:
                print("No technical questions found")
            else:
                for i, q in enumerate(questions['technical'], 1):
                    print(f"\n{i}. {q['question']}")
                    print("   " + "\n   ".join([q['answer'][i:i+80] for i in range(0, min(240, len(q['answer'])), 80)]))
                    if len(q['answer']) > 240:
                        print("   ... [answer truncated]")
            
            # Print behavioral questions
            print("\n\nBEHAVIORAL QUESTIONS:")
            print("-" * 80)
            if not questions['behavioral']:
                print("No behavioral questions found")
            else:
                for i, q in enumerate(questions['behavioral'], 1):
                    print(f"\n{i}. {q['question']}")
                    print("   " + "\n   ".join([q['answer'][i:i+80] for i in range(0, min(240, len(q['answer'])), 80)]))
                    if len(q['answer']) > 240:
                        print("   ... [answer truncated]")
            
            print("\n" + "-" * 80)
                
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
    
    # Print debug info
    print("\nDEBUG INFO:")
    print(f"Base directory: {selector.base_dir}")
    for domain in domains:
        filename = selector.domain_files.get(domain)
        if filename:
            filepath = os.path.join(selector.base_dir, filename)
            exists = os.path.exists(filepath)
            print(f"{domain}: {filename} - {'Exists' if exists else 'Missing'}")
            if exists:
                print(f"   Path: {filepath}")

if __name__ == "__main__":
    test_question_selector()
