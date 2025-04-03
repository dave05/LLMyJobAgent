import pytest
from job_agent.job_boards.dice import DiceJobBoard

@pytest.fixture
def dice():
    """Create a DiceJobBoard instance for testing"""
    return DiceJobBoard()

def test_dice_initialization(dice):
    """Test DiceJobBoard initialization"""
    assert dice.base_url == "https://www.dice.com"

def test_dice_search_jobs(dice):
    """Test Dice job search functionality"""
    # Test with sample resume data
    resume_data = {
        "skills": ["Python", "Java", "SQL"],
        "experience": ["Software Engineer", "Developer"],
        "education": ["Computer Science"]
    }
    
    jobs = dice.search_jobs("Software Engineer", "San Francisco", resume_data)
    assert isinstance(jobs, list)
    if jobs:  # If any jobs are found
        job = jobs[0]
        assert "title" in job
        assert "company" in job
        assert "location" in job
        assert "url" in job
        assert "description" in job
        assert "match_score" in job 