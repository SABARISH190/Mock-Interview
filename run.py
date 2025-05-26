import os
import signal
import sys
from dotenv import load_dotenv
from app import create_app, db
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import Interview, Question, Response
from app.models.analysis import Analysis

# Load environment variables from .env file
load_dotenv()

app = create_app(os.getenv('FLASK_CONFIG') or 'config.DevelopmentConfig')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Resume': Resume, 
        'Interview': Interview, 
        'Question': Question, 
        'Response': Response, 
        'Analysis': Analysis
    }

def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    # Perform any cleanup here if needed
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
    
    # Run the app with threading disabled to prevent daemon thread issues
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)
