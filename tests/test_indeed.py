import pytest
from src.job_boards.indeed import IndeedJobBoard

@pytest.fixture
def indeed():
    """Create an IndeedJobBoard instance for testing"""
    return IndeedJobBoard()

def test_indeed_initialization(indeed):
    """Test IndeedJobBoard initialization"""
    assert indeed.base_url == "https://www.indeed.com"

def test_indeed_search_jobs(indeed):
    """Test Indeed job search functionality"""
    # Test with sample resume data
    resume_data = {
        "skills": ["Python", "Java", "SQL"],
        "experience": ["Software Engineer", "Developer"],
        "education": ["Computer Science"]
    }
    
    jobs = indeed.search_jobs("Software Engineer", "San Francisco", resume_data)
    assert isinstance(jobs, list)
    if jobs:  # If any jobs are found
        job = jobs[0]
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "url" in job
        assert "description" in job
        assert "match_score" in job 