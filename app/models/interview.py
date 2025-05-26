from datetime import datetime
from app import db

class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=True)
    domain = db.Column(db.String(50), nullable=False)  # Full Stack, AI Engineer, Data Analyst
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    attempt_number = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='interview', lazy=True, cascade='all, delete-orphan')
    analysis = db.relationship('Analysis', backref='interview', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Interview {self.id} - {self.domain} - User {self.user_id}>"


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # technical, behavioral, situational, etc.
    difficulty = db.Column(db.String(20), nullable=True)  # easy, medium, hard
    category = db.Column(db.String(100), nullable=True)  # e.g., "Python", "Machine Learning", etc.
    source = db.Column(db.String(20), default='default', nullable=False)  # 'ai_generated' or 'default'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    responses = db.relationship('Response', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Question {self.id} - {self.question_text[:50]}...>"


class Response(db.Model):
    __tablename__ = 'responses'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)  # Text transcription of the answer
    audio_path = db.Column(db.String(255), nullable=True)  # Path to the audio file
    duration = db.Column(db.Float, nullable=True)  # Duration of the response in seconds
    sentiment_score = db.Column(db.Float, nullable=True)  # Sentiment analysis score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Response {self.id} - Q{self.question_id}>"
