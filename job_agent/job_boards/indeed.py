import os
import logging
import time
import random
import re
from typing import Dict, List, Optional, Tuple
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
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import difflib
import spacy
from job_agent.utils.password_manager import PasswordManager
import uuid
from .base import BaseJobBoard

logger = logging.getLogger(__name__)

class IndeedJobBoard(BaseJobBoard):
    def __init__(self, password_manager=None):
        """Initialize Indeed job board"""
        super().__init__()
        self.base_url = "https://www.indeed.com"
        self.driver = None
        self.setup_driver()
        self.password_manager = password_manager or PasswordManager()
        self.applications_file = "data/applications.json"
        self._ensure_applications_file()
        self.max_applications_per_day = int(os.getenv('MAX_APPLICATIONS_PER_DAY', 10))
        self.min_match_score = float(os.getenv('MIN_MATCH_SCORE', 0.7))
        self.nlp = spacy.load("en_core_web_sm")
        self.logger = logging.getLogger(__name__)
        
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
            msg['Subject'] = f"Top Indeed Job Matches - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            body = f"""
            <html>
                <body>
                    <h2>Top Indeed Job Matches</h2>
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
        """Search for jobs on Indeed"""
        try:
            # Set up WebDriver
            driver = self._setup_driver()
            
            # Construct search URL
            search_url = f"https://www.indeed.com/jobs?q={job_title}&l={location}"
            driver.get(search_url)
            
            # Wait for job list to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#mosaic-provider-jobcards"))
                )
            except TimeoutException:
                self.logger.warning("Job list not found")
                return []
            
            # Extract job details
            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
            self.logger.info(f"Found {len(job_cards)} job cards on Indeed")
            
            jobs = []
            for card in job_cards:
                try:
                    # Extract job details
                    title_element = card.find_element(By.CSS_SELECTOR, "h2.jobTitle")
                    title = title_element.text
                    company = card.find_element(By.CSS_SELECTOR, "span.companyName").text
                    location = card.find_element(By.CSS_SELECTOR, "div.companyLocation").text
                    url = title_element.find_element(By.XPATH, "./..").get_attribute("href")
                    
                    # Get job description
                    description = self._get_job_description(url)
                    
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
                    self.logger.warning(f"Error extracting job details: {str(e)}")
                    continue
            
            # Sort jobs by match score
            jobs.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Filter jobs by minimum match score
            filtered_jobs = [job for job in jobs if job['match_score'] >= self.min_match_score]
            
            # Send email with top matches
            if filtered_jobs:
                self._send_job_matches_email(filtered_jobs[:5], resume_data)
            
            return filtered_jobs
            
        except Exception as e:
            self.logger.error(f"Error searching jobs: {str(e)}")
            return []
        finally:
            if driver:
                driver.quit()

    def _get_job_description(self, job_url: str) -> str:
        """Get job description from job page"""
        try:
            driver = self._setup_driver()
            driver.get(job_url)
            
            # Wait for description to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#jobDescriptionText"))
                )
                description = driver.find_element(By.CSS_SELECTOR, "div#jobDescriptionText").text
            except TimeoutException:
                self.logger.warning("Job description not found")
                description = ""
            
            return description
            
        except Exception as e:
            self.logger.error(f"Error getting job description: {str(e)}")
            return ""
        finally:
            if driver:
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
            
    def _random_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay to simulate human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def _human_type(self, element, text):
        """Simulate human typing with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
            
    def _human_click(self, element):
        """Simulate human clicking with random delays"""
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.pause(random.uniform(0.5, 1.5))
        actions.click()
        actions.perform()
            
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