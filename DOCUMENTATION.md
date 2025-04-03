# Job Application Agent Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Components](#core-components)
3. [AI Components](#ai-components)
4. [Job Board Integration](#job-board-integration)
5. [Data Management](#data-management)
6. [Security Features](#security-features)
7. [Deployment](#deployment)
8. [Development Setup](#development-setup)

## Project Overview

The Job Application Agent is an automated system that helps users find and apply for jobs across multiple job boards (LinkedIn, Indeed, and Dice). It uses AI to match job descriptions with resumes and automates the application process.

### Main Execution Flow
1. The system starts from `src/main.py`
2. Initializes all components (resume analyzer, job matcher, email notifier)
3. Sets up job board connections
4. Runs scheduled job searches
5. Processes and matches jobs
6. Handles applications
7. Sends notifications

## Core Components

### 1. Main Application (`src/main.py`)
The central orchestrator that:
- Initializes all components
- Manages the application lifecycle
- Handles configuration and environment variables
- Coordinates between different modules

### 2. Job Search Runner (`src/run_job_search.py`)
- Manages scheduled job searches
- Defines search parameters (locations, job titles)
- Coordinates with job boards
- Handles search results

### 3. Email Notifier (`src/email_notifier.py`)
- Sends email notifications about:
  - New job matches
  - Application status
  - System updates
- Uses SMTP for email delivery
- Formats and styles email content

### 4. Password Manager (`src/utils/password_manager.py`)
- Securely stores and retrieves credentials
- Uses encryption for sensitive data
- Manages API keys and passwords
- Handles credential rotation

## AI Components

### 1. AI Job Matcher (`src/ai_job_matcher.py`)
Uses machine learning to:
- Calculate job similarity scores
- Match job requirements with resume skills
- Learn from successful applications
- Update skill weights based on outcomes

Key Features:
- Uses SentenceTransformer for text embeddings
- Implements cosine similarity for matching
- Maintains learning data for improvement
- Adapts to user's application success

### 2. AI Resume Analyzer (`src/ai_resume_analyzer.py`)
Processes and analyzes resumes:
- Extracts skills and experience
- Identifies key qualifications
- Matches against job requirements
- Uses NLP for text analysis

Features:
- Custom skill entity recognition
- Experience level assessment
- Education background analysis
- Skill proficiency evaluation

### 3. Resume Parser (`src/resume_parser.py`)
Handles different resume formats:
- PDF parsing
- DOCX parsing
- Text extraction
- Format standardization

## Job Board Integration

### 1. Base Job Board (`src/job_boards/base.py`)
Abstract base class that defines:
- Common job board operations
- Authentication methods
- Job search patterns
- Application tracking

### 2. LinkedIn Integration (`src/job_boards/linkedin.py`)
- Handles LinkedIn-specific authentication
- Implements LinkedIn job search
- Manages LinkedIn applications
- Tracks application status

### 3. Indeed Integration (`src/job_boards/indeed.py`)
- Implements Indeed job search
- Handles Indeed-specific requirements
- Manages Indeed applications
- Tracks Indeed-specific metrics

### 4. Dice Integration (`src/job_boards/dice.py`)
- Implements Dice job search
- Handles Dice-specific authentication
- Manages Dice applications
- Tracks Dice-specific metrics

## Data Management

### 1. Application Tracking
- Stores application history
- Tracks application status
- Maintains job details
- Records success metrics

### 2. Learning Data
- Stores successful matches
- Tracks application outcomes
- Maintains skill weights
- Records improvement metrics

### 3. Configuration Management
- Environment variables
- API keys
- User preferences
- System settings

## Security Features

### 1. Credential Management
- Encrypted storage
- Secure retrieval
- Access control
- Audit logging

### 2. Data Protection
- Sensitive data encryption
- Secure file handling
- Access restrictions
- Data validation

## Deployment

### 1. Docker Configuration
- Containerized application
- Environment isolation
- Dependency management
- Resource optimization

### 2. GitHub Actions
- Automated testing
- Continuous integration
- Docker image building
- Deployment automation

### 3. GitHub Codespaces
- Development environment
- Pre-configured setup
- Extension management
- Container customization

## Development Setup

### 1. Environment Setup
1. Clone the repository
2. Create virtual environment
3. Install dependencies
4. Configure environment variables

### 2. Running the Application
```bash
# Using Python directly
python src/main.py

# Using Docker
docker-compose up
```

### 3. Testing
```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_job_search.py
```

### 4. Development Tools
- VS Code extensions
- Python linting
- Code formatting
- Git integration

## Configuration

### Environment Variables
Required environment variables (see `.env.example`):
- Email configuration
- Job board credentials
- API keys
- Application settings

### Customization
- Job search parameters
- Matching thresholds
- Notification preferences
- Application limits

## Best Practices

### 1. Code Organization
- Modular design
- Clear separation of concerns
- Consistent naming conventions
- Comprehensive documentation

### 2. Error Handling
- Graceful failure
- Detailed logging
- Error recovery
- User notifications

### 3. Performance
- Efficient algorithms
- Resource optimization
- Caching strategies
- Load management

### 4. Security
- Regular updates
- Secure coding practices
- Access control
- Data protection

## Maintenance

### 1. Regular Updates
- Dependency updates
- Security patches
- Feature enhancements
- Bug fixes

### 2. Monitoring
- Application logs
- Performance metrics
- Error tracking
- User feedback

### 3. Backup
- Data backup
- Configuration backup
- Recovery procedures
- Disaster planning 