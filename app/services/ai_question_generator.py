import os
import json
import logging
import hashlib
import time
import groq
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app
from ratelimit import limits, sleep_and_retry

class AIQuestionGenerator:
    # Rate limiting: 10 calls per minute (Groq's free tier limit)
    RATE_LIMIT = 10
    RATE_PERIOD = 60  # seconds
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Set to debug level for more detailed logs
        
        # Ensure we have the API key
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            self.logger.error("GROQ_API_KEY environment variable is not set")
            raise ValueError("GROQ_API_KEY environment variable is required")
            
        self.logger.info("Initializing Groq client with API key")
        try:
            self.client = groq.Client(api_key=api_key)
            self.logger.info("Successfully initialized Groq client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Groq client: {str(e)}")
            raise
            
        # Set up directories
        self.analysis_dir = os.path.join(current_app.root_path, 'static', 'analysis')
        self.cache_dir = os.path.join(current_app.instance_path, 'cache')
        os.makedirs(self.analysis_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.model = "mixtral-8x7b-32768"  # Groq's Mixtral model
        self.cache_ttl = timedelta(hours=24)  # Cache TTL
        self.logger.debug(f"Initialized with model: {self.model}")
    
    def save_analysis(self, resume_text, domain, analysis_type='resume'):
        """Save the resume text and analysis to a file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{analysis_type}_{domain.lower().replace(' ', '_')}_{timestamp}.txt"
            filepath = os.path.join(self.analysis_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Domain: {domain}\n")
                f.write(f"Analysis Type: {analysis_type}\n")
                f.write("="*50 + "\n")
                f.write(resume_text)
                
            self.logger.info(f"Saved {analysis_type} analysis to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving {analysis_type} analysis: {str(e)}", exc_info=True)
            return None
    
    def _get_cache_key(self, text, domain, question_type):
        """Generate a cache key for the given parameters."""
        key_str = f"{text[:1000]}_{domain}_{question_type}"  # Use first 1000 chars for key
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _get_cached_questions(self, cache_key):
        """Get cached questions if they exist and are not expired."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > self.cache_ttl:
                return None
                
            return cache_data['questions']
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Error reading cache file {cache_file}: {str(e)}")
            return None
    
    def _save_to_cache(self, cache_key, questions):
        """Save questions to cache."""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'questions': questions
            }
            
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            self.logger.error(f"Error saving to cache: {str(e)}")
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT, period=RATE_PERIOD)
    def _call_groq_api(self, prompt):
        """Make API call to Groq with rate limiting."""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=1000,
                top_p=1,
                n=1
            )
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Groq API error: {str(e)}")
            raise
    
    def generate_questions(self, resume_text, domain, num_questions=5, question_type='technical', projects=None):
        """
        Generate interview questions using Groq's API with caching and rate limiting.
        
        Args:
            resume_text (str): The resume text to analyze
            domain (str): The job domain (e.g., 'Full Stack Developer')
            num_questions (int): Number of questions to generate
            question_type (str): Type of questions ('technical', 'behavioral', 'project')
            projects (list): List of project details for project-specific questions
            
        Returns:
            list: List of generated questions
        """
        try:
            self.logger.info(f"Starting question generation for type: {question_type}")
            self.logger.debug(f"Domain: {domain}, Num questions: {num_questions}")
            
            # Check cache first
            cache_key = self._get_cache_key(resume_text, domain, question_type)
            self.logger.debug(f"Generated cache key: {cache_key}")
            
            cached = self._get_cached_questions(cache_key)
            if cached:
                self.logger.info(f"Using cached {len(cached)} {question_type} questions")
                return cached
            
            self.logger.info(f"Generating {num_questions} {question_type} questions for {domain}")
            
            # Log the first 200 chars of resume text for debugging
            self.logger.debug(f"Resume text sample: {resume_text[:200]}...")
            
            # Prepare the prompt based on question type
            if question_type == 'technical':
                prompt = self._create_technical_prompt(resume_text, domain, num_questions)
            elif question_type == 'behavioral':
                prompt = self._create_behavioral_prompt(resume_text, domain, num_questions)
            elif question_type == 'project' and projects:
                prompt = self._create_project_prompt(projects, domain, num_questions)
            else:  # experience
                prompt = self._create_experience_prompt(resume_text, domain, num_questions)
            
            # Make API call with rate limiting
            questions_text = self._call_groq_api(prompt)
            
            # Process and clean questions
            questions = self._process_questions(questions_text, num_questions)
            
            # Save to cache
            self._save_to_cache(cache_key, questions)
            
            # Save the generated questions for reference
            self.save_analysis(
                "\n".join(questions),
                domain,
                f"generated_questions_{question_type}"
            )
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating {question_type} questions: {str(e)}", exc_info=True)
            return []
    
    def _create_technical_prompt(self, resume_text, domain, num_questions):
        """Create prompt for technical questions."""
        return f"""Generate {num_questions} in-depth technical interview questions for a {domain} position 
        based on the following resume. Focus on specific technologies, tools, and technical challenges:
        \n{resume_text[:6000]}\n\nFor each question, include:
1. A clear, specific technical question
2. The expected knowledge level (beginner/intermediate/advanced)
3. The technology or concept being tested

Questions:\n1."""
    
    def _create_behavioral_prompt(self, resume_text, domain, num_questions):
        """Create prompt for behavioral questions."""
        return f"""Generate {num_questions} behavioral interview questions for a {domain} position 
        based on the following resume. Focus on soft skills, teamwork, and problem-solving:
        \n{resume_text[:6000]}\n\nFor each question, include:
1. The behavioral competency being tested (e.g., leadership, conflict resolution)
2. Follow-up questions to probe deeper
3. What a strong answer might include

Questions:\n1."""
    
    def _create_project_prompt(self, projects, domain, num_questions):
        """Create prompt for project-specific questions."""
        projects_text = "\n\n".join(
            f"Project: {p.get('title', 'Untitled Project')}\n"
            f"Technologies: {', '.join(p.get('technologies', []))}\n"
            f"Description: {p.get('description', 'No description')}\n"
            f"Duration: {p.get('duration', 'N/A')}"
            for p in projects[:3]  # Limit to top 3 projects
        )
        
        return f"""Generate {num_questions} detailed technical questions about the following projects 
        for a {domain} position. For each project, ask about:
        1. Technical challenges and solutions
        2. Architecture and design decisions
        3. Technologies used and their purpose
        4. Impact and results achieved
        
        Projects:
        {projects_text}
        
        For each question, specify which project it refers to and what aspect it's testing.
        
        Questions:
        1."""
    
    def _process_questions(self, questions_text, max_questions):
        """Process and clean the raw questions text from the API response."""
        if not questions_text:
            return []
            
        # Split into individual questions
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        # Clean up each question
        cleaned_questions = []
        for q in questions:
            # Remove leading numbers and dots/bullets
            q = q.split('.', 1)[-1].strip() if '.' in q[:5] else q
            q = q.replace('•', '').strip()
            
            # Basic validation
            if q and not q.startswith(('Note:', 'For project', 'Project:')) and len(q) > 10:
                cleaned_questions.append(q)
        
        return cleaned_questions[:max_questions]
    
    def _create_experience_prompt(self, resume_text, domain, num_questions):
        """Create prompt for experience-based questions."""
        return f"""Generate {num_questions} experience-based interview questions for a {domain} position 
        based on the following work experiences. Focus on specific roles, responsibilities, and achievements:
        \n{resume_text[:6000]}\n\nFor each question, include:
1. The specific experience or role it relates to
2. What aspect of the experience is being probed
3. What makes a strong response

Questions:\n1."""
    
    def analyze_and_generate_questions(self, resume_text, domain, num_questions=5):
        """
        Perform complete analysis and generate different types of questions.
        
        Returns:
            dict: Dictionary containing different types of questions
        """
        # Save the original resume text
        self.save_analysis(resume_text, domain, 'resume')
        
        # Generate different types of questions
        questions = {
            'technical': self.generate_questions(resume_text, domain, num_questions, 'technical'),
            'behavioral': self.generate_questions(resume_text, domain, num_questions, 'behavioral'),
            'experience': self.generate_questions(resume_text, domain, num_questions, 'experience')
        }
        
        return questions
