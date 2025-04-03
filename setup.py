from setuptools import setup, find_packages

setup(
    name="job_agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "webdriver-manager",
        "python-dotenv",
        "pytest",
        "pytest-cov",
    ],
) 