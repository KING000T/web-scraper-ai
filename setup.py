"""
Web Scraper AI - Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="web-scraper-ai",
    version="1.0.0",
    author="Web Scraper AI Team",
    author_email="contact@webscraper.ai",
    description="A comprehensive Python-based web scraping system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KING000T/web-scraper-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "grafana-api>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "web-scraper-ai=main:main",
            "ws-manage=manage:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.json", "*.yml", "*.yaml"],
        "frontends": ["*.html", "*.css", "*.js"],
        "config": ["*.json", "*.yml", "*.yaml"],
        "scripts": ["*.sh", "*.bat", "*.sql"],
    },
    zip_safe=False,
    keywords="web scraping, data extraction, automation, ai, machine learning",
    project_urls={
        "Bug Reports": "https://github.com/KING000T/web-scraper-ai/issues",
        "Source": "https://github.com/KING000T/web-scraper-ai",
        "Documentation": "https://web-scraper-ai.readthedocs.io/",
    },
)
