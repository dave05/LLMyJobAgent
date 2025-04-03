import os
import pytest
from src.job_boards.linkedin import LinkedInJobBoard
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture
def linkedin():
    """Create a LinkedInJobBoard instance for testing"""
    return LinkedInJobBoard()

def test_linkedin_initialization(linkedin):
    """Test LinkedInJobBoard initialization"""
    assert linkedin.base_url == "https://www.linkedin.com"
    assert linkedin.username is not None
    assert linkedin.password is not None

def test_linkedin_login(linkedin):
    """Test LinkedIn login functionality"""
    # Test with invalid credentials
    linkedin.username = "invalid@email.com"
    linkedin.password = "invalid_password"
    assert not linkedin._login()
    
    # Test with valid credentials from .env
    linkedin.username = os.getenv('LINKEDIN_USERNAME')
    linkedin.password = os.getenv('LINKEDIN_PASSWORD')
    if linkedin.username and linkedin.password:
        assert linkedin._login()
    else:
        pytest.skip("LinkedIn credentials not found in .env file")

def test_linkedin_public_search(linkedin):
    """Test LinkedIn public search functionality"""
    jobs = linkedin._public_search("Software Engineer", "San Francisco", {})
    assert isinstance(jobs, list)
    if jobs:  # If any jobs are found
        job = jobs[0]
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "url" in job
        assert job["source"] == "LinkedIn (Public)"

def test_linkedin_search_jobs(linkedin):
    """Test LinkedIn job search functionality"""
    # Test with sample resume data
    resume_data = {
        "skills": ["Python", "Java", "SQL"],
        "experience": ["Software Engineer", "Developer"],
        "education": ["Computer Science"]
    }
    
    jobs = linkedin.search_jobs("Software Engineer", "San Francisco", resume_data)
    assert isinstance(jobs, list)
    if jobs:  # If any jobs are found
        job = jobs[0]
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "url" in job
        assert "description" in job
        assert "match_score" in job 