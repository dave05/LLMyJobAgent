import os
import logging
import re
from typing import Dict, List, Tuple
import PyPDF2
import spacy
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        """Initialize resume parser with NLP model"""
        load_dotenv()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            
    def parse_resume(self, resume_path: str) -> Dict:
        """
        Parse resume and extract relevant information
        
        Args:
            resume_path: Path to the resume file
            
        Returns:
            Dictionary containing parsed resume information
        """
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(resume_path)
            
            # Process text with NLP
            doc = self.nlp(text)
            
            # Extract information
            resume_data = {
                'name': self._extract_name(doc),
                'email': self._extract_email(text),
                'phone': self._extract_phone(text),
                'skills': self._extract_skills(doc),
                'experience': self._extract_experience(doc),
                'education': self._extract_education(doc),
                'keywords': self._extract_keywords(doc),
                'entities': self._extract_entities(doc),
                'text': text
            }
            
            logger.info("Successfully parsed resume")
            return resume_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise
            
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
            
    def _extract_name(self, doc) -> str:
        """Extract name from resume"""
        try:
            # Look for name pattern (usually at the beginning)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text
            return ""
        except Exception as e:
            logger.error(f"Error extracting name: {str(e)}")
            return ""
            
    def _extract_email(self, text: str) -> str:
        """Extract email from resume"""
        try:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            match = re.search(email_pattern, text)
            return match.group(0) if match else ""
        except Exception as e:
            logger.error(f"Error extracting email: {str(e)}")
            return ""
            
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume"""
        try:
            phone_pattern = r'\+?1?\s*\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}'
            match = re.search(phone_pattern, text)
            return match.group(0) if match else ""
        except Exception as e:
            logger.error(f"Error extracting phone: {str(e)}")
            return ""
            
    def _extract_skills(self, doc) -> List[str]:
        """Extract skills from resume"""
        try:
            skills = []
            skill_keywords = ['skill', 'expertise', 'proficient', 'experience', 'knowledge']
            
            for sent in doc.sents:
                if any(keyword in sent.text.lower() for keyword in skill_keywords):
                    for token in sent:
                        if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2:
                            skills.append(token.text)
                            
            return list(set(skills))
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []
            
    def _extract_experience(self, doc) -> List[str]:
        """Extract work experience from resume"""
        try:
            experience = []
            exp_keywords = ['experience', 'work', 'job', 'role', 'position']
            
            for sent in doc.sents:
                if any(keyword in sent.text.lower() for keyword in exp_keywords):
                    experience.append(sent.text.strip())
                    
            return experience
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}")
            return []
            
    def _extract_education(self, doc) -> List[str]:
        """Extract education information from resume"""
        try:
            education = []
            edu_keywords = ['education', 'degree', 'university', 'college', 'school']
            
            for sent in doc.sents:
                if any(keyword in sent.text.lower() for keyword in edu_keywords):
                    education.append(sent.text.strip())
                    
            return education
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
            return []
            
    def _extract_keywords(self, doc) -> List[str]:
        """Extract important keywords from resume"""
        try:
            keywords = []
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN', 'VERB'] and len(token.text) > 2:
                    keywords.append(token.text.lower())
            return list(set(keywords))
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
            
    def _extract_entities(self, doc) -> List[Tuple[str, str]]:
        """Extract named entities from resume"""
        try:
            entities = []
            for ent in doc.ents:
                entities.append((ent.text, ent.label_))
            return entities
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return [] 