"""Password management utilities."""

import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

class PasswordManager:
    """Simple password manager that uses environment variables."""
    
    def __init__(self, key_file: str = "secret.key", credentials_file: str = "credentials.enc"):
        """Initialize the password manager with encryption key and credentials file."""
        self.key_file = Path(key_file)
        self.credentials_file = Path(credentials_file)
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)
        self.credentials = self._load_credentials()
        load_dotenv()
        
    def _load_or_create_key(self) -> bytes:
        """Load existing encryption key or create a new one."""
        try:
            if self.key_file.exists():
                return self.key_file.read_bytes()
            else:
                key = Fernet.generate_key()
                self.key_file.write_bytes(key)
                return key
        except Exception as e:
            logger.error(f"Error handling encryption key: {str(e)}")
            raise

    def _load_credentials(self) -> Dict:
        """Load encrypted credentials from file."""
        try:
            if self.credentials_file.exists():
                encrypted_data = self.credentials_file.read_bytes()
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            return {}
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return {}

    def _save_credentials(self):
        """Save encrypted credentials to file."""
        try:
            encrypted_data = self.fernet.encrypt(json.dumps(self.credentials).encode())
            self.credentials_file.write_bytes(encrypted_data)
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            raise

    def encrypt_password(self, password: str) -> str:
        """Encrypt a password"""
        try:
            return self.fernet.encrypt(password.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting password: {str(e)}")
            raise
            
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password"""
        try:
            return self.fernet.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting password: {str(e)}")
            raise
            
    def store_credentials(self, service: str, credentials: dict):
        """Store encrypted credentials for a service"""
        try:
            # Encrypt credentials
            creds_bytes = json.dumps(credentials).encode()
            encrypted_creds = self.fernet.encrypt(creds_bytes)
            
            # Save to file
            creds_file = f'.{service}_creds.enc'
            with open(creds_file, 'wb') as f:
                f.write(encrypted_creds)
                
            # Set secure permissions
            os.chmod(creds_file, 0o600)
            
            logger.info(f"Credentials stored successfully for {service}")
            
        except Exception as e:
            logger.error(f"Error storing credentials for {service}: {str(e)}")
            raise
            
    def get_credentials(self, service: str) -> Optional[Dict]:
        """Get credentials for a specific service."""
        return self.credentials.get(service)

    def set_credentials(self, service: str, username: str, password: str):
        """Set credentials for a specific service."""
        self.credentials[service] = {
            "username": username,
            "password": password
        }
        self._save_credentials()

    def delete_credentials(self, service: str):
        """Delete credentials for a specific service."""
        if service in self.credentials:
            del self.credentials[service]
            self._save_credentials()

    def prompt_for_credentials(self, service: str) -> None:
        """Prompt user for credentials and store them securely"""
        try:
            print(f"\nEnter credentials for {service}:")
            username = input("Username/Email: ")
            password = getpass.getpass("Password: ")
            
            self.set_credentials(service, username, password)
            print(f"Credentials for {service} stored securely.")
            
        except Exception as e:
            logger.error(f"Error prompting for credentials: {str(e)}")
            raise
            
    def setup_all_credentials(self) -> None:
        """Setup all required credentials"""
        services = ['linkedin', 'indeed', 'dice', 'email']
        for service in services:
            self.prompt_for_credentials(service)
            
    def get_env_credentials(self) -> Dict[str, str]:
        """Get all credentials for environment variables"""
        try:
            credentials = {}
            services = ['linkedin', 'indeed', 'dice', 'email']
            
            for service in services:
                creds = self.get_credentials(service)
                credentials[f'{service.upper()}_EMAIL'] = creds['username']
                credentials[f'{service.upper()}_PASSWORD'] = creds['password']
                
            return credentials
            
        except Exception as e:
            logger.error(f"Error getting environment credentials: {str(e)}")
            raise

    def list_services(self) -> list:
        """List all services with stored credentials."""
        return list(self.credentials.keys())

    def clear_all(self):
        """Clear all stored credentials."""
        self.credentials = {}
        self._save_credentials() 