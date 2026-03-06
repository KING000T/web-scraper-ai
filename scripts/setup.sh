#!/bin/bash

# Web Scraper AI Setup Script
# This script sets up the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_status "Found Python $PYTHON_VERSION"
    
    # Check if Python version is 3.8+
    if [[ $PYTHON_VERSION < "3.8" ]]; then
        print_error "Python 3.8+ is required. Found version $PYTHON_VERSION"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        print_error "pip is not installed. Please install pip first."
        exit 1
    fi
    
    print_status "Found pip $($PIP_CMD --version)"
}

# Create virtual environment
create_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    if [ -d "venv" ]; then
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
            print_status "Virtual environment activated"
        elif [ -f "venv/Scripts/activate" ]; then
            source venv/Scripts/activate
            print_status "Virtual environment activated"
        else
            print_error "Virtual environment activation script not found"
            exit 1
        fi
    else
        print_error "Virtual environment not found"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed from requirements.txt"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "logs"
        "exports"
        "uploads"
        "temp"
        "static"
        "backups"
        "scripts"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    print_success "All necessary directories created"
}

# Setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Created .env from .env.example"
            print_warning "Please edit .env file with your configuration"
        else
            print_warning ".env.example not found, creating basic .env file"
            cat > .env << EOF
# Web Scraper AI Configuration

# Application Settings
APP_NAME=Web Scraper AI
DEBUG=True
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Database Settings
DATABASE_URL=sqlite:///./scraper.db

# Redis Settings
REDIS_URL=redis://localhost:6379/0

# Scraping Settings
DEFAULT_DELAY=1.0
MAX_CONCURRENT_JOBS=5
USER_AGENT=WebScraper/1.0

# File Storage
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Monitoring Settings
MONITORING_ENABLED=True
LOG_LEVEL=INFO
EOF
            print_status "Created basic .env file"
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    if command -v sqlite3 &> /dev/null; then
        # Create SQLite database
        if [ ! -f "scraper.db" ]; then
            sqlite3 scraper.db "SELECT 1;"
            print_success "SQLite database created"
        else
            print_warning "SQLite database already exists"
        fi
        
        # Run database migrations
        python manage.py db migrate
        print_success "Database migrations completed"
        
        # Seed database
        python manage.py db seed
        print_success "Database seeded with sample data"
    else
        print_warning "SQLite not found, skipping database initialization"
    fi
}

# Setup Git repository
setup_git() {
    if [ ! -d ".git" ]; then
        print_status "Initializing Git repository..."
        git init
        
        # Create .gitignore if it doesn't exist
        if [ ! -f ".gitignore" ]; then
            cat > .gitignore << EOF
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*\$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# Project specific
scraper.db
scraper.db-journal
scraper.db-wal
scraper.db-shm

# Logs
logs/
*.log

# Exports
exports/
*.csv
*.json
*.xlsx
*.xls

# Uploads
uploads/
temp/
*.tmp

# Backups
backups/
*.backup
*.bak

# Browser data
chromedriver*
geckodriver*
*.crx

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
EOF
            print_status "Created .gitignore file"
        fi
        
        # Initial commit
        git add .
        git commit -m "Initial commit: Web Scraper AI setup"
        print_success "Git repository initialized"
    else
        print_warning "Git repository already exists"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    if command -v pytest &> /dev/null; then
        pytest --version
        pytest tests/ -v
        print_success "Tests completed"
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Check system requirements
check_system() {
    print_status "Checking system requirements..."
    
    # Check available disk space
    if command -v df &> /dev/null; then
        AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
        REQUIRED_SPACE=1048576  # 1GB in KB
        
        if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
            print_warning "Low disk space. At least 1GB recommended."
        else
            print_success "Sufficient disk space available"
        fi
    fi
    
    # Check memory
    if command -v free &> /dev/null; then
        AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
        REQUIRED_MEM=1024  # 1GB in MB
        
        if [ "$AVAILABLE_MEM" -lt "$REQUIRED_MEM" ]; then
            print_warning "Low memory. At least 1GB recommended."
        else
            print_success "Sufficient memory available"
        fi
    fi
}

# Main setup function
main() {
    echo "========================================"
    echo "Web Scraper AI Setup Script"
    echo "========================================"
    
    print_status "Starting setup process..."
    
    # Check system requirements
    check_system
    
    # Check Python and pip
    check_python
    check_pip
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Setup environment
    setup_env
    
    # Initialize database
    init_database
    
    # Setup Git
    setup_git
    
    # Run tests
    run_tests
    
    echo "========================================"
    print_success "Setup completed successfully!"
    echo "========================================"
    
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Edit .env file with your configuration"
    echo "3. Run the application: python main.py"
    echo "4. Access the API: http://localhost:8000"
    echo "5. View documentation: http://localhost:8000/docs"
    echo ""
    echo "For more information, see the README.md file."
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --check        Only check system requirements"
        echo "  --venv         Only create virtual environment"
        echo "  --deps         Only install dependencies"
        echo "  --db           Only initialize database"
        echo "  --test         Only run tests"
        echo ""
        echo "Without options, runs full setup."
        exit 0
        ;;
    --check)
        check_system
        check_python
        check_pip
        exit 0
        ;;
    --venv)
        check_python
        create_venv
        exit 0
        ;;
    --deps)
        check_python
        check_pip
        activate_venv
        install_dependencies
        exit 0
        ;;
    --db)
        activate_venv
        init_database
        exit 0
        ;;
    --test)
        activate_venv
        run_tests
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information."
        exit 1
        ;;
esac
