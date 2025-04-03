import os
import logging
from dotenv import load_dotenv
from job_agent.job_boards.linkedin import LinkedInJobBoard
from job_agent.utils.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_linkedin.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_linkedin():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize resume parser
        parser = ResumeParser()
        resume_path = "data/test_resume.json"  # Use the test resume file
        
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")
            
        # Parse resume
        logger.info("Analyzing resume...")
        resume_data = parser.parse_resume(resume_path)
        
        # Initialize LinkedIn job board
        linkedin = LinkedInJobBoard()
        
        # Test LinkedIn job search
        logger.info("Searching LinkedIn jobs...")
        jobs = linkedin.search_jobs(resume_data)
        
        # Print job details
        print("\n=== LinkedIn Job Search Results ===")
        print(f"\nFound {len(jobs)} jobs:")
        for job in jobs:
            print(f"\nTitle: {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Location: {job['location']}")
            print(f"URL: {job['url']}")
            print("-" * 50)
            
        print("\n✅ LinkedIn job search test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during LinkedIn test: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_linkedin() 