import os
import logging
from dotenv import load_dotenv
from job_boards.indeed import IndeedJobBoard
from job_boards.dice import DiceJobBoard
from job_boards.linkedin import LinkedInJobBoard
from utils.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_job_search.log'),
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
        resume_path = os.getenv('RESUME_PATH')
        
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")
            
        # Parse resume
        logger.info("Analyzing resume...")
        resume_data = parser.parse_resume(resume_path)
        
        # Initialize job boards
        indeed = IndeedJobBoard()
        dice = DiceJobBoard()
        linkedin = LinkedInJobBoard()
        
        # Test Indeed job search
        logger.info("Searching Indeed jobs...")
        indeed_jobs = indeed.search_jobs(resume_data)
        logger.info(f"Found {len(indeed_jobs)} jobs on Indeed")
        
        # Test Dice job search
        logger.info("Searching Dice jobs...")
        dice_jobs = dice.search_jobs(resume_data)
        logger.info(f"Found {len(dice_jobs)} jobs on Dice")
        
        # Test LinkedIn job search
        logger.info("Searching LinkedIn jobs...")
        linkedin_jobs = linkedin.search_jobs(resume_data)
        logger.info(f"Found {len(linkedin_jobs)} jobs on LinkedIn")
        
        # Print job details
        print("\n=== Job Search Results ===")
        print(f"\nIndeed Jobs ({len(indeed_jobs)}):")
        for job in indeed_jobs[:3]:  # Show first 3 jobs
            print(f"- {job['title']} at {job['company']}")
            
        print(f"\nDice Jobs ({len(dice_jobs)}):")
        for job in dice_jobs[:3]:  # Show first 3 jobs
            print(f"- {job['title']} at {job['company']}")
            
        print(f"\nLinkedIn Jobs ({len(linkedin_jobs)}):")
        for job in linkedin_jobs[:3]:  # Show first 3 jobs
            print(f"- {job['title']} at {job['company']}")
            
        print("\n✅ Job search test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during job search test: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_job_search() 