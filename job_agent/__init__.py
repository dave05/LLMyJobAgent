"""Job Application Agent package."""

__version__ = "0.1.0"

from .utils.password_manager import PasswordManager
from .job_boards.linkedin import LinkedInJobBoard
from .job_boards.indeed import IndeedJobBoard
from .job_boards.dice import DiceJobBoard
from .resume_parser import ResumeParser

__all__ = [
    'PasswordManager',
    'LinkedInJobBoard',
    'IndeedJobBoard',
    'DiceJobBoard',
    'ResumeParser'
] 