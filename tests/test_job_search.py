import os
import pytest
from src.run_job_search import run_job_search
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_run_job_search():
    """Test the main job search functionality"""
    # Test with sample resume data
    resume_data = {
        "skills": ["Python", "Java", "SQL"],
        "experience": ["Software Engineer", "Developer"],
        "education": ["Computer Science"]
    }
    
    # Test with required environment variables
    required_vars = [
        'LINKEDIN_USERNAME',
        'LINKEDIN_PASSWORD',
        'RESUME_PATH',
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD',
        'NOTIFICATION_EMAIL'
    ]
    
    # Check if all required environment variables are set
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Run the job search
    jobs = run_job_search()
    assert isinstance(jobs, list)
    
    # If jobs are found, verify their structure
    if jobs:
        job = jobs[0]
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "url" in job
        assert "description" in job
        assert "match_score" in job
        assert "source" in job 