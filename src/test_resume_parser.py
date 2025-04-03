import os
import logging
from dotenv import load_dotenv
from utils.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_resume_parser.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_resume_parser():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize resume parser
        parser = ResumeParser()
        resume_path = os.getenv('RESUME_PATH')
        
        if not os.path.exists(resume_path):
            raise FileNotFoundError(f"Resume not found at {resume_path}")
            
        # Parse resume
        logger.info(f"Parsing resume: {resume_path}")
        resume_data = parser.parse_resume(resume_path)
        
        # Print parsed sections
        print("\n=== Resume Analysis Results ===")
        for section, data in resume_data.items():
            if data['text'].strip():
                print(f"\n{section.upper()}:")
                print(f"Text: {data['text'][:200]}...")  # Show first 200 chars
                if data['entities']:
                    print(f"Entities: {', '.join([f'{e[0]} ({e[1]})' for e in data['entities'][:5]])}...")
                if data['keywords']:
                    print(f"Keywords: {', '.join(data['keywords'][:10])}...")
                    
        print("\n✅ Resume parsing test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during resume parsing test: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_resume_parser() 