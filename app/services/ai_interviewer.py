import os
import json
import random
import logging
from datetime import datetime
from flask import current_app

# In a production app, you would likely use OpenAI or another LLM provider
# For this example, we'll implement a simple mock version
class AIInterviewer:
    """
    AI Interviewer class responsible for generating questions,
    analyzing responses, and providing interview feedback.
    """
    
    def __init__(self, domain, resume_analysis=None):
        """
        Initialize the AI Interviewer with a specific domain and optional resume analysis.
        
        Args:
            domain (str): The job domain (e.g., 'Full Stack Developer', 'AI Engineer')
            resume_analysis (dict, optional): Analysis of the candidate's resume
        """
        self.domain = domain
        self.resume_analysis = resume_analysis or {}
        self.logger = logging.getLogger(__name__)
        self.question_bank = self._load_question_bank()
        
        # If we have resume analysis, enhance question bank with personalized questions
        if resume_analysis:
            self._enhance_question_bank()
        
    def _generate_skill_questions(self, skill_category, skills):
        """
        Generate questions about specific skills mentioned in the resume.
        
        Args:
            skill_category (str): Category of skills (e.g., 'languages', 'frameworks')
            skills (dict): Dictionary of skills and their weights
            
        Returns:
            list: List of generated questions
        """
        questions = []
        
        # Sort skills by weight (highest first)
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        
        # Generate questions for top skills
        for skill, weight in sorted_skills[:5]:  # Limit to top 5 skills per category
            if weight >= 2:  # Only include skills with sufficient weight
                if skill_category == 'languages':
                    questions.extend([
                        f"Can you explain your experience with {skill}? What kind of projects have you used it for?",
                        f"What are some advanced features of {skill} that you've worked with?",
                        f"How would you compare {skill} to other similar technologies you've used?"
                    ])
                elif skill_category == 'frameworks' or skill_category.endswith('_frameworks'):
                    questions.extend([
                        f"What challenges have you faced while working with {skill}?",
                        f"Can you describe your experience with {skill}'s architecture?",
                        f"How do you handle version upgrades or migrations in {skill}?"
                    ])
                elif 'database' in skill_category or 'db' in skill_category:
                    questions.extend([
                        f"How have you optimized database performance in your projects using {skill}?",
                        f"Can you describe a complex query or data model you've implemented in {skill}?",
                        f"What are some limitations of {skill} that you've encountered?"
                    ])
                else:
                    questions.extend([
                        f"How would you rate your expertise with {skill} on a scale of 1-10, and why?",
                        f"Can you provide an example of how you've used {skill} to solve a problem?",
                        f"What resources do you use to stay updated with {skill}?"
                    ])
        
        return questions
    
    def _generate_experience_questions(self, experiences):
        """
        Generate questions based on the candidate's work experience.
        
        Args:
            experiences (list): List of work experience entries
            
        Returns:
            list: List of generated questions
        """
        questions = []
        
        for exp in experiences[:3]:  # Limit to most recent 3 experiences
            company = exp.get('company', 'your previous company')
            title = exp.get('title', 'your role')
            
            questions.extend([
                f"At {company}, what were your key responsibilities as {title}?",
                f"What was the most challenging project you worked on at {company} and why?",
                f"How did you measure success in your role at {company}?",
                f"What technologies did you work with at {company} and how did you use them?",
                f"Can you tell me about a time you had to learn something new at {company}?"
            ])
        
        return questions
    
    def _enhance_question_bank(self):
        """Enhance the question bank with personalized questions based on resume analysis."""
        if not self.resume_analysis:
            self.logger.warning("No resume analysis provided to enhance question bank")
            return
            
        # Ensure domain exists in question bank
        if self.domain not in self.question_bank:
            self.logger.warning(f"Domain '{self.domain}' not found in question bank. Available domains: {list(self.question_bank.keys())}")
            return
            
        # Ensure domain has the required question categories
        if not isinstance(self.question_bank[self.domain], dict):
            self.logger.error(f"Invalid question bank structure for domain '{self.domain}'")
            return
            
        # Initialize question categories if they don't exist
        if 'technical' not in self.question_bank[self.domain]:
            self.question_bank[self.domain]['technical'] = []
        if 'behavioral' not in self.question_bank[self.domain]:
            self.question_bank[self.domain]['behavioral'] = []
        
        # Add skill-based questions if we have skills analysis
        skills_analysis = self.resume_analysis.get('skills_analysis', {})
        if skills_analysis and isinstance(skills_analysis, dict):
            for category, skills in skills_analysis.items():
                if not skills:
                    continue
                    
                try:
                    skill_questions = self._generate_skill_questions(category, skills)
                    if skill_questions:
                        self.question_bank[self.domain]['technical'].extend(skill_questions)
                        self.logger.debug(f"Added {len(skill_questions)} skill questions for category: {category}")
                except Exception as e:
                    self.logger.error(f"Error generating skill questions for category {category}: {str(e)}", exc_info=True)
        else:
            self.logger.warning("No valid skills analysis found in resume data")
        
        # Add experience-based questions if we have experience data
        experiences = self.resume_analysis.get('experience', [])
        if experiences and isinstance(experiences, list):
            try:
                exp_questions = self._generate_experience_questions(experiences)
                if exp_questions:
                    self.question_bank[self.domain]['behavioral'].extend(exp_questions)
                    self.logger.debug(f"Added {len(exp_questions)} experience-based questions")
            except Exception as e:
                self.logger.error(f"Error generating experience questions: {str(e)}", exc_info=True)
        else:
            self.logger.warning("No valid experience data found in resume analysis")
    
    def _load_question_bank(self):
        """Load domain-specific questions from the question bank."""
        try:
            # In a real application, you would load from a database or API
            # For this example, we'll use pre-defined questions
            
            question_bank = {
                'Full Stack Developer': {
                    'technical': [
                        "Can you explain the difference between REST and GraphQL APIs?",
                        "How do you handle authentication in a web application?",
                        "What's your experience with front-end frameworks like React, Angular, or Vue.js?",
                        "Explain the concept of middleware in the context of web frameworks.",
                        "How would you optimize a web application for performance?",
                        "What's your approach to responsive design?",
                        "Explain the concept of server-side rendering and its benefits."
                    ],
                    'behavioral': [
                        "Tell me about a challenging project you worked on and how you overcame obstacles.",
                        "How do you stay updated with the latest web development trends?",
                        "How do you handle code reviews and feedback from team members?",
                        "Describe how you would debug a complex issue in a web application."
                    ]
                },
                'AI Engineer': {
                    'technical': [
                        "What's the difference between supervised and unsupervised learning?",
                        "Explain the concept of neural networks and deep learning.",
                        "How would you handle a dataset with missing values?",
                        "What metrics would you use to evaluate a classification model?",
                        "Explain the concept of transfer learning and when you would use it.",
                        "What's your experience with natural language processing?",
                        "How do you optimize a model that's overfitting?"
                    ],
                    'behavioral': [
                        "Tell me about a data science project you've worked on.",
                        "How do you approach a new machine learning problem?",
                        "How do you explain complex machine learning concepts to non-technical stakeholders?",
                        "How do you stay current with the rapidly evolving field of AI and ML?"
                    ]
                },
                'Data Analyst': {
                    'technical': [
                        "What's your experience with SQL and data querying?",
                        "How would you approach cleaning a dataset with inconsistencies?",
                        "What data visualization tools are you familiar with?",
                        "Explain the difference between correlation and causation.",
                        "How would you design and analyze an A/B test?",
                        "What statistical methods do you use for data analysis?",
                        "How do you handle outliers in a dataset?"
                    ],
                    'behavioral': [
                        "Tell me about a data analysis project that provided valuable insights.",
                        "How do you communicate data findings to stakeholders?",
                        "Describe a situation where you had to work with limited or incomplete data.",
                        "How do you validate your data analysis results?"
                    ]
                }
            }
            
            # Default to a general question bank if the domain isn't found
            return question_bank.get(self.domain, {
                'technical': [
                    "Tell me about your technical background.",
                    "What programming languages are you familiar with?",
                    "Describe a challenging technical problem you've solved.",
                    "How do you approach learning new technologies?"
                ],
                'behavioral': [
                    "Tell me about yourself.",
                    "What are your strengths and weaknesses?",
                    "Why are you interested in this field?",
                    "Where do you see yourself in five years?"
                ]
            })
            
        except Exception as e:
            self.logger.error(f"Error loading question bank: {str(e)}")
            # Return a minimal question bank if there's an error
            return {
                'technical': ["Tell me about your technical experience."],
                'behavioral': ["Tell me about your background."]
            }
    
    def generate_question(self, resume_data=None):
        """
        Generate a relevant interview question based on the domain and optionally resume data.
        
        Args:
            resume_data (dict, optional): Parsed resume data with skills, experience, etc.
            
        Returns:
            str: An interview question
        """
        # In a real AI system, you would use resume_data to generate personalized questions
        # For this example, we'll randomly select from our question bank
        
        # Decide question type (technical or behavioral)
        question_type = random.choice(['technical', 'behavioral'])
        
        # Get questions for the selected type
        questions = self.question_bank.get(question_type, [])
        
        if not questions:
            return "Could you tell me about your experience and skills?"
            
        return random.choice(questions)
    
    def generate_next_question(self, conversation_history=None):
        """
        Generate the next interview question based on the conversation history.
        
        Args:
            conversation_history (list, optional): List of previous questions and answers.
            
        Returns:
            str: The next interview question
        """
        # In a real AI system, you would analyze the conversation history
        # to generate a relevant follow-up question
        
        # For this example, we'll just return another random question
        # that hasn't been asked yet
        
        asked_questions = []
        if conversation_history:
            for item in conversation_history:
                if item.get('role') == 'interviewer':
                    asked_questions.append(item.get('content'))
        
        # Combine all questions
        all_questions = self.question_bank.get('technical', []) + self.question_bank.get('behavioral', [])
        
        # Filter out questions that have already been asked
        available_questions = [q for q in all_questions if q not in asked_questions]
        
        if not available_questions:
            return "Is there anything else you'd like to add about your experience or skills?"
            
        return random.choice(available_questions)
    
    def analyze_response(self, question, answer):
        """
        Analyze a candidate's response to a question.
        
        Args:
            question (str): The interview question
            answer (str): The candidate's answer
            
        Returns:
            dict: Analysis with relevance, clarity, completeness scores
        """
        # In a real AI system, you would use NLP to analyze the response
        # For this example, we'll generate random scores
        
        # Simple analysis based on answer length and complexity
        word_count = len(answer.split())
        
        # Very basic metrics - in a real system, you'd use NLP for this
        relevance = min(100, max(50, random.randint(60, 95)))
        clarity = min(100, max(50, random.randint(60, 95)))
        completeness = min(100, max(50, 70 + word_count // 10))  # Longer answers score better
        
        return {
            'relevance': relevance,
            'clarity': clarity,
            'completeness': completeness,
            'overall': (relevance + clarity + completeness) / 3
        }
    
    def analyze_interview(self, conversation):
        """
        Analyze the entire interview and provide a comprehensive assessment.
        
        Args:
            conversation (list): List of questions and answers
            
        Returns:
            dict: Comprehensive analysis with scores and feedback
        """
        # In a real AI system, you would use NLP to analyze the entire conversation
        # For this example, we'll generate a simple analysis
        
        # Count questions and answers
        questions = [item for item in conversation if item.get('role') == 'interviewer']
        answers = [item for item in conversation if item.get('role') == 'candidate']
        
        if not questions or not answers:
            return {
                'technical_score': 0,
                'communication_score': 0,
                'problem_solving_score': 0,
                'overall_score': 0,
                'strengths': [],
                'weaknesses': [],
                'technical_suggestions': "No interview data to analyze.",
                'communication_suggestions': "No interview data to analyze.",
                'general_suggestions': "Please complete an interview to receive feedback."
            }
        
        # Analyze individual responses
        response_scores = []
        for i in range(min(len(questions), len(answers))):
            question = questions[i].get('content', '')
            answer = answers[i].get('content', '')
            
            score = self.analyze_response(question, answer)
            response_scores.append(score)
        
        # Calculate overall scores
        if not response_scores:
            return {
                'technical_score': 0,
                'communication_score': 0,
                'problem_solving_score': 0,
                'overall_score': 0,
                'strengths': [],
                'weaknesses': [],
                'technical_suggestions': "No interview data to analyze.",
                'communication_suggestions': "No interview data to analyze.",
                'general_suggestions': "Please complete an interview to receive feedback."
            }
            
        # Average scores across all responses
        avg_relevance = sum(s['relevance'] for s in response_scores) / len(response_scores)
        avg_clarity = sum(s['clarity'] for s in response_scores) / len(response_scores)
        avg_completeness = sum(s['completeness'] for s in response_scores) / len(response_scores)
        
        # Map these to our desired output metrics
        technical_score = avg_relevance
        communication_score = avg_clarity
        problem_solving_score = avg_completeness
        overall_score = (technical_score + communication_score + problem_solving_score) / 3
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        # Technical strengths/weaknesses
        if technical_score >= 80:
            strengths.append("Strong technical knowledge in your domain")
        elif technical_score <= 60:
            weaknesses.append("Could improve technical depth and understanding of the domain")
        
        # Communication strengths/weaknesses
        if communication_score >= 80:
            strengths.append("Excellent communication skills with clear and concise responses")
        elif communication_score <= 60:
            weaknesses.append("Work on providing clearer and more structured responses")
        
        # Problem-solving strengths/weaknesses
        if problem_solving_score >= 80:
            strengths.append("Effective problem-solving approach with thorough solutions")
        elif problem_solving_score <= 60:
            weaknesses.append("Could improve problem-solving techniques and provide more complete solutions")
        
        # Ensure we have at least one strength and weakness
        if not strengths:
            strengths.append("Participated well in the interview process")
        if not weaknesses:
            weaknesses.append("Consider providing more detailed examples from your experience")
        
        # Generate suggestions
        technical_suggestions = ""
        communication_suggestions = ""
        general_suggestions = ""
        
        if technical_score <= 70:
            technical_suggestions = "Focus on deepening your technical knowledge in key areas of your domain. Consider online courses or practice projects to strengthen your skills."
        else:
            technical_suggestions = "Continue building on your technical foundation by exploring advanced concepts and staying current with industry trends."
        
        if communication_score <= 70:
            communication_suggestions = "Practice structuring your responses using the STAR method (Situation, Task, Action, Result) and work on concise explanations of complex topics."
        else:
            communication_suggestions = "Your communication is strong. Consider practicing with technical and non-technical audiences to further refine your ability to explain complex concepts."
        
        general_suggestions = f"Overall, you scored {overall_score:.1f}/100. Continue practicing mock interviews and focus on the areas mentioned for improvement."
        
        return {
            'technical_score': technical_score,
            'communication_score': communication_score,
            'problem_solving_score': problem_solving_score,
            'overall_score': overall_score,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'technical_suggestions': technical_suggestions,
            'communication_suggestions': communication_suggestions,
            'general_suggestions': general_suggestions
        }
    
    def generate_report(self, interview_data, analysis):
        """
        Generate a detailed PDF report based on the interview analysis.
        
        Args:
            interview_data (dict): Interview details including questions and answers
            analysis (dict): The completed analysis
            
        Returns:
            str: Path to the generated PDF report
        """
        # In a real application, you would generate a PDF report here
        # For this example, we'll just return a mock report path
        
        report_dir = os.path.join(current_app.root_path, 'static/reports')
        os.makedirs(report_dir, exist_ok=True)
        
        report_filename = f"interview_report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        report_path = os.path.join(report_dir, report_filename)
        
        # In a real application, generate the actual PDF here
        # For now, just create a placeholder file
        with open(report_path, 'w') as f:
            f.write("Mock Interview Report")
        
        return report_path
