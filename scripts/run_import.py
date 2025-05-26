import os
import sys
from app import create_app, db
from app.models.question_bank import QuestionBank

def main():
    # Create the Flask application
    app = create_app()
    
    with app.app_context():
        # Import the populate_question_bank function
        script_path = os.path.join(os.path.dirname(__file__), 'populate_question_bank.py')
        
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("populate_question_bank", script_path)
        populate_module = importlib.util.module_from_spec(spec)
        sys.modules["populate_question_bank"] = populate_module
        spec.loader.exec_module(populate_module)
        
        # Call the populate function
        print("Starting to import questions...")
        populate_module.populate_question_bank()
        print("Question import completed successfully!")

if __name__ == '__main__':
    main()
