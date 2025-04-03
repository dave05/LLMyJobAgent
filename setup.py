from setuptools import setup, find_packages

setup(
    name="job_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "spacy==3.7.2",
        "sentence-transformers==2.2.2",
        "numpy==1.24.3",
        "scikit-learn==1.3.0",
        "selenium==4.15.2",
        "apscheduler==3.10.4",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3",
        "webdriver-manager==4.0.1",
        "cryptography==41.0.7",
        "python-docx==1.0.1",
        "PyPDF2==3.0.1",
        "pdfminer.six==20221105"
    ],
    python_requires=">=3.11",
) 