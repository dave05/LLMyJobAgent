import spacy
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from numpy import ndarray
from job_agent.utils.resume_parser import ResumeParser
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

class AIResumeAnalyzer:
    def __init__(self):
        """Initialize the AI resume analyzer with NLP models"""
        try:
            # Load spaCy model for NLP tasks
            self.nlp = spacy.load("en_core_web_lg")
            
            # Load sentence transformer for semantic analysis
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize resume parser
            self.resume_parser = ResumeParser()
            
            # Add custom entity ruler for skills
            self.setup_skill_entity_ruler()
            
            logger.info("AI Resume Analyzer initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI Resume Analyzer: {str(e)}")
            raise
            
    def setup_skill_entity_ruler(self):
        """Set up custom entity ruler for skill extraction"""
        try:
            # Common technical skills patterns
            skill_patterns = [
                {"label": "SKILL", "pattern": [{"LOWER": {"IN": [
                    "python", "java", "javascript", "react", "angular", "vue", "node.js",
                    "sql", "nosql", "aws", "azure", "gcp", "docker", "kubernetes",
                    "machine learning", "data science", "artificial intelligence",
                    "web development", "mobile development", "backend", "frontend",
                    "full stack", "devops", "cloud computing", "cybersecurity"
                ]}}]},
                {"label": "SKILL", "pattern": [{"LOWER": {"REGEX": r"^[a-z]+\.(js|py|java|ts|go|rb)$"}}]},
                {"label": "SKILL", "pattern": [{"LOWER": {"REGEX": r"^[a-z]+-?[a-z]+$"}}]}
            ]
            
            # Add entity ruler to pipeline
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            ruler.add_patterns(skill_patterns)
            
        except Exception as e:
            logger.error(f"Error setting up skill entity ruler: {str(e)}")
            raise
            
    def extract_skills_with_context(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills from text with surrounding context"""
        try:
            doc = self.nlp(text)
            skills = []
            
            for ent in doc.ents:
                if ent.label_ == "SKILL":
                    # Get surrounding context (2 sentences before and after)
                    start_sent = max(0, ent.sent.start - 2)
                    end_sent = min(len(doc.sents), ent.sent.end + 2)
                    context = " ".join([sent.text for sent in list(doc.sents)[start_sent:end_sent]])
                    
                    skills.append({
                        "skill": ent.text,
                        "context": context,
                        "confidence": 1.0  # Can be enhanced with ML model confidence
                    })
                    
            return skills
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []
            
    def extract_experience_with_semantics(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience with semantic analysis"""
        try:
            doc = self.nlp(text)
            experiences = []
            
            # Find sentences containing work experience indicators
            work_indicators = ["worked", "experience", "role", "position", "job", "employed"]
            
            for sent in doc.sents:
                if any(indicator in sent.text.lower() for indicator in work_indicators):
                    # Extract role and company using dependency parsing
                    role = None
                    company = None
                    
                    for token in sent:
                        if token.dep_ == "nsubj" and token.pos_ == "NOUN":
                            role = token.text
                        elif token.dep_ == "pobj" and token.pos_ == "PROPN":
                            company = token.text
                            
                    if role and company:
                        # Encode description for semantic analysis
                        description_embedding = self.sentence_transformer.encode(sent.text)
                        
                        experiences.append({
                            "role": role,
                            "company": company,
                            "description": sent.text,
                            "embedding": description_embedding.tolist()
                        })
                        
            return experiences
            
        except Exception as e:
            logger.error(f"Error extracting experiences: {str(e)}")
            return []
            
    def generate_tailored_resume(self, resume_data: Dict[str, Any], job_description: str) -> str:
        """Generate a tailored resume based on job description"""
        try:
            # Encode job description
            job_embedding = self.sentence_transformer.encode(job_description)
            
            # Find most relevant experiences
            relevant_experiences = []
            for exp in resume_data['experiences']:
                exp_embedding = np.array(exp['embedding'])
                similarity = cosine_similarity(
                    job_embedding.reshape(1, -1),
                    exp_embedding.reshape(1, -1)
                )[0][0]
                
                if similarity > 0.7:  # Threshold for relevance
                    relevant_experiences.append(exp)
                    
            # Generate tailored resume
            tailored_resume = f"Professional Summary:\n"
            tailored_resume += f"Experienced {resume_data['skills'][0]['skill']} professional with expertise in "
            tailored_resume += ", ".join([skill['skill'] for skill in resume_data['skills'][:5]]) + ".\n\n"
            
            tailored_resume += "Relevant Experience:\n"
            for exp in relevant_experiences:
                tailored_resume += f"{exp['role']} at {exp['company']}\n"
                tailored_resume += f"- {exp['description']}\n\n"
                
            tailored_resume += "Skills:\n"
            tailored_resume += ", ".join([skill['skill'] for skill in resume_data['skills']])
            
            return tailored_resume
            
        except Exception as e:
            logger.error(f"Error generating tailored resume: {str(e)}")
            return ""
            
    def analyze(self, resume_path: str) -> Dict[str, Any]:
        """Analyze resume file and extract relevant information"""
        try:
            # Parse resume file
            resume_text = self.resume_parser.parse_resume(resume_path)
            if not resume_text:
                raise ValueError("Failed to parse resume file")
                
            # Extract sections
            sections = self.resume_parser.extract_sections(resume_text)
            
            # Extract skills with context
            skills = self.extract_skills_with_context(sections['skills'])
            
            # Extract work experience with semantic analysis
            experiences = self.extract_experience_with_semantics(sections['experience'])
            
            # Return structured resume data
            return {
                "skills": skills,
                "experiences": experiences,
                "sections": sections,
                "raw_text": resume_text
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            raise 