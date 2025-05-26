import os
import re
import logging
import json
from flask import current_app
from werkzeug.utils import secure_filename
import PyPDF2
import docx
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# Download NLTK resources if not already present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class ResumeParser:
    """Class to parse and extract structured data from resumes."""
    
    def __init__(self):
        """Initialize the resume parser with necessary resources."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Ensure debug logging is enabled
        self.cache = {}
        
        # Common project-related keywords to help identify project sections
        self.project_keywords = [
            'projects', 'project experience', 'personal projects',
            'academic projects', 'side projects', 'project work'
        ]
        
        # Common skills by domain with weights (1-3, higher is more important)
        self.skills_by_domain = {
            'Full Stack Developer': {
                'languages': {'javascript': 3, 'typescript': 3, 'python': 2, 'java': 2, 'c#': 2, 'php': 1},
                'frontend': {'react': 3, 'angular': 3, 'vue': 3, 'html': 3, 'css': 3, 'sass': 2, 'redux': 2},
                'backend': {'node': 3, 'express': 3, 'django': 3, 'flask': 2, 'spring': 2, 'ruby': 1, 'rails': 1},
                'databases': {'sql': 3, 'mongodb': 2, 'postgresql': 2, 'mysql': 2, 'redis': 1},
                'devops': {'docker': 2, 'kubernetes': 2, 'aws': 2, 'azure': 1, 'gcp': 1, 'ci/cd': 2},
                'tools': {'git': 3, 'github': 2, 'gitlab': 2, 'jira': 1, 'jenkins': 1}
            },
            'AI Engineer': {
                'languages': {'python': 3, 'r': 2, 'java': 1, 'c++': 1, 'julia': 1},
                'ml_frameworks': {'tensorflow': 3, 'pytorch': 3, 'keras': 2, 'scikit-learn': 3, 'mxnet': 1},
                'data_processing': {'pandas': 3, 'numpy': 3, 'scipy': 2, 'dask': 1, 'pyspark': 2},
                'ml_concepts': {
                    'machine learning': 3, 'deep learning': 3, 'neural networks': 3, 'nlp': 2, 
                    'computer vision': 2, 'reinforcement learning': 1, 'time series': 1
                },
                'tools': {'jupyter': 3, 'colab': 2, 'kaggle': 1, 'mlflow': 1, 'tensorboard': 1}
            },
            'Data Analyst': {
                'languages': {'sql': 3, 'python': 3, 'r': 2, 'sas': 1, 'matlab': 1},
                'data_processing': {'pandas': 3, 'numpy': 2, 'excel': 3, 'google sheets': 2},
                'viz_tools': {'tableau': 3, 'power bi': 3, 'matplotlib': 2, 'seaborn': 2, 'plotly': 2},
                'databases': {'sql': 3, 'bigquery': 2, 'snowflake': 2, 'redshift': 1, 'postgresql': 1},
                'statistics': {
                    'statistical analysis': 3, 'regression': 2, 'hypothesis testing': 2, 
                    'a/b testing': 2, 'predictive modeling': 1
                },
                'tools': {'looker': 2, 'mode': 1, 'airflow': 1, 'git': 1}
            }
        }
        
        # Education keywords
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'bsc', 'msc', 'degree', 'diploma',
            'university', 'college', 'institute', 'school', 'certification', 'certificate'
        ]
        
        # Experience keywords
        self.experience_keywords = [
            'experience', 'work', 'employment', 'job', 'position', 'role', 'career',
            'professional', 'responsibilities', 'duties', 'achievements'
        ]
        
        # Try to load spaCy model if available
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
            self.logger.warning("spaCy model not available. Some advanced parsing features will be disabled.")
    
    def analyze_skills(self, text, domain):
        """
        Analyze the resume text to extract and score skills based on the target domain.
        
        Args:
            text (str): The resume text to analyze
            domain (str): The target job domain
            
        Returns:
            dict: Dictionary of skill categories with matched skills and their scores
        """
        try:
            if not text or not isinstance(text, str):
                self.logger.warning("No text provided for skill analysis")
                return {}
                
            if not domain or domain not in self.skills_by_domain:
                self.logger.warning(f"Domain '{domain}' not found in skills database. Available domains: {list(self.skills_by_domain.keys())}")
                # Default to first available domain if the specified one is not found
                if not self.skills_by_domain:
                    return {}
                domain = next(iter(self.skills_by_domain))
                self.logger.info(f"Using default domain: {domain}")
                
            # Convert text to lowercase for case-insensitive matching
            text_lower = text.lower()
            domain_skills = self.skills_by_domain.get(domain, {})
            
            results = {}
            
            # Check each skill category
            for category, skills in domain_skills.items():
                try:
                    matched_skills = {}
                    for skill, weight in skills.items():
                        try:
                            if not skill or not isinstance(skill, str):
                                continue
                                
                            # Check for both the skill and common variations
                            variations = [skill]
                            # Add common variations (e.g., 'js' for 'javascript')
                            if skill == 'javascript':
                                variations.append('js')
                            elif skill == 'typescript':
                                variations.append('ts')
                            elif skill == 'c++':
                                variations.extend(['c++', 'cpp', 'c plus plus'])
                            elif skill == 'c#':
                                variations.extend(['c#', 'csharp'])
                                
                            # Check for any variation in the text
                            for variation in variations:
                                try:
                                    if re.search(r'\b' + re.escape(variation) + r'\b', text_lower):
                                        matched_skills[skill] = weight
                                        break
                                except re.error as re_err:
                                    self.logger.debug(f"Regex error for variation '{variation}': {str(re_err)}")
                                    continue
                                    
                        except Exception as skill_err:
                            self.logger.debug(f"Error processing skill '{skill}': {str(skill_err)}")
                            continue
                            
                    if matched_skills:
                        results[category] = matched_skills
                        
                except Exception as category_err:
                    self.logger.warning(f"Error processing category '{category}': {str(category_err)}")
                    continue
                    
            self.logger.debug(f"Found {sum(len(skills) for skills in results.values())} skills across {len(results)} categories")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in analyze_skills: {str(e)}", exc_info=True)
            return {}
    
    def extract_experience(self, text):
        """
        Extract work experience information from resume text.
        
        Args:
            text (str): The resume text
            
        Returns:
            list: List of work experience entries with company, title, and duration
        """
        if not text or not isinstance(text, str):
            self.logger.warning("No text provided for experience extraction")
            return []
            
        experiences = []
        
        try:
            # Multiple patterns to catch different resume formats
            experience_patterns = [
                # Pattern 1: Standard work experience section
                r'(?i)(?:(?:work|professional|employment)[\s\w]*experience|experience)[\s\-:]*\n(.*?)(?=\n\w|$|\n\n\w)',
                # Pattern 2: Job entries with dates
                r'(?i)(?:employment|work) history:?\n(.*?)(?=\n\w|$|\n\n\w)',
                # Pattern 3: Just look for job titles and companies if other patterns fail
                r'(?i)(?:\n|^)((?:[A-Z][\w\s\-&.,'']+?)\s*[\-–]\s*(?:\w+\s+){1,3}\s*\(?\d{4}\s*[\-–]\s*(?:Present|\d{4}|Current)\)?)(.*?)(?=\n\w|$|\n\n\w)'
            ]
            
            for pattern in experience_patterns:
                try:
                    matches = list(re.finditer(pattern, text, re.DOTALL))
                    if not matches:
                        continue
                        
                    for match in matches:
                        try:
                            experience_text = match.group(1).strip()
                            if not experience_text:
                                continue
                                
                            # Extract company, title, and dates using more flexible patterns
                            job_patterns = [
                                # Pattern 1: Company - Title (Date - Date)
                                r'(?i)([A-Z][\w\s\-&.,'']+?)\s*[\-–]\s*([^\n\-–]+?)\s*\(?([A-Za-z]+\s*\d{4})\s*[\-–]\s*([A-Za-z]+\s*\d{4}|Present|Current)\)?',
                                # Pattern 2: Title at Company (Date - Date)
                                r'(?i)([^\n\-–]+?)\s*at\s+([A-Z][\w\s\-&.,'']+?)\s*\(?([A-Za-z]+\s*\d{4})\s*[\-–]\s*([A-Za-z]+\s*\d{4}|Present|Current)\)?',
                                # Pattern 3: Just look for any date ranges that look like employment periods
                                r'(?i)([A-Z][\w\s\-&.,'']+?)\s*[\-–]\s*([^\n\-–]+?)\s*([A-Za-z]+\s*\d{4})\s*[\-–]\s*([A-Za-z]+\s*\d{4}|Present|Current)'
                            ]
                            
                            for job_pattern in job_patterns:
                                try:
                                    job_matches = list(re.finditer(job_pattern, experience_text, re.DOTALL))
                                    if job_matches:
                                        for m in job_matches:
                                            experiences.append({
                                                'company': m.group(1).strip(),
                                                'title': m.group(2).strip(),
                                                'start_date': m.group(3).strip(),
                                                'end_date': m.group(4).strip(),
                                                'description': experience_text[:500]  # Limit description length
                                            })
                                        break
                                except Exception as job_err:
                                    self.logger.debug(f"Error parsing job pattern: {str(job_err)}")
                                    continue
                                    
                        except Exception as match_err:
                            self.logger.debug(f"Error processing experience match: {str(match_err)}")
                            continue
                            
                except Exception as pattern_err:
                    self.logger.debug(f"Error with experience pattern {pattern}: {str(pattern_err)}")
                    continue
                    
            # If we couldn't extract structured data, at least return the raw text
            if not experiences and len(text) > 50:
                experiences.append({
                    'company': 'Not specified',
                    'title': 'Work Experience',
                    'start_date': 'N/A',
                    'end_date': 'Present',
                    'description': 'Work experience details could not be parsed. Please review the resume content.'
                })
                
        except Exception as e:
            self.logger.error(f"Error in extract_experience: {str(e)}", exc_info=True)
            
        self.logger.info(f"Extracted {len(experiences)} experience entries")
        return experiences
    
    def extract_projects(self, text):
        """
        Extract project information from resume text.
        
        Args:
            text (str): The resume text to analyze
            
        Returns:
            list: List of dictionaries containing project details
        """
        try:
            self.logger.info("Starting project extraction from resume")
            projects = []
            
            # First, try to find projects section
            projects_text = self._extract_section(text, self.project_keywords)
            
            if not projects_text:
                self.logger.warning("No projects section found in resume")
                return []
                
            # Split into individual projects
            project_entries = self._split_into_projects(projects_text)
            
            for entry in project_entries:
                project = {
                    'title': self._extract_project_title(entry),
                    'duration': self._extract_duration(entry),
                    'technologies': self._extract_technologies(entry),
                    'responsibilities': self._extract_responsibilities(entry),
                    'description': entry.strip()
                }
                projects.append(project)
                
            self.logger.info(f"Extracted {len(projects)} projects from resume")
            return projects
            
        except Exception as e:
            self.logger.error(f"Error extracting projects: {str(e)}", exc_info=True)
            return []
    
    def _extract_section(self, text, possible_headers):
        """Extract a specific section from the resume text."""
        text_lower = text.lower()
        
        for header in possible_headers:
            header_lower = header.lower()
            if header_lower in text_lower:
                # Find the start of the section
                start_idx = text_lower.find(header_lower) + len(header_lower)
                
                # Find the end of the section (next major section)
                section_end = len(text)
                for next_header in ['\n\n', '\n•', '\n-', '\n*']:
                    next_idx = text.find(next_header, start_idx)
                    if 0 < next_idx < section_end:
                        section_end = next_idx
                
                return text[start_idx:section_end].strip()
        
        return ""
    
    def _split_into_projects(self, projects_text):
        """Split projects text into individual project entries."""
        # Common project separators
        separators = ['\n•', '\n-', '\n*', '\n~', '\n']
        
        for sep in separators:
            if sep in projects_text:
                return [p.strip() for p in projects_text.split(sep) if p.strip()]
                
        return [projects_text]
    
    def _extract_project_title(self, project_text):
        """Extract project title from project text."""
        # First non-empty line is often the title
        lines = [line.strip() for line in project_text.split('\n') if line.strip()]
        return lines[0] if lines else "Untitled Project"
    
    def _extract_duration(self, project_text):
        """Extract project duration if available."""
        # Look for date patterns like (MM/YYYY - MM/YYYY) or (YYYY - YYYY)
        import re
        date_pattern = r'\((?:\d{1,2}[/-])?(?:\d{4}|\d{2})\s*[-–—]\s*(?:\d{1,2}[/-])?(?:\d{4}|\d{2}|present|current|now)\)|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4} (?:to|-) (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}\b'
        match = re.search(date_pattern, project_text, re.IGNORECASE)
        return match.group(0) if match else ""
    
    def _extract_technologies(self, project_text):
        """Extract technologies used in the project."""
        # Common technology keywords to look for
        tech_keywords = [
            'python', 'java', 'javascript', 'react', 'node', 'django', 'flask',
            'sql', 'mongodb', 'aws', 'docker', 'kubernetes', 'git', 'github',
            'machine learning', 'ai', 'data analysis', 'web development', 'api'
        ]
        
        return [tech for tech in tech_keywords if tech in project_text.lower()]
    
    def _extract_responsibilities(self, project_text):
        """Extract key responsibilities/achievements from project text."""
        # Look for bullet points or key achievements
        lines = [line.strip() for line in project_text.split('\n') if line.strip()]
        
        # Skip the first line (title) and filter out lines that are too short
        return [line for line in lines[1:] if len(line) > 20]
    
    def analyze_resume_for_interview(self, text, domain):
        """
        Analyze resume text and prepare data for interview question generation.
        
        Args:
            text (str): The resume text to analyze
            domain (str): The job domain (e.g., 'Full Stack Developer')
            
        Returns:
            dict: Analysis results including skills, experience, and AI-generated questions
        """
        try:
            if not text or not text.strip():
                error_msg = "Empty or invalid resume text provided"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            self.logger.info(f"Starting resume analysis for domain: {domain}")
            self.logger.debug(f"Resume text length: {len(text)} characters")
            self.logger.debug(f"First 200 chars: {text[:200]}...")
                
            # First, save the resume text for AI processing
            try:
                from app.services.ai_question_generator import AIQuestionGenerator
                self.logger.info("Initializing AIQuestionGenerator...")
                ai_generator = AIQuestionGenerator()
                
                # Save the original resume text
                self.logger.info("Saving resume analysis...")
                saved_path = ai_generator.save_analysis(text, domain, 'resume')
                if saved_path:
                    self.logger.info(f"Successfully saved resume analysis to: {saved_path}")
                else:
                    self.logger.warning("Failed to save resume analysis")
                    
            except Exception as e:
                self.logger.error(f"Error initializing AIQuestionGenerator: {str(e)}", exc_info=True)
                raise
            
            # Generate AI-powered questions
            self.logger.info("Generating AI-powered questions...")
            try:
                ai_questions = ai_generator.analyze_and_generate_questions(text, domain)
                
                if not ai_questions:
                    self.logger.warning("No AI questions were generated")
                else:
                    question_counts = {k: len(v) for k, v in ai_questions.items() if v}  # Only count non-empty lists
                    self.logger.info(f"Generated AI questions: {question_counts}")
                    
                    # Log a sample of the generated questions for debugging
                    for q_type, questions in ai_questions.items():
                        if questions and len(questions) > 0:
                            self.logger.debug(f"Sample {q_type} question: {questions[0]}")
                            
            except Exception as e:
                self.logger.error(f"Error generating AI questions: {str(e)}", exc_info=True)
                ai_questions = {}
            
            # Traditional analysis (keep for fallback)
            skills_analysis = self.analyze_skills(text, domain)
            self.logger.info(f"Skills analysis completed. Found {len(skills_analysis)} skill categories.")
            
            # Extract experience
            self.logger.info("Extracting experience...")
            experience = self.extract_experience(text)
            self.logger.info(f"Extracted {len(experience)} experience entries.")
            
            # Extract projects
            self.logger.info("Extracting projects...")
            projects = self.extract_projects(text)
            self.logger.info(f"Extracted {len(projects)} projects.")
            
            result = {
                'skills_analysis': skills_analysis,
                'experience': experience,
                'projects': projects,
                'domain': domain,
                'ai_questions': ai_questions  # Include the AI-generated questions
            }
            
            self.logger.info("Resume analysis completed successfully.")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in analyze_resume_for_interview: {str(e)}", exc_info=True)
            # Return empty but valid structure to prevent downstream errors
            return {
                'skills_analysis': {},
                'experience': [],
                'domain': domain or 'Unknown',
                'ai_questions': {},  # Ensure ai_questions is always in the response
                'error': str(e)
            }
    
    def parse_resume(self, file_path):
        """
        Parse a resume file and extract structured information.
        
        Args:
            file_path (str): Path to the resume file
            
        Returns:
            dict: Structured resume data
        """
        try:
            # Extract text from file based on file type
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                text = self._extract_text_from_pdf(file_path)
            elif file_ext in ['.doc', '.docx']:
                text = self._extract_text_from_docx(file_path)
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Process and structure the extracted text
            resume_data = self._process_resume_text(text)
            
            # Add file metadata
            resume_data['file_info'] = {
                'filename': os.path.basename(file_path),
                'file_type': file_ext.replace('.', ''),
                'file_size': os.path.getsize(file_path)
            }
            
            return resume_data
            
        except Exception as e:
            self.logger.error(f"Error parsing resume: {str(e)}")
            return {
                'error': str(e),
                'file_info': {
                    'filename': os.path.basename(file_path),
                    'file_type': os.path.splitext(file_path)[1].lower().replace('.', ''),
                    'file_size': os.path.getsize(file_path)
                }
            }
    
    def _extract_text_from_pdf(self, file_path):
        """Extract text from a PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
        return text
    
    def _extract_text_from_docx(self, file_path):
        """Extract text from a DOCX file."""
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            self.logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
        return text
    
    def _process_resume_text(self, text):
        """Process and structure the extracted resume text."""
        # Initialize structured data
        resume_data = {
            'personal_info': {},
            'skills': [],
            'education': [],
            'experience': [],
            'projects': [],
            'summary': "",
            'detected_domain': None,
            'domain_confidence': 0.0
        }
        
        # Clean and normalize text
        text = self._preprocess_text(text)
        
        # Extract contact information
        resume_data['personal_info'] = self._extract_contact_info(text)
        
        # Extract skills
        resume_data['skills'] = self._extract_skills(text)
        
        # Detect domain based on skills
        domain_scores = self._detect_domain(resume_data['skills'])
        if domain_scores:
            top_domain = max(domain_scores.items(), key=lambda x: x[1])
            resume_data['detected_domain'] = top_domain[0]
            resume_data['domain_confidence'] = top_domain[1]
        
        # Extract education
        resume_data['education'] = self._extract_education(text)
        
        # Extract experience
        resume_data['experience'] = self._extract_experience(text)
        
        # Extract or generate summary
        resume_data['summary'] = self._extract_summary(text)
        
        # Extract years of experience
        resume_data['years_of_experience'] = self._estimate_years_of_experience(resume_data['experience'])
        
        return resume_data
    
    def _preprocess_text(self, text):
        """Clean and normalize the text."""
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters and normalize
        text = re.sub(r'[^\w\s@.:;,\/\(\)\-]', '', text)
        
        return text.strip()
    
    def _extract_contact_info(self, text):
        """Extract contact information from the text."""
        contact_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            contact_info['email'] = email_matches[0]
        
        # Extract phone
        phone_pattern = r'\b(?:\+\d{1,3}[-\.\s]?)?(?:\(?\d{3}\)?[-\.\s]?)?(?:\d{3})[-\.\s]?(?:\d{4})\b'
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
        
        # Extract LinkedIn
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=)([a-zA-Z0-9_-]+)'
        linkedin_matches = re.findall(linkedin_pattern, text.lower())
        if linkedin_matches:
            contact_info['linkedin'] = linkedin_matches[0]
        
        return contact_info
    
    def _extract_skills(self, text):
        """Extract skills from the text."""
        skills = []
        
        # Flatten skills from all domains
        all_skills = []
        for domain_skills in self.skills_by_domain.values():
            all_skills.extend(domain_skills)
        
        # Remove duplicates
        all_skills = list(set(all_skills))
        
        # Extract skills using pattern matching
        text_lower = text.lower()
        for skill in all_skills:
            # Use word boundaries to ensure we're matching whole words
            skill_pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(skill_pattern, text_lower):
                skills.append(skill)
        
        return skills
    
    def _detect_domain(self, skills):
        """Detect the most likely domain based on detected skills."""
        if not skills:
            return {}
        
        domain_scores = {}
        
        for domain, domain_skills in self.skills_by_domain.items():
            # Count how many skills match this domain
            matches = [skill for skill in skills if skill.lower() in [ds.lower() for ds in domain_skills]]
            
            # Calculate a confidence score
            if len(domain_skills) > 0:
                score = len(matches) / len(domain_skills)
                domain_scores[domain] = score
        
        return domain_scores
    
    def _extract_education(self, text):
        """Extract education information from the text."""
        education = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Look for education section
        in_education_section = False
        education_section_text = ""
        
        # Keywords that might indicate the start of an education section
        education_section_starters = ['education', 'academic background', 'qualifications']
        
        # Keywords that might indicate the end of an education section
        section_enders = ['experience', 'employment', 'work history', 'skills', 'projects']
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're entering the education section
            if any(starter in line_lower for starter in education_section_starters):
                in_education_section = True
                continue
            
            # Check if we're leaving the education section
            if in_education_section and any(ender in line_lower for ender in section_enders):
                in_education_section = False
                break
                
            # Add line to education section text if we're in the section
            if in_education_section and line.strip():
                education_section_text += line + "\n"
        
        # If no clear education section was found, try to extract based on keywords
        if not education_section_text:
            education_section_text = text
        
        # Look for common degree patterns
        degree_patterns = [
            r'\b(?:Bachelor|Master|PhD|Doctorate|BSc|MSc|MBA|B\.A\.|M\.A\.|B\.S\.|M\.S\.)\b[^,;.]*(?:of|in)[^,;.]*',
            r'\b(?:University|College|Institute)[^,;.]*',
            r'\b(?:Degree|Diploma)[^,;.]*'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, education_section_text, re.IGNORECASE)
            for match in matches:
                # Check if this is likely a degree (not already found)
                if match.strip() and not any(match.strip() in edu for edu in education):
                    # Try to extract year
                    year_match = re.search(r'\b(19|20)\d{2}\b', match)
                    year = year_match.group(0) if year_match else None
                    
                    education.append({
                        'degree': match.strip(),
                        'year': year
                    })
        
        return education
    
    def _extract_experience(self, text):
        """Extract work experience information from the text."""
        experience = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Look for experience section
        in_experience_section = False
        experience_section_text = ""
        
        # Keywords that might indicate the start of an experience section
        experience_section_starters = ['experience', 'employment', 'work history', 'professional background']
        
        # Keywords that might indicate the end of an experience section
        section_enders = ['education', 'skills', 'projects', 'certifications', 'interests']
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're entering the experience section
            if any(starter in line_lower for starter in experience_section_starters):
                in_experience_section = True
                continue
            
            # Check if we're leaving the experience section
            if in_experience_section and any(ender in line_lower for ender in section_enders):
                in_experience_section = False
                break
                
            # Add line to experience section text if we're in the section
            if in_experience_section and line.strip():
                experience_section_text += line + "\n"
        
        # If no clear experience section was found, try to extract based on keywords
        if not experience_section_text:
            experience_section_text = text
        
        # Look for common job title and company patterns
        job_patterns = [
            r'\b(?:Senior|Junior|Lead|Principal)?\s*(?:Software|Web|Frontend|Backend|Full Stack|Data|Machine Learning|AI)?\s*(?:Engineer|Developer|Architect|Scientist|Analyst|Designer)\b[^,;.]*(?:at|for)?\s*[^,;.]*',
            r'\b(?:Company|Corporation|Inc\.|LLC|Ltd\.)[^,;.]*',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[^,;.]*\d{4}[^,;.]*(?:to|–|-)?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[^,;.]*\d{0,4}[^,;.]*'
        ]
        
        # Extract potential job entries
        job_entries = []
        for pattern in job_patterns:
            matches = re.findall(pattern, experience_section_text, re.IGNORECASE)
            job_entries.extend([match.strip() for match in matches if match.strip()])
        
        # Process job entries to extract structured data
        for entry in job_entries:
            # Try to extract dates
            date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[^,;.]*\d{4}[^,;.]*(?:to|–|-)?\s*(?:Present|Current|Now|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[^,;.]*\d{0,4}[^,;.]*'
            date_match = re.search(date_pattern, entry, re.IGNORECASE)
            dates = date_match.group(0).strip() if date_match else None
            
            # Try to extract title and company
            title_company = entry
            if dates:
                title_company = entry.replace(dates, '').strip()
            
            # Add to experience list if we have something meaningful
            if title_company and len(title_company) > 5:
                experience.append({
                    'title_company': title_company,
                    'dates': dates
                })
        
        return experience
    
    def _extract_summary(self, text):
        """Extract or generate a summary from the resume text."""
        # Try to find a summary section
        summary_pattern = r'(?:Summary|Profile|About|Objective)[:\s]*(.*?)(?=\n\n|\Z)'
        summary_match = re.search(summary_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if summary_match:
            summary = summary_match.group(1).strip()
            # Limit summary length
            if len(summary) > 500:
                summary = summary[:497] + '...'
            return summary
        
        # If no summary found, use the first paragraph
        paragraphs = text.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 30:  # Ensure it's substantial
                if len(first_para) > 500:
                    first_para = first_para[:497] + '...'
                return first_para
        
        return "No summary available."
    
    def _estimate_years_of_experience(self, experience_entries):
        """Estimate total years of experience from experience entries."""
        total_years = 0
        
        for entry in experience_entries:
            dates = entry.get('dates', '')
            if not dates:
                continue
                
            # Try to extract years
            years_pattern = r'(\d{4})\s*(?:to|–|-)\s*(?:Present|Current|Now|(\d{4}))?'
            years_match = re.search(years_pattern, dates, re.IGNORECASE)
            
            if years_match:
                start_year = int(years_match.group(1))
                end_year = int(years_match.group(2)) if years_match.group(2) else datetime.now().year
                
                # Add years to total
                years_in_role = end_year - start_year
                if years_in_role > 0 and years_in_role < 30:  # Sanity check
                    total_years += years_in_role
        
        return total_years

# Function to parse a resume file
def parse_resume(file_path):
    """
    Parse a resume file and extract structured information.
    
    Args:
        file_path (str): Path to the resume file
        
    Returns:
        dict: Structured resume data
    """
    parser = ResumeParser()
    return parser.parse_resume(file_path)
