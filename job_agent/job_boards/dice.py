import os
import logging
import time
import random
import re
from typing import Dict, List, Optional, Tuple, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from job_agent.utils.password_manager import PasswordManager
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import difflib
import spacy
from .base import BaseJobBoard
import uuid

logger = logging.getLogger(__name__)

class DiceJobBoard(BaseJobBoard):
    def __init__(self, password_manager=None):
        """Initialize Dice job board"""
        super().__init__()
        self.base_url = "https://www.dice.com"
        self.driver = None
        self.setup_driver()
        self.password_manager = password_manager or PasswordManager()
        self.applications_file = "data/applications.json"
        self._ensure_applications_file()
        self.max_applications_per_day = int(os.getenv('MAX_APPLICATIONS_PER_DAY', 10))
        self.min_match_score = float(os.getenv('MIN_MATCH_SCORE', 0.7))
        self.nlp = spacy.load("en_core_web_sm")
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        try:
            options = Options()
            # Temporarily disable headless mode for testing
            # options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Set up ChromeDriver using webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Override navigator.webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set a random user agent
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
            self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{random.choice(user_agents)}'}})")
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            raise
            
    def _random_delay(self, min_seconds: int, max_seconds: int):
        """Add a random delay between actions to avoid detection"""
        time.sleep(min_seconds + (max_seconds - min_seconds) * random.random())
        
    def _human_type(self, element, text):
        """Simulate human typing with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
            
    def _human_click(self, element):
        """Simulate a human-like click"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self._random_delay(1, 2)
        element.click()
        
    def _ensure_applications_file(self):
        """Ensure the applications tracking file exists"""
        os.makedirs(os.path.dirname(self.applications_file), exist_ok=True)
        if not os.path.exists(self.applications_file):
            with open(self.applications_file, 'w') as f:
                json.dump([], f)
                
    def _load_applications(self) -> List[Dict]:
        """Load tracked applications from file"""
        try:
            with open(self.applications_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading applications: {str(e)}")
            return []
            
    def _save_application(self, application: Dict):
        """Save application to tracking file"""
        try:
            applications = self._load_applications()
            applications.append(application)
            with open(self.applications_file, 'w') as f:
                json.dump(applications, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving application: {str(e)}")
            
    def _calculate_match_score(self, job: Dict, resume_data: Dict) -> float:
        """Calculate how well the job matches the resume"""
        try:
            # Extract keywords from job description
            job_keywords = set(re.findall(r'\b\w+\b', job['description'].lower()))
            
            # Get resume keywords from latest experience
            resume_keywords = set()
            if 'experience' in resume_data and resume_data['experience']:
                latest_exp = resume_data['experience'][0]  # Get most recent experience
                resume_keywords.update(re.findall(r'\b\w+\b', latest_exp.lower()))
            
            # Add skills to keywords
            if 'skills' in resume_data:
                resume_keywords.update(k.lower() for k in resume_data['skills'])
                    
            # Calculate similarity
            if not job_keywords or not resume_keywords:
                return 0.0
                
            # Use sequence matcher for better matching
            matcher = difflib.SequenceMatcher(None, 
                                            ' '.join(sorted(job_keywords)),
                                            ' '.join(sorted(resume_keywords)))
            return matcher.ratio()
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return 0.0
            
    def _send_job_matches_email(self, jobs: List[Dict], resume_data: Dict):
        """Send email with top job matches"""
        try:
            msg = MIMEMultipart()
            msg['From'] = os.getenv('EMAIL_USERNAME')
            msg['To'] = os.getenv('NOTIFICATION_EMAIL')
            msg['Subject'] = f"Top Dice Job Matches - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            body = f"""
            <html>
                <body>
                    <h2>Top Dice Job Matches</h2>
                    <p>Here are the top job matches based on your experience:</p>
                    <ul>
            """
            
            for job in jobs:
                body += f"""
                    <li>
                        <strong>{job['title']}</strong> at {job['company']}<br>
                        Location: {job['location']}<br>
                        Match Score: {job['match_score']:.2%}<br>
                        <a href="{job['url']}">View Job</a>
                    </li>
                """
            
            body += """
                    </ul>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
            server.starttls()
            server.login(os.getenv('EMAIL_USERNAME'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
            server.quit()
            
            logger.info("Successfully sent job matches email")
            
        except Exception as e:
            logger.error(f"Error sending job matches email: {str(e)}")
            
    def search_jobs(self, job_title: str, location: str, resume_data: Dict[str, str]) -> List[Dict]:
        """Search for jobs on Dice"""
        try:
            # Set up WebDriver
            driver = self._setup_driver()
            
            # Construct search URL
            search_url = f"https://www.dice.com/jobs?q={job_title}&l={location}"
            driver.get(search_url)
            
            # Wait for job list to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-results"))
                )
            except TimeoutException:
                self.logger.warning("Job list not found")
                return []
            
            # Extract job details
            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.search-card")
            self.logger.info(f"Found {len(job_cards)} job cards on Dice")
            
            jobs = []
            for card in job_cards:
                try:
                    # Extract job details
                    title = card.find_element(By.CSS_SELECTOR, "a.card-title-link").text
                    company = card.find_element(By.CSS_SELECTOR, "a.ng-star-inserted").text
                    location = card.find_element(By.CSS_SELECTOR, "span.job-location").text
                    url = card.find_element(By.CSS_SELECTOR, "a.card-title-link").get_attribute("href")
                    
                    # Click on job to get description
                    card.find_element(By.CSS_SELECTOR, "a.card-title-link").click()
                    time.sleep(2)  # Wait for description to load
                    
                    try:
                        description = driver.find_element(By.CSS_SELECTOR, "div.description").text
                    except:
                        description = ""
                    
                    # Calculate match score
                    match_score = self._calculate_match_score({
                        'title': title,
                        'description': description,
                        'company': company,
                        'location': location
                    }, resume_data)
                    
                    jobs.append({
                        'id': str(uuid.uuid4()),
                        'title': title,
                        'company': company,
                        'location': location,
                        'url': url,
                        'description': description,
                        'match_score': match_score
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error extracting job details: {str(e)}")
                    continue
            
            # Filter jobs by match score
            jobs = [job for job in jobs if job['match_score'] >= self.min_match_score]
            
            # Sort by match score and limit to top 5
            jobs.sort(key=lambda x: x['match_score'], reverse=True)
            jobs = jobs[:5]
            
            self.logger.info(f"Found {len(jobs)} jobs on Dice")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error searching Dice jobs: {str(e)}")
            return []
        finally:
            if 'driver' in locals():
                driver.quit()
            
    def _scroll_page(self):
        """Scroll the page to load more job listings with human-like behavior"""
        try:
            # Scroll to bottom of page with random pauses
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll a random amount
                scroll_amount = random.randint(300, 700)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self._random_delay(1, 2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
        except Exception as e:
            logger.warning(f"Error scrolling page: {str(e)}")
            
    def _get_job_description(self, job_url: str) -> str:
        """Get job description from job page with human-like behavior"""
        try:
            self.driver.get(job_url)
            self._random_delay(3, 5)
            
            # Wait for job description to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-description"))
            )
            
            # Scroll through the description
            description_element = self.driver.find_element(By.CLASS_NAME, "job-description")
            self.driver.execute_script("arguments[0].scrollIntoView();", description_element)
            self._random_delay(1, 2)
            
            description = description_element.text
            return description
            
        except Exception as e:
            logger.warning(f"Error getting job description: {str(e)}")
            return ""
            
    def _extract_search_keywords(self, resume_data: Dict) -> List[str]:
        """Extract relevant keywords from resume data for job search"""
        keywords = []
        
        # Add skills from all sections
        for section_name, section_data in resume_data.items():
            if 'keywords' in section_data:
                keywords.extend(section_data['keywords'][:5])  # Top 5 keywords per section
                
            # Add entities that might be relevant
            if 'entities' in section_data:
                for entity, label in section_data['entities']:
                    if label in ['ORG', 'PERSON', 'GPE', 'NORP']:  # Organization, Person, Location, Nationality
                        keywords.append(entity)
                        
        # Add job title and education from text
        for section_name, section_data in resume_data.items():
            if 'text' in section_data:
                text = section_data['text'].lower()
                if 'experience' in section_name.lower():
                    # Extract job titles
                    job_titles = re.findall(r'(?:senior|junior|lead|principal)?\s*(?:software|web|frontend|backend|fullstack|devops|data|machine learning|ai|cloud|security)?\s*(?:engineer|developer|architect|scientist|analyst|specialist)', text)
                    keywords.extend(job_titles)
                    
                if 'education' in section_name.lower():
                    # Extract degrees
                    degrees = re.findall(r'(?:bachelor|master|phd|doctorate)\s*(?:of|in)?\s*(?:science|arts|engineering|computer science|information technology)', text)
                    keywords.extend(degrees)
                    
        return list(set(keywords))  # Remove duplicates
        
    def _extract_job_title(self, listing) -> str:
        """Extract job title from listing"""
        title_elem = listing.find('h5', class_='card-title')
        return title_elem.text.strip() if title_elem else ''
        
    def _extract_company(self, listing) -> str:
        """Extract company name from listing"""
        company_elem = listing.find('a', class_='card-company')
        return company_elem.text.strip() if company_elem else ''
        
    def _extract_location(self, listing) -> str:
        """Extract job location from listing"""
        location_elem = listing.find('span', class_='job-location')
        return location_elem.text.strip() if location_elem else ''
        
    def _extract_salary(self, listing) -> str:
        """Extract salary information from listing"""
        salary_elem = listing.find('span', class_='salary')
        return salary_elem.text.strip() if salary_elem else ''
        
    def _extract_description(self, listing) -> str:
        """Extract job description from listing"""
        desc_elem = listing.find('div', class_='card-description')
        return desc_elem.text.strip() if desc_elem else ''
        
    def _extract_posted_date(self, listing) -> str:
        """Extract job posting date from listing"""
        date_elem = listing.find('span', class_='posted-date')
        return date_elem.text.strip() if date_elem else ''
        
    def _extract_job_url(self, listing) -> str:
        """Extract job URL from listing"""
        url_elem = listing.find('a', class_='card-title-link')
        if url_elem and 'href' in url_elem.attrs:
            return url_elem['href']
        return ''
        
    def extract_required_skills(self, job_description: str) -> List[str]:
        """Extract required skills from job description"""
        common_skills = [
            "python", "java", "javascript", "react", "angular", "vue", "node.js",
            "sql", "nosql", "aws", "azure", "gcp", "docker", "kubernetes",
            "machine learning", "data science", "artificial intelligence",
            "web development", "mobile development", "backend", "frontend",
            "full stack", "devops", "cloud computing", "cybersecurity"
        ]
        
        required_skills = []
        for skill in common_skills:
            if skill.lower() in job_description.lower():
                required_skills.append(skill)
                
        return required_skills
        
    def apply_for_job(self, job: Dict[str, Any], resume_data: Dict[str, Any]) -> bool:
        """Apply for a job on Dice"""
        try:
            # Navigate to job page
            self.driver.get(job['link'])
            
            # Wait for apply button
            apply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "apply-button"))
            )
            apply_button.click()
            
            # Wait for application form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "application-form"))
            )
            
            # Fill application form
            self.fill_application_form(resume_data)
            
            # Submit application
            submit_button = self.driver.find_element(By.CLASS_NAME, "submit-button")
            submit_button.click()
            
            # Wait for confirmation
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying for job on Dice: {str(e)}")
            return False
            
    def fill_application_form(self, resume_data: Dict[str, Any]):
        """Fill out the Dice application form"""
        try:
            # Upload resume
            resume_path = os.getenv('RESUME_PATH')
            if resume_path:
                file_input = self.driver.find_element(By.CLASS_NAME, "resume-upload")
                file_input.send_keys(resume_path)
                
            # Fill personal information
            self.fill_personal_info(resume_data)
            
            # Fill work experience
            self.fill_work_experience(resume_data['experiences'])
            
            # Fill skills
            self.fill_skills(resume_data['skills'])
            
        except Exception as e:
            logger.error(f"Error filling application form: {str(e)}")
            raise
            
    def fill_personal_info(self, resume_data: Dict[str, Any]):
        """Fill personal information in the application form"""
        try:
            # Get Gmail credentials
            creds = self.password_manager.get_credentials('email')
            
            # Fill name
            name_input = self.driver.find_element(By.NAME, "name")
            name_input.send_keys(resume_data.get('name', ''))
            
            # Fill email
            email_input = self.driver.find_element(By.NAME, "email")
            email_input.send_keys(creds['username'])
            
            # Fill phone
            phone_input = self.driver.find_element(By.NAME, "phone")
            phone_input.send_keys(os.getenv('PHONE'))
            
        except Exception as e:
            logger.error(f"Error filling personal information: {str(e)}")
            raise
            
    def fill_work_experience(self, experiences: List[Dict[str, Any]]):
        """Fill work experience in the application form"""
        try:
            for exp in experiences:
                # Add new experience section
                add_exp_button = self.driver.find_element(By.CLASS_NAME, "add-experience")
                add_exp_button.click()
                
                # Fill experience details
                title_input = self.driver.find_element(By.NAME, "title")
                title_input.send_keys(exp['role'])
                
                company_input = self.driver.find_element(By.NAME, "company")
                company_input.send_keys(exp['company'])
                
                description_input = self.driver.find_element(By.NAME, "description")
                description_input.send_keys(exp['description'])
                
        except Exception as e:
            logger.error(f"Error filling work experience: {str(e)}")
            raise
            
    def fill_skills(self, skills: List[Dict[str, Any]]):
        """Fill skills in the application form"""
        try:
            skills_input = self.driver.find_element(By.NAME, "skills")
            skills_text = ', '.join([skill['skill'] for skill in skills])
            skills_input.send_keys(skills_text)
            
        except Exception as e:
            logger.error(f"Error filling skills: {str(e)}")
            raise
            
    def __del__(self):
        """Clean up WebDriver when object is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with options"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)  # Set implicit wait time
            return driver
            
        except Exception as e:
            self.logger.error(f"Error setting up WebDriver: {str(e)}")
            raise 