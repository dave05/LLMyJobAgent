import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from ai_resume_analyzer import AIResumeAnalyzer
from ai_job_matcher import AIJobMatcher
from email_notifier import EmailNotifier
from job_boards.linkedin import LinkedInJobBoard
from job_boards.indeed import IndeedJobBoard
from job_boards.dice import DiceJobBoard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/job_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIJobApplicationAgent:
    def __init__(self):
        self.resume_analyzer = AIResumeAnalyzer()
        self.job_matcher = AIJobMatcher()
        self.email_notifier = EmailNotifier()
        self.job_boards = [
            LinkedInJobBoard(),
            IndeedJobBoard(),
            DiceJobBoard()
        ]
        self.resume_data = None
        
    def process_resume(self) -> Dict[str, Any]:
        """Process the resume and extract relevant information"""
        try:
            resume_path = os.getenv('RESUME_PATH')
            if not resume_path:
                raise ValueError("RESUME_PATH environment variable not set")
                
            with open(resume_path, 'r') as f:
                resume_text = f.read()
                
            self.resume_data = self.resume_analyzer.analyze(resume_text)
            return self.resume_data
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            self.email_notifier.send_error_notification(f"Error processing resume: {str(e)}")
            raise
            
    def search_and_apply_for_jobs(self):
        """Search for jobs and apply to matching positions"""
        try:
            if not self.resume_data:
                self.process_resume()
                
            applications = []
            
            for job_board in self.job_boards:
                try:
                    # Search for jobs
                    jobs = job_board.search_jobs(self.resume_data)
                    
                    # Filter and rank jobs
                    ranked_jobs = self.job_matcher.rank_jobs(jobs, self.resume_data)
                    filtered_jobs = self.job_matcher.filter_jobs(ranked_jobs, self.resume_data)
                    
                    # Apply to jobs
                    for job in filtered_jobs:
                        try:
                            success = job_board.apply_for_job(job, self.resume_data)
                            applications.append({
                                **job,
                                'success': success,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            if success:
                                self.job_matcher.record_application_outcome(job, True)
                            else:
                                self.job_matcher.record_application_outcome(job, False)
                                
                        except Exception as e:
                            logger.error(f"Error applying for job {job['title']} at {job['company']}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error with job board {job_board.__class__.__name__}: {str(e)}")
                    continue
                    
            # Send application summary
            if applications:
                self.email_notifier.send_application_summary(applications)
                
        except Exception as e:
            logger.error(f"Error in search_and_apply_for_jobs: {str(e)}")
            self.email_notifier.send_error_notification(f"Error in search_and_apply_for_jobs: {str(e)}")
            raise
            
    def run(self):
        """Run the job application agent"""
        try:
            # Process resume
            self.process_resume()
            
            # Set up scheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(
                self.search_and_apply_for_jobs,
                'cron',
                day_of_week='mon-fri',
                hour='9-17',
                minute='0',
                timezone='America/New_York'
            )
            
            # Start scheduler
            scheduler.start()
            logger.info("Job application agent started")
            self.email_notifier.send_status_update("Job application agent started successfully")
            
            # Keep the script running
            while True:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error running job application agent: {str(e)}")
            self.email_notifier.send_error_notification(f"Error running job application agent: {str(e)}")
            raise
            
if __name__ == "__main__":
    agent = AIJobApplicationAgent()
    agent.run() 