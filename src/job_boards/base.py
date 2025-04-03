import os
import logging
import random
import time
import json
from typing import Dict, List
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import spacy
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from utils.password_manager import PasswordManager

logger = logging.getLogger(__name__)

class BaseJobBoard(ABC):
    def __init__(self):
        """Initialize base job board with common functionality"""
        self.driver = None
        self.min_match_score = float(os.getenv('MIN_MATCH_SCORE', 0.7))
        self.password_manager = PasswordManager()
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
        if not all([self.email_username, self.email_password, self.notification_email]):
            logger.warning("Missing email configuration. Email notifications will not be sent.")
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            
        # Applications file path
        self.applications_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'applications.json')
    
    def _ensure_applications_file_exists(self):
        """Ensure the applications tracking file exists."""
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.dirname(self.applications_file)
            os.makedirs(data_dir, exist_ok=True)
            
            # Create applications file if it doesn't exist
            if not os.path.exists(self.applications_file):
                with open(self.applications_file, 'w') as f:
                    json.dump([], f)
                logger.info(f"Created applications file at {self.applications_file}")
            
        except Exception as e:
            logger.error(f"Error ensuring applications file exists: {str(e)}")
    
    def _extract_keywords(self, resume_data: Dict) -> List[str]:
        """Extract relevant keywords from resume data"""
        keywords = []
        
        # Add skills
        if 'skills' in resume_data:
            keywords.extend(resume_data['skills'][:5])  # Top 5 skills
            
        # Add experience keywords from latest experience
        if 'experience' in resume_data and resume_data['experience']:
            latest_exp = resume_data['experience'][0]  # Get most recent experience
            doc = self.nlp(latest_exp)
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2:
                    keywords.append(token.text)
                    
        # Clean and deduplicate keywords
        keywords = list(set([k.strip().lower() for k in keywords if k.strip()]))
        return keywords[:5]  # Return top 5 keywords
    
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add a random delay with microsecond precision"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _human_type(self, element, text: str):
        """Simulate human typing with variable delays"""
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes (50-200ms)
            time.sleep(random.uniform(0.05, 0.2))
            # 5% chance of a longer pause (0.5-1s)
            if random.random() < 0.05:
                time.sleep(random.uniform(0.5, 1.0))
    
    def _human_click(self, element):
        """Simulate human-like clicking behavior"""
        try:
            # Move mouse to random position within element
            action = webdriver.ActionChains(self.driver)
            action.move_to_element_with_offset(
                element,
                random.randint(-10, 10),
                random.randint(-10, 10)
            )
            # Random delay before clicking (100-300ms)
            time.sleep(random.uniform(0.1, 0.3))
            action.click()
            action.perform()
        except Exception as e:
            logger.warning(f"Error in human click: {str(e)}")
            # Fallback to regular click
            element.click()
    
    def setup_driver(self):
        """Set up Chrome WebDriver with anti-detection measures"""
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Set window size randomly
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        self.driver.set_window_size(width, height)
        
        # Execute stealth JavaScript
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
    
    @abstractmethod
    def search_jobs(self, job_title: str, location: str, resume_data: Dict) -> List[Dict]:
        """Search for jobs and return matching results"""
        pass
    
    def _calculate_match_score(self, job: Dict, resume_data: Dict) -> float:
        """Calculate match score between job and resume"""
        try:
            # Get job description text
            job_text = f"{job['title']} {job['description']}"
            
            # Get resume text (focus on latest experience)
            resume_text = ""
            if resume_data.get('experience'):
                resume_text = resume_data['experience'][0]  # Most recent experience
            if resume_data.get('skills'):
                resume_text += " " + " ".join(resume_data['skills'])
            
            # Process texts with NLP
            job_doc = self.nlp(job_text.lower())
            resume_doc = self.nlp(resume_text.lower())
            
            # Calculate similarity score
            similarity = job_doc.similarity(resume_doc)
            
            # Boost score if job title matches desired title
            job_title = job['title'].lower()
            desired_title = os.getenv('JOB_TITLE', '').lower()
            if desired_title in job_title:
                similarity += 0.2
            
            # Cap score at 1.0
            return min(similarity, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating match score: {str(e)}")
            return 0.0
    
    def _send_job_matches_email(self, jobs: List[Dict], source: str = None):
        """Send email with job matches"""
        if not all([self.email_username, self.email_password, self.notification_email]):
            logger.error("Cannot send email: Missing email configuration")
            return
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = self.notification_email
            msg['Subject'] = f"Top {source if source else ''} Job Matches - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create HTML content
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f8f9fa; color: #495057; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .match-score {{ color: #28a745; font-weight: bold; }}
                    .job-title {{ color: #007bff; font-weight: bold; }}
                    .company {{ color: #6c757d; }}
                </style>
            </head>
            <body>
                <h2>Top Job Matches{f' from {source}' if source else ''}</h2>
                <table>
                    <tr>
                        <th>Title</th>
                        <th>Company</th>
                        <th>Location</th>
                        <th>Match Score</th>
                        <th>Link</th>
                    </tr>
            """
            
            for job in jobs:
                html += f"""
                    <tr>
                        <td class="job-title">{job['title']}</td>
                        <td class="company">{job['company']}</td>
                        <td>{job['location']}</td>
                        <td class="match-score">{job['match_score']:.0%}</td>
                        <td><a href="{job['url']}">Apply</a></td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
                
            logger.info("Job matches email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending job matches email: {str(e)}")

    def _send_job_links_email(self, jobs: List[Dict], source: str = None):
        """Send email with job links only"""
        if not all([self.email_username, self.email_password, self.notification_email]):
            logger.error("Cannot send email: Missing email configuration")
            return
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = self.notification_email
            msg['Subject'] = f"Job Links from {source if source else ''} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create HTML content
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ margin: 10px 0; padding: 10px; border-bottom: 1px solid #eee; }}
                    a {{ color: #007bff; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h2>Job Links{f' from {source}' if source else ''}</h2>
                <ul>
            """
            
            for job in jobs:
                html += f"""
                    <li>
                        <a href="{job['url']}">{job.get('title', 'View Job')} at {job.get('company', '')}</a>
                        {f"<br>{job.get('location', '')}" if job.get('location') else ''}
                    </li>
                """
            
            html += """
                </ul>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
                
            logger.info("Job links email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending job links email: {str(e)}")

    def track_application(self, job: Dict) -> bool:
        """Track a job application."""
        try:
            # Create applications directory if it doesn't exist
            os.makedirs("data/applications", exist_ok=True)
            
            # Load existing applications
            applications_file = f"data/applications/{self.__class__.__name__.lower()}_applications.json"
            if os.path.exists(applications_file):
                try:
                    with open(applications_file, "r") as f:
                        applications = json.load(f)
                except json.JSONDecodeError:
                    applications = []
            else:
                applications = []
            
            # Check if job was already applied to
            if any(app["id"] == job["id"] for app in applications):
                self.logger.warning(f"Job {job['id']} was already applied to")
                return False
            
            # Check daily application limit
            max_applications = int(os.getenv("MAX_APPLICATIONS_PER_DAY", 10))
            today = datetime.now().date()
            today_applications = [app for app in applications if datetime.fromisoformat(app["date"]).date() == today]
            
            if len(today_applications) >= max_applications:
                self.logger.warning(f"Daily application limit of {max_applications} reached")
                return False
            
            # Add new application
            application = {
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "url": job["url"],
                "date": datetime.now().isoformat(),
                "status": "applied"
            }
            applications.append(application)
            
            # Save applications
            with open(applications_file, "w") as f:
                json.dump(applications, f, indent=2)
            
            self.logger.info(f"Tracked application for {job['title']} at {job['company']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error tracking application: {str(e)}")
            return False
    
    def get_applications(self, days: int = None) -> List[Dict]:
        """Get tracked applications, optionally filtered by days"""
        try:
            # Get job board specific applications file
            applications_file = f"data/applications/{self.__class__.__name__.lower()}_applications.json"
            
            if not os.path.exists(applications_file):
                return []
            
            # Load applications
            with open(applications_file, 'r') as f:
                applications = json.load(f)
            
            if days is not None:
                # Filter applications by date range
                cutoff_date = (datetime.now() - timedelta(days=days)).date()
                applications = [
                    app for app in applications 
                    if datetime.fromisoformat(app['date']).date() >= cutoff_date
                ]
            
            return applications
            
        except Exception as e:
            logger.error(f"Error getting applications: {str(e)}")
            return [] 