import os
import logging
from dotenv import load_dotenv
from job_agent.job_boards.indeed import IndeedJobBoard
from job_agent.utils.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_job_search():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize resume parser
        parser = ResumeParser()
        resume_path = "data/test_resume.json"
        
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")
            
        # Parse resume
        logger.info("Analyzing resume...")
        resume_data = parser.parse_resume(resume_path)
        
        # Initialize job board
        indeed = IndeedJobBoard()
        
        # Test Indeed job search
        logger.info("Searching Indeed jobs...")
        indeed_jobs = indeed.search_jobs("Software Engineer", "San Francisco", resume_data)
        assert isinstance(indeed_jobs, list), "Job search should return a list"
        logger.info(f"Found {len(indeed_jobs)} jobs on Indeed")
        
        print("\n✅ Job search test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during job search test: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_job_search() 