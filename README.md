# Job Application Agent

An automated job application system that helps you find and apply for jobs across multiple job boards.

## Features

- Automated job search across multiple job boards (LinkedIn, Indeed, Dice)
- Intelligent job matching based on your resume
- Application tracking and management
- Email notifications for new job matches
- Daily application limit enforcement
- Duplicate application prevention

## Prerequisites

- Python 3.11+
- Chrome browser
- Gmail account (for email notifications)
- Job board accounts (LinkedIn, Indeed, Dice)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/job-agent.git
cd job-agent
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Edit the `.env` file with your credentials and preferences.

4. Build and run using Docker:
```bash
make docker-build
make docker-run
```

### Manual Installation

1. Create and activate a virtual environment:
```bash
make setup-dev
source .venv/bin/activate
```

2. Install dependencies:
```bash
make install
```

3. Create a `.env` file and configure it:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the application:
```bash
make run
```

## Configuration

The application is configured through environment variables in the `.env` file:

### Email Configuration
- `EMAIL_USERNAME`: Your Gmail address
- `EMAIL_PASSWORD`: Your Gmail App Password
- `NOTIFICATION_EMAIL`: Email address to receive notifications
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)

### Job Board Credentials
- `LINKEDIN_EMAIL`: LinkedIn account email
- `LINKEDIN_PASSWORD`: LinkedIn account password
- `INDEED_USERNAME`: Indeed account email
- `INDEED_PASSWORD`: Indeed account password
- `DICE_USERNAME`: Dice account email
- `DICE_PASSWORD`: Dice account password

### Application Settings
- `RESUME_PATH`: Path to your resume PDF
- `JOB_TITLE`: Desired job title
- `MAX_APPLICATIONS_PER_DAY`: Maximum number of applications per day
- `MIN_MATCH_SCORE`: Minimum match score for job applications

## Usage

1. Start the application:
```bash
make run
```

2. The application will:
   - Search for jobs matching your criteria
   - Calculate match scores
   - Send email notifications for new matches
   - Track your applications
   - Enforce daily limits

## Development

### Running Tests
```bash
make test
```

### Cleaning Build Files
```bash
make clean
```

### Docker Commands
```bash
make docker-build    # Build Docker image
make docker-run     # Start container
make docker-stop    # Stop container
make docker-logs    # View container logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Selenium for web automation
- spaCy for natural language processing
- Python-dotenv for environment management 