import os
import sys
import logging
from dotenv import load_dotenv
from utils.password_manager import PasswordManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/credential_setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_credentials():
    """Set up and manage credentials for the job application agent"""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Initialize password manager
        password_manager = PasswordManager()
        
        print("\n=== Job Application Agent Credential Setup ===")
        print("This script will help you securely set up your credentials.")
        print("Your passwords will be encrypted and stored locally.")
        print("Please have your Gmail credentials ready.\n")
        
        # Set up Gmail credentials
        print("\n=== Gmail Credentials ===")
        print("These credentials will be used for Indeed and Dice login.")
        email = input("Enter your Gmail address: ")
        password = input("Enter your Gmail password: ")
        
        # Store Gmail credentials
        password_manager.store_credentials('email', {
            'username': email,
            'password': password
        })
        
        # Update .env file
        with open('.env', 'a') as f:
            f.write(f"\n# Email configuration\n")
            f.write(f"EMAIL={email}\n")
        
        print("\n=== Credential Setup Complete ===")
        print("Your credentials have been securely stored.")
        print("\nImportant Notes:")
        print("1. The encryption key is stored in 'data/encryption_key.key'")
        print("2. Your encrypted credentials are stored in '.email_creds.enc'")
        print("3. Keep these files safe and back them up")
        print("4. Do not modify the .env file manually")
        print("\nYou can now run the job application agent.")
        
    except Exception as e:
        logger.error(f"Error setting up credentials: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    setup_credentials()