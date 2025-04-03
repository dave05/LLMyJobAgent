import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('EMAIL_USERNAME')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
        if not all([self.sender_email, self.sender_password, self.notification_email]):
            raise ValueError("Missing required email configuration in environment variables")
        
    def send_application_summary(self, applications: List[Dict]):
        """Send email summary of job applications"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.notification_email
            msg['Subject'] = f"Job Application Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            body = "Job Application Summary:\n\n"
            
            # Group applications by job board
            board_applications = {}
            for app in applications:
                board = app['board']
                if board not in board_applications:
                    board_applications[board] = []
                board_applications[board].append(app)
            
            # Format applications by job board
            for board, apps in board_applications.items():
                body += f"\n{board}:\n"
                body += "=" * (len(board) + 1) + "\n"
                
                for app in apps:
                    body += f"\nPosition: {app['job_title']}\n"
                    body += f"Company: {app['company']}\n"
                    body += f"Match Score: {app['match_score']:.2f}\n"
                    body += f"Applied at: {app['timestamp']}\n"
                    body += "-" * 50 + "\n"
            
            # Add summary statistics
            body += f"\nSummary Statistics:\n"
            body += f"Total Applications: {len(applications)}\n"
            body += f"Average Match Score: {sum(app['match_score'] for app in applications) / len(applications):.2f}\n"
            body += f"Applications by Platform: {', '.join(f'{board}: {len(apps)}' for board, apps in board_applications.items())}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info(f"Successfully sent application summary email for {len(applications)} applications")
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise
            
    def send_error_notification(self, error_message: str):
        """Send email notification for errors"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.notification_email
            msg['Subject'] = f"Job Application Agent Error - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            body = f"An error occurred in the Job Application Agent:\n\n{error_message}"
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info("Successfully sent error notification email")
                
        except Exception as e:
            logger.error(f"Error sending error notification: {str(e)}")
            raise
            
    def send_status_update(self, status_message: str):
        """Send email status update"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.notification_email
            msg['Subject'] = f"Job Application Agent Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            msg.attach(MIMEText(status_message, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info("Successfully sent status update email")
                
        except Exception as e:
            logger.error(f"Error sending status update: {str(e)}")
            raise 