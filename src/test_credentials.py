from utils.password_manager import PasswordManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_credentials():
    try:
        # Initialize password manager
        pm = PasswordManager()
        
        # Store Gmail credentials
        gmail_creds = {
            'username': 'dasam2012@gmail.com',
            'password': 'agdb mgqn jxdp lbrw'
        }
        pm.store_credentials('email', gmail_creds)
        
        # Test retrieving credentials
        retrieved_creds = pm.get_credentials('email')
        
        # Verify credentials match
        assert retrieved_creds['username'] == gmail_creds['username']
        assert retrieved_creds['password'] == gmail_creds['password']
        
        print("✅ Credential storage test passed!")
        print(f"Stored credentials for: {retrieved_creds['username']}")
        
    except Exception as e:
        print(f"❌ Error testing credentials: {str(e)}")
        raise

if __name__ == "__main__":
    test_credentials() 