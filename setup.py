from setuptools import setup, find_packages

setup(
    name="job_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "python-dotenv",
        "PyPDF2",
        "requests",
        "beautifulsoup4",
        "cryptography",
    ],
    python_requires=">=3.11",
    author="Dawit Beshah",
    author_email="dawit.beshah@gmail.com",
    description="An AI-powered job application agent",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dave05/LLMyJobAgent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 