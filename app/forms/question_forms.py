from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, TextAreaField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class QuestionForm(FlaskForm):
    """Form for adding or editing a question."""
    text = TextAreaField('Question Text', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='Question must be between 10 and 1000 characters long')
    ])
    
    question_type = SelectField('Question Type', 
                              choices=[
                                  ('technical', 'Technical'),
                                  ('behavioral', 'Behavioral'),
                                  ('situational', 'Situational')
                              ],
                              validators=[DataRequired()])
    
    domain = StringField('Domain', validators=[
        DataRequired(),
        Length(max=100, message='Domain cannot be longer than 100 characters')
    ])
    
    difficulty = SelectField('Difficulty',
                           choices=[
                               ('easy', 'Easy'),
                               ('medium', 'Medium'),
                               ('hard', 'Hard')
                           ],
                           validators=[DataRequired()])
    
    time_limit = IntegerField('Time Limit (seconds)', 
                            validators=[
                                Optional(),
                                NumberRange(min=30, max=600, message='Time limit must be between 30 and 600 seconds')
                            ],
                            default=120)
    
    is_active = BooleanField('Active', default=True)
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Question')

class ImportQuestionsForm(FlaskForm):
    """Form for importing questions from a file."""
    domain = SelectField('Domain', validators=[DataRequired()], choices=[])
    question_type = SelectField('Question Type', 
                              choices=[
                                  ('technical', 'Technical'),
                                  ('behavioral', 'Behavioral'),
                                  ('situational', 'Situational')
                              ],
                              validators=[DataRequired()])
    file = FileField('Question File', validators=[
        FileRequired(),
        FileAllowed(['json', 'csv'], 'Only JSON and CSV files are allowed')
    ])
    submit = SubmitField('Import Questions')
