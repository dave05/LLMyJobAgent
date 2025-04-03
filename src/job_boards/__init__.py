# This file makes the job_boards directory a Python package 

"""
Job board modules for the job application agent.
"""

from .linkedin import LinkedInJobBoard
from .indeed import IndeedJobBoard
from .dice import DiceJobBoard
from .base import BaseJobBoard

__all__ = [
    'BaseJobBoard',
    'LinkedInJobBoard',
    'IndeedJobBoard',
    'DiceJobBoard'
] 