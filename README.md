# AI-Powered Mock Interview Platform

A comprehensive platform for preparing for technical interviews using AI-powered mock interviews, resume analysis, and performance feedback.

## Features

- **User Authentication**: Secure registration and login with email/phone verification
- **Domain-specific Interviews**: Practice interviews for Full Stack, AI/ML, and Data Analysis
- **Resume Analysis**: Upload and analyze your resume for personalized interview questions
- **AI-powered Questions**: Dynamic question generation based on domain, difficulty, and your resume
- **Real-time Interview Simulation**: Audio recording and transcription for natural interview experience
- **Detailed Performance Analysis**: Get comprehensive feedback on technical knowledge, communication, and problem-solving
- **Progress Tracking**: Track your improvement over multiple practice sessions
- **Downloadable Reports**: Generate and download PDF reports of your interview performance

## Tech Stack

- **Backend**: Flask, Python
- **Database**: SQLAlchemy with SQLite (can be configured for PostgreSQL/MySQL)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap and Tailwind CSS
- **Authentication**: Flask-Login with JWT
- **AI Components**: Custom AI services for question generation and analysis

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment tool (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mock-interview-platform.git
   cd mock-interview-platform
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database with sample data:
   ```
   python init_db.py
   ```

5. Run the application:
   ```
   python run.py
   ```

6. Access the application in your browser:
   ```
   http://localhost:5000
   ```

### Default Users

- Admin User:
  - Email: admin@mockinterview.com
  - Password: admin12345

- Demo User:
  - Email: demo@mockinterview.com
  - Password: demo12345

## Project Structure

```
mock-interview-platform/
├── app/                        # Application package
│   ├── __init__.py            # Application factory
│   ├── models/                # Database models
│   │   ├── user.py           # User model
│   │   ├── resume.py         # Resume model
│   │   ├── interview.py      # Interview-related models
│   │   └── analysis.py       # Analysis model
│   ├── routes/                # Route handlers
│   │   ├── auth.py           # Authentication routes
│   │   ├── main.py           # Main routes
│   │   ├── interview.py      # Interview routes
│   │   ├── admin.py          # Admin routes
│   │   └── forms.py          # Form definitions
│   ├── services/              # Business logic services
│   │   ├── email.py          # Email service
│   │   ├── ai_interviewer.py # AI interview service
│   │   └── resume_parser.py  # Resume parsing service
│   ├── static/                # Static assets
│   │   ├── css/              # CSS files
│   │   ├── js/               # JavaScript files
│   │   └── images/           # Image assets
│   ├── templates/             # HTML templates
│   │   ├── auth/             # Authentication templates
│   │   ├── email/            # Email templates
│   │   ├── dashboard/        # Dashboard templates
│   │   ├── interview/        # Interview templates
│   │   └── admin/            # Admin templates
│   └── utils/                 # Utility functions
│       ├── decorators.py     # Custom decorators
│       └── errors.py         # Error handlers
├── config.py                  # Application configuration
├── requirements.txt           # Python dependencies
├── run.py                     # Application entry point
└── init_db.py                 # Database initialization script
```

## Features Explained

### User Authentication

- **Registration**: Users can register with email, phone, and password
- **OTP Verification**: Email/Phone verification using OTP
- **Password Reset**: Secure password reset functionality

### Dashboard

- **Overview Statistics**: View total interviews, completed interviews, and average scores
- **Upcoming Interviews**: See scheduled interviews with preparation links
- **Recent Interviews**: Access recent interview results
- **Resume Management**: Upload and manage resumes for different domains

### Interview Process

1. **Schedule**: Choose domain, difficulty, and optionally upload a resume
2. **Prepare**: Get domain-specific preparation tips and test your equipment
3. **Conduct**: Answer AI-generated questions with audio or text responses
4. **Analysis**: Receive detailed performance analysis and improvement suggestions

### Admin Features

- **User Management**: View and manage user accounts
- **Interview Overview**: Monitor all interviews conducted on the platform
- **Analytics**: View domain-wise statistics and user performance metrics

## Customization

### Adding New Domains

To add new interview domains, modify the following files:

1. Add domain options in `app/routes/forms.py`
2. Add domain questions in `app/services/ai_interviewer.py`
3. Add domain-specific skills in `app/services/resume_parser.py`

### Extending AI Capabilities

For enhanced AI capabilities:

1. Integrate with OpenAI or other LLM providers in `app/services/ai_interviewer.py`
2. Add more sophisticated resume parsing in `app/services/resume_parser.py`
3. Enhance the speech-to-text functionality in the interview process

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Flask and its extensions
- Bootstrap and Tailwind CSS for UI components
- FontAwesome for icons
- Chart.js for data visualization
