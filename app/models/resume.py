from datetime import datetime
from app import db
import os

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    stored_filename = db.Column(db.String(255), nullable=False)  # Unique filename on disk
    file_path = db.Column(db.String(500), nullable=False)  # Full path to the file
    file_size = db.Column(db.Integer, nullable=False)  # File size in bytes
    file_type = db.Column(db.String(10), nullable=False)  # File extension (pdf, doc, docx)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship is defined in the User model
    
    def __init__(self, **kwargs):
        super(Resume, self).__init__(**kwargs)
        # Ensure the upload directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
    
    def delete_file(self):
        """Delete the physical file from disk."""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                return True
        except Exception as e:
            current_app.logger.error(f"Error deleting resume file {self.file_path}: {str(e)}")
        return False
    
    def get_file_extension(self):
        """Get the file extension in lowercase."""
        return os.path.splitext(self.filename)[1].lower() if self.filename else ''
    
    def get_file_size_mb(self):
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    def is_pdf(self):
        """Check if the file is a PDF."""
        return self.get_file_extension() == '.pdf'
    
    def is_word_doc(self):
        """Check if the file is a Word document."""
        return self.get_file_extension() in ['.doc', '.docx']
    
    def __repr__(self):
        return f'<Resume {self.filename} (User {self.user_id})>'
