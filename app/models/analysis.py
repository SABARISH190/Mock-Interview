from datetime import datetime
from app import db

class Analysis(db.Model):
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id'), nullable=False, unique=True)
    
    # Overall scores (0-100)
    technical_score = db.Column(db.Float, nullable=True)
    communication_score = db.Column(db.Float, nullable=True)
    problem_solving_score = db.Column(db.Float, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    overall_score = db.Column(db.Float, nullable=True)
    
    # Detailed feedback
    strengths = db.Column(db.JSON, nullable=True)  # List of strengths
    weaknesses = db.Column(db.JSON, nullable=True)  # List of weaknesses
    
    # Suggestions for improvement
    technical_suggestions = db.Column(db.Text, nullable=True)
    communication_suggestions = db.Column(db.Text, nullable=True)
    general_suggestions = db.Column(db.Text, nullable=True)
    
    # Comparison with previous attempts
    previous_scores = db.Column(db.JSON, nullable=True)  # Array of previous scores for trend analysis
    improvement_since_last = db.Column(db.Float, nullable=True)  # Percentage improvement
    
    # Additional metrics
    word_count = db.Column(db.Integer, nullable=True)
    speech_rate = db.Column(db.Float, nullable=True)  # Words per minute
    filler_words = db.Column(db.JSON, nullable=True)  # Count of filler words used
    
    # Report generation
    report_path = db.Column(db.String(255), nullable=True)  # Path to generated PDF report
    is_report_generated = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Analysis {self.id} - Interview {self.interview_id}>"
    
    def to_dict(self):
        """Convert analysis to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'interview_id': self.interview_id,
            'scores': {
                'technical': self.technical_score,
                'communication': self.communication_score,
                'problem_solving': self.problem_solving_score,
                'confidence': self.confidence_score,
                'overall': self.overall_score
            },
            'strengths': self.strengths or [],
            'weaknesses': self.weaknesses or [],
            'suggestions': {
                'technical': self.technical_suggestions,
                'communication': self.communication_suggestions,
                'general': self.general_suggestions
            },
            'improvement': self.improvement_since_last,
            'report_available': self.is_report_generated,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
