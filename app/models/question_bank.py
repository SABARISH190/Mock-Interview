from datetime import datetime
from app import db

class QuestionBank(db.Model):
    __tablename__ = 'question_bank'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(50), nullable=False)  # FullStack, AIEngineer, DataAnalyst, Behavioral
    question_text = db.Column(db.Text, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # technical, behavioral, situational
    difficulty = db.Column(db.String(20), nullable=True)  # easy, medium, hard
    category = db.Column(db.String(100), nullable=True)  # e.g., "Python", "Machine Learning", etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuestionBank {self.id} - {self.domain} - {self.question_text[:50]}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'domain': self.domain,
            'question_text': self.question_text,
            'answer_text': self.answer_text,
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'category': self.category
        }
