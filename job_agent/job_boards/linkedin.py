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
from .base import BaseJobBoard

logger = logging.getLogger(__name__)

class LinkedInJobBoard(BaseJobBoard):
    def __init__(self, password_manager=None):
        """Initialize LinkedIn job board"""
        super().__init__()
        self.base_url = "https://www.linkedin.com"
        self.password_manager = password_manager or PasswordManager()
        self.username = os.getenv('LINKEDIN_USERNAME', os.getenv('EMAIL_USERNAME'))
        self.password = os.getenv('LINKEDIN_PASSWORD', os.getenv('EMAIL_PASSWORD'))
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
            
    def _can_apply_today(self) -> bool:
        """Check if we can apply for more jobs today"""
        try:
            applications = self._load_applications()
            today = datetime.now().date()
            today_applications = [
                app for app in applications
                if datetime.fromisoformat(app['applied_date']).date() == today
            ]
            return len(today_applications) < self.max_applications_per_day
        except Exception as e:
            logger.error(f"Error checking daily application limit: {str(e)}")
            return False
            
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
            msg['Subject'] = f"Top LinkedIn Job Matches - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            body = f"""
            <html>
                <body>
                    <h2>Top LinkedIn Job Matches</h2>
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
            
    def _login(self) -> bool:
        """Login to LinkedIn"""
        try:
            if not self.username or not self.password:
                logger.error("LinkedIn credentials not found")
                return False
                
            self.driver.get("https://www.linkedin.com/login")
            self._random_delay(2, 3)
            
            # Wait for login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            # Enter credentials
            username_field.send_keys(self.username)
            self._random_delay(1, 2)
            password_field.send_keys(self.password)
            self._random_delay(1, 2)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            self._human_click(login_button)
            
            # Wait for login to complete - try multiple selectors
            try:
                for selector in ["nav.global-nav", ".feed-identity-module", ".search-global-typeahead"]:
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info("Successfully logged in to LinkedIn")
                        return True
                    except TimeoutException:
                        continue
                        
                logger.error("Failed to verify login success")
                return False
                
            except Exception as e:
                logger.error(f"Error verifying login: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {str(e)}")
            return False
            
    def search_jobs(self, job_title: str, location: str, resume_data: Dict) -> List[Dict]:
        """Search for jobs on LinkedIn"""
        try:
            # Set up WebDriver
            self.setup_driver()
            
            # Login first
            if not self._login():
                raise Exception("Failed to login to LinkedIn")
            
            # Add random delay to avoid detection
            self._random_delay(3, 5)
            
            # Construct search URL with filters
            search_url = (
                f"{self.base_url}/jobs/search/?"
                f"keywords={job_title}&"
                f"location={location}&"
                f"f_TPR=r86400&"  # Last 24 hours
                f"f_WT=2&"  # Remote jobs
                f"sortBy=DD"  # Sort by date
            )
            self.driver.get(search_url)
            self._random_delay(3, 5)
            
            # Wait for job list to load
            try:
                job_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-search__results-list"))
                )
                job_cards = job_list.find_elements(By.CSS_SELECTOR, "div.job-card-container")
                logger.info(f"Found {len(job_cards)} job cards on LinkedIn")
            except TimeoutException:
                logger.warning("Job list not found")
                return []
            
            jobs = []
            for card in job_cards[:10]:  # Limit to first 10 jobs
                try:
                    # Extract minimal job details
                    title_elem = card.find_element(By.CSS_SELECTOR, ".job-card-list__title")
                    company_elem = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name")
                    location_elem = card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item")
                    
                    job = {
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "location": location_elem.text.strip(),
                        "url": title_elem.get_attribute("href"),
                        "source": "LinkedIn"
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract job details: {str(e)}")
                    continue
            
            # Send email with job links
            if jobs:
                self._send_job_links_email(jobs, source="LinkedIn")
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
            
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
            
    def __del__(self):
        """Clean up WebDriver when object is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 

    def _scroll_page(self):
        """Scroll the page to load more jobs with human-like behavior"""
        try:
            # Get initial height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down to bottom with random pauses
            while True:
                # Scroll down to bottom
                scroll_amount = random.randint(300, 700)  # Random scroll amount
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                
                # Wait to load page
                self._random_delay(1, 2)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                # Random chance to pause scrolling (simulate human behavior)
                if random.random() < 0.2:  # 20% chance
                    self._random_delay(1, 3)
                
        except Exception as e:
            logger.warning(f"Error scrolling page: {str(e)}")

    def _public_search(self, job_title: str, location: str, resume_data: Dict) -> List[Dict]:
        """Perform a public job search on LinkedIn without logging in"""
        try:
            # Construct public search URL
            search_query = f"{job_title}"
            search_url = f"{self.base_url}/jobs/search/?keywords={search_query}&location={location}&f_TPR=r86400"
            self.driver.get(search_url)
            self._random_delay(2, 4)
            
            # Handle any login prompts or popups
            try:
                dismiss_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-modal__dismiss"))
                )
                self._human_click(dismiss_button)
            except TimeoutException:
                pass
            
            # Wait for job list to load
            try:
                job_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results-list"))
                )
            except TimeoutException:
                logger.warning("Job list not found in public search")
                return []
            
            # Get all job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job-card-container")
            logger.info(f"Found {len(job_cards)} job cards in public search")
            
            jobs = []
            for card in job_cards[:10]:  # Limit to first 10 jobs for public search
                try:
                    # Extract job details
                    title_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title")
                    company_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-container__company-name")
                    location_elem = card.find_element(By.CSS_SELECTOR, "span.job-card-container__metadata-item")
                    
                    job = {
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "location": location_elem.text.strip(),
                        "url": title_elem.get_attribute("href"),
                        "source": "LinkedIn (Public)",
                        "description": "",  # Limited description in public search
                        "match_score": 0.5  # Default match score for public search
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract public job details: {str(e)}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs in public search")
            return jobs
            
        except Exception as e:
            logger.error(f"Error in public search: {str(e)}")
            return [] 