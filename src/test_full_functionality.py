import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from job_boards.linkedin import LinkedInJobBoard
from job_boards.indeed_simple import IndeedJobBoard
from job_boards.dice import DiceJobBoard
from utils.password_manager import PasswordManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up test environment variables."""
    # Load test environment variables
    load_dotenv('tests/test_config.env')
    
    # Verify required environment variables
    required_vars = [
        'LINKEDIN_EMAIL',
        'LINKEDIN_PASSWORD',
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD',
        'NOTIFICATION_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    logger.info("Test environment setup completed successfully")

def test_job_search():
    """Test job search functionality across all job boards."""
    try:
        setup_test_environment()
        
        # Initialize job boards with test resume data
        resume_data = {
            "skills": ["python", "selenium", "web scraping"],
            "experience": ["software engineer", "web developer"],
            "education": ["computer science"]
        }
        
        # Test Indeed
        logger.info("Testing Indeed job search...")
        indeed = IndeedJobBoard(resume_data)
        indeed_jobs = indeed.search_jobs("python developer", "remote")
        logger.info(f"Found {len(indeed_jobs)} jobs on Indeed")
        
        # Verify results
        assert len(indeed_jobs) > 0, "No jobs found on Indeed"
        logger.info("Job search test passed successfully")
        
    except Exception as e:
        logger.error(f"Job search test failed: {str(e)}")
        raise

def test_application_tracking():
    """Test application tracking functionality."""
    try:
        setup_test_environment()
        
        # Initialize job board for testing
        resume_data = {"skills": ["python"], "experience": [], "education": []}
        job_board = IndeedJobBoard(resume_data)
        
        # Create test job
        test_job = {
            "id": f"test_{int(datetime.now().timestamp())}",
            "title": "Software Engineer",
            "company": "Test Company",
            "location": "Remote",
            "url": "https://example.com/job/1",
            "description": "Test job description"
        }
        
        # Track application
        result = job_board.track_application(test_job)
        assert result, "Failed to track application"
        
        # Get all applications
        applications = job_board.get_applications()
        assert len(applications) > 0, "No applications found"
        
        # Verify application data
        latest_app = applications[0]
        assert latest_app["id"] == test_job["id"], "Job ID mismatch"
        assert latest_app["title"] == test_job["title"], "Job title mismatch"
        assert latest_app["company"] == test_job["company"], "Company name mismatch"
        
        # Test duplicate application
        result = job_board.track_application(test_job)
        assert not result, "Duplicate application should not be allowed"
        
        # Test daily limit
        max_apps = int(os.getenv("MAX_APPLICATIONS_PER_DAY", 10))
        for i in range(max_apps):
            job = test_job.copy()
            job["id"] = f"test_{i}"
            job_board.track_application(job)
            
        # Try one more application
        job = test_job.copy()
        job["id"] = "test_limit"
        result = job_board.track_application(job)
        assert not result, "Should not exceed daily application limit"
        
        # Test date filtering
        today = datetime.now().date()
        today_apps = job_board.get_applications(date=today)
        assert len(today_apps) > 0, "No applications found for today"
        
        logger.info("Application tracking test passed successfully")
        
    except Exception as e:
        logger.error(f"Application tracking test failed: {str(e)}")
        raise

def test_match_score_calculation():
    """Test job match score calculation."""
    try:
        setup_test_environment()
        
        # Initialize job board
        resume_data = {
            "skills": ["python", "selenium"],
            "experience": ["software engineer"],
            "education": ["computer science"]
        }
        job_board = IndeedJobBoard(resume_data)
        
        # Test job
        test_job = {
            "description": "Looking for a Python developer with Selenium experience. Must have a degree in Computer Science."
        }
        
        # Calculate match score
        score = job_board._calculate_match_score(test_job["description"])
        assert 0 <= score <= 1, "Match score should be between 0 and 1"
        logger.info(f"Match score for test job: {score:.5f}")
        
        logger.info("Match score calculation test passed successfully")
        
    except Exception as e:
        logger.error(f"Match score calculation test failed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting comprehensive functionality test...")
        
        # Run all tests
        test_job_search()
        test_application_tracking()
        test_match_score_calculation()
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1) 