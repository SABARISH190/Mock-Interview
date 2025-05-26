# Import forms here to make them available when importing from app.forms
from app.forms.user_forms import LoginForm, RegistrationForm, UpdateProfileForm
from app.forms.question_forms import QuestionForm
from app.forms.resume_forms import ResumeUploadForm

# Make forms available when importing from app.forms
__all__ = ['LoginForm', 'RegistrationForm', 'UpdateProfileForm', 'QuestionForm', 'ResumeUploadForm']
