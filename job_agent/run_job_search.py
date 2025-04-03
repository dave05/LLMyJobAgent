import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from resume_parser import ResumeParser
from job_boards.linkedin import LinkedInJobBoard
from job_boards.indeed import IndeedJobBoard
from job_boards.dice import DiceJobBoard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/job_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Major US tech hubs and cities
LOCATIONS = [
    "Remote",
    "San Francisco, CA",
    "New York, NY",
    "Seattle, WA",
    "Austin, TX",
    "Boston, MA",
    "Los Angeles, CA",
    "Chicago, IL",
    "Denver, CO",
    "Atlanta, GA",
    "Washington, DC",
    "Portland, OR",
    "San Diego, CA",
    "Miami, FL",
    "Phoenix, AZ"
]

def run_job_search():
    """Run the job search across multiple locations"""
    logger.info("Starting scheduled job search")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Check required environment variables
        required_vars = ['RESUME_PATH', 'EMAIL_USERNAME', 'EMAIL_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Parse resume
        parser = ResumeParser()
        resume_data = parser.parse_resume(os.getenv("RESUME_PATH"))
        logger.info("Successfully parsed resume")
        
        # Initialize job boards
        job_boards = [
            LinkedInJobBoard(),
            IndeedJobBoard(),
            DiceJobBoard()
        ]
        
        all_jobs = []
        job_title = os.getenv('JOB_TITLE', 'Software Engineer')
        
        # Search each location
        for location in LOCATIONS:
            logger.info(f"Searching jobs in {location}")
            
            # Search each job board
            for board in job_boards:
                try:
                    logger.info(f"Starting job search on {board.__class__.__name__} in {location}")
                    jobs = board.search_jobs(job_title, location, resume_data)
                    if jobs:
                        all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Error searching {board.__class__.__name__} in {location}: {str(e)}")
                    continue
        
        # Sort all jobs by match score
        all_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Get top 20 jobs across all locations
        top_jobs = all_jobs[:20]
        
        # Send email with top matches if any found
        if top_jobs:
            job_boards[0]._send_job_matches_email(top_jobs, resume_data)
            
        logger.info(f"Job search completed. Found {len(all_jobs)} total jobs across {len(LOCATIONS)} locations")
        return all_jobs
        
    except Exception as e:
        logger.error(f"Error in job search: {str(e)}")
        return []
        
if __name__ == "__main__":
    run_job_search() 