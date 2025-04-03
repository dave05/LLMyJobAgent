import os
import logging
from job_agent.utils.password_manager import PasswordManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_credentials():
    try:
        # Initialize password manager with test secret key
        pm = PasswordManager(secret_key_path="secret.key")
        
        # Store test credentials
        test_creds = {
            'username': 'test@example.com',
            'password': 'test_password'
        }
        pm.store_credentials('test', test_creds)
        
        # Test retrieving credentials
        retrieved_creds = pm.get_credentials('test')
        assert retrieved_creds is not None, "Failed to retrieve credentials"
        
        print("✅ Credential storage test passed!")
        
    except Exception as e:
        print(f"❌ Error testing credentials: {str(e)}")
        raise

if __name__ == "__main__":
    test_credentials() 