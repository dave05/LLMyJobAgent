import os
import logging
from dotenv import load_dotenv
from job_boards.linkedin import LinkedInJobBoard
from job_boards.indeed import IndeedJobBoard
from job_boards.dice import DiceJobBoard
from utils.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_job_boards.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_all_job_boards():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize resume parser
        parser = ResumeParser()
        resume_path = "data/_Beshah, Dawit latest .pdf"  # Use the actual resume path
        
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")
            
        # Parse resume
        logger.info("Analyzing resume...")
        resume_data = parser.parse_resume(resume_path)
        
        # Initialize job boards
        job_boards = {
            'LinkedIn': LinkedInJobBoard(),
            'Indeed': IndeedJobBoard(),
            'Dice': DiceJobBoard()
        }
        
        # Test each job board
        for board_name, board in job_boards.items():
            try:
                logger.info(f"Testing {board_name} job search...")
                jobs = board.search_jobs(resume_data)
                
                # Print job details
                print(f"\n=== {board_name} Job Search Results ===")
                print(f"\nFound {len(jobs)} jobs:")
                for job in jobs:
                    print(f"\nTitle: {job['title']}")
                    print(f"Company: {job['company']}")
                    print(f"Location: {job['location']}")
                    print(f"URL: {job['url']}")
                    print("-" * 50)
                    
                print(f"\n✅ {board_name} job search test completed successfully!")
                
            except Exception as e:
                logger.error(f"Error during {board_name} test: {str(e)}")
                print(f"❌ {board_name} Error: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error during job board tests: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_all_job_boards() 