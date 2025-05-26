import random
from typing import List, Dict, Optional
from sqlalchemy import or_
from app import db
from app.models.question_bank import QuestionBank

class QuestionSelector:
    def __init__(self):
        """
        Initialize the QuestionSelector to fetch questions from the database.
        """
        self.domain_mapping = {
            'Full Stack Developer': 'FullStackDeveloper',
            'AI Engineer': 'AIEngineer',
            'Data Analyst': 'DataAnalyst',
            'Behavioral': 'Behavioral'
        }
    
    def _get_domain_filter(self, domain: str) -> list:
        """
        Get the SQLAlchemy filter condition for the given domain.
        
        Args:
            domain: The domain to filter by (e.g., 'FullStackDeveloper', 'AIEngineer')
            
        Returns:
            SQLAlchemy filter condition
        """
        if domain == 'Behavioral':
            return [QuestionBank.domain == 'Behavioral']
        else:
            return [
                QuestionBank.domain == domain,
                QuestionBank.question_type == 'technical'
            ]
    
    def get_questions(self, domain: str, count: int = 5, difficulty: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get a list of random questions for a specific domain from the database.
        
        Args:
            domain: The domain to get questions for (e.g., 'Full Stack Developer')
            count: Number of questions to return
            difficulty: Optional difficulty filter ('easy', 'medium', 'hard')
            
        Returns:
            List of dictionaries with question details
        """
        if domain not in self.domain_mapping:
            return []
            
        domain_value = self.domain_mapping[domain]
        query = QuestionBank.query.filter(
            *self._get_domain_filter(domain_value)
        )
        
        if difficulty:
            query = query.filter(QuestionBank.difficulty == difficulty.lower())
            
        # Get all matching questions
        all_questions = query.all()
        
        if not all_questions:
            return []
            
        # If not enough questions, return all available
        if len(all_questions) <= count:
            return [q.to_dict() for q in all_questions]
            
        # Select random questions without replacement
        selected = random.sample(all_questions, count)
        return [q.to_dict() for q in selected]
    
    def get_behavioral_questions(self, count: int = 3) -> List[Dict[str, str]]:
        """
        Get a list of random behavioral questions from the database.
        
        Args:
            count: Number of questions to return
            
        Returns:
            List of dictionaries with question details
        """
        return self.get_questions('Behavioral', count)
    
    def get_interview_questions(self, domain: str, tech_count: int = 5, behavioral_count: int = 3) -> Dict[str, List[Dict[str, str]]]:
        """
        Get a complete set of interview questions.
        
        Args:
            domain: The technical domain
            tech_count: Number of technical questions (default: 5)
            behavioral_count: Number of behavioral questions (default: 3)
            behavioral_count: Number of behavioral questions (default: 15)
            
        Returns:
            Dictionary with 'technical' and 'behavioral' question lists
        """
        return {
            'technical': self.get_domain_questions(domain, tech_count),
            'behavioral': self.get_behavioral_questions(behavioral_count)
        }
