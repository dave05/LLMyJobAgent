import os
import logging
import time
from typing import List, Dict
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from job_agent.job_boards.linkedin import LinkedInJobBoard
from job_agent.utils.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/linkedin_applications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def send_application_summary(jobs: List[Dict]):
    """Send email summary of job applications"""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USERNAME')
        msg['To'] = os.getenv('NOTIFICATION_EMAIL')
        msg['Subject'] = f"LinkedIn Job Applications Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create summary table
        summary = """
        <html>
        <body>
        <h2>Job Applications Summary</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>Position</th>
            <th>Company</th>
            <th>Status</th>
            <th>Match Score</th>
            <th>Applied Date</th>
        </tr>
        """
        
        for job in jobs:
            summary += f"""
            <tr>
                <td>{job['title']}</td>
                <td>{job['company']}</td>
                <td>{job['status']}</td>
                <td>{job.get('match_score', 'N/A')}</td>
                <td>{job.get('applied_date', 'N/A')}</td>
            </tr>
            """
            
        summary += """
        </table>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(summary, 'html'))
        
        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USERNAME'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        logger.info("Sent application summary email")
        
    except Exception as e:
        logger.error(f"Error sending application summary: {str(e)}")

def main():
    """Main function to test LinkedIn job applications"""
    try:
        load_dotenv()
        
        # Initialize LinkedIn job board
        linkedin = LinkedInJobBoard()
        
        # Parse resume
        resume_parser = ResumeParser()
        resume_data = resume_parser.parse_resume(os.getenv('RESUME_PATH'))
        
        # Search for jobs
        logger.info("Searching for jobs on LinkedIn...")
        jobs = linkedin.search_jobs(resume_data)
        
        if not jobs:
            logger.warning("No jobs found matching the criteria")
            return
            
        # Sort jobs by match score
        jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Take top 10 jobs
        top_jobs = jobs[:10]
        logger.info(f"Selected top {len(top_jobs)} jobs for application")
        
        # Track application status
        application_results = []
        
        # Apply to each job with retries
        for job in top_jobs:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Applying for {job['title']} at {job['company']} (Attempt {attempt + 1}/{max_retries})")
                    
                    # Apply for job
                    success = linkedin.apply_for_job(job, resume_data)
                    
                    if success:
                        application_results.append({
                            'title': job['title'],
                            'company': job['company'],
                            'status': 'Applied',
                            'match_score': job.get('match_score', 'N/A'),
                            'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        logger.info(f"Successfully applied for {job['title']} at {job['company']}")
                        break
                    else:
                        if attempt == max_retries - 1:
                            application_results.append({
                                'title': job['title'],
                                'company': job['company'],
                                'status': 'Failed',
                                'match_score': job.get('match_score', 'N/A'),
                                'applied_date': 'N/A'
                            })
                            logger.warning(f"Failed to apply for {job['title']} at {job['company']} after {max_retries} attempts")
                        else:
                            logger.warning(f"Retry {attempt + 1} failed for {job['title']} at {job['company']}")
                            time.sleep(5)  # Wait before retry
                            
                except Exception as e:
                    logger.error(f"Error applying for {job['title']} at {job['company']}: {str(e)}")
                    if attempt == max_retries - 1:
                        application_results.append({
                            'title': job['title'],
                            'company': job['company'],
                            'status': 'Error',
                            'match_score': job.get('match_score', 'N/A'),
                            'applied_date': 'N/A'
                        })
                    time.sleep(5)  # Wait before retry
                    
        # Send application summary
        send_application_summary(application_results)
        
        logger.info("Completed job application process")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main() 