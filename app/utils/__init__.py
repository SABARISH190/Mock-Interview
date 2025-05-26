"""
Utility functions and classes for the Mock Interview application.
"""

from .question_selector import QuestionSelector

# Create a single instance of QuestionSelector that can be imported throughout the app
question_selector = QuestionSelector()
