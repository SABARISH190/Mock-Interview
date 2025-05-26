from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from wtforms.validators import DataRequired

class ResumeUploadForm(FlaskForm):
    """Form for uploading a resume."""
    resume = FileField('Resume', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF, DOC and DOCX files are allowed!')
    ])
    submit = SubmitField('Upload Resume')

    def validate_resume(self, field):
        # Check file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if field.data:
            field.data.seek(0, 2)  # Seek to end of file
            file_size = field.data.tell()
            field.data.seek(0)  # Reset file pointer to beginning
            
            if file_size > max_size:
                raise ValidationError('File size must be less than 5MB')
