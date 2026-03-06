@echo off
REM Web Scraper AI Setup Script for Windows
REM This script sets up the development environment on Windows

echo ========================================
echo Web Scraper AI Setup Script (Windows)
echo ========================================

REM Colors for output (limited in Windows)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM Function to print status
:print_status
echo %INFO% %~1
goto :eof

REM Function to print success
:print_success
echo %SUCCESS% %~1
goto :eof

REM Function to print warning
:print_warning
echo %WARNING% %~1
goto :eof

REM Function to print error
:print_error
echo %ERROR% %~1
goto :eof

REM Check if Python is installed
call :print_status "Checking Python installation..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Python is not installed. Please install Python 3.8+ first."
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :print_status "Found Python %PYTHON_VERSION%"

REM Check if pip is installed
call :print_status "Checking pip installation..."
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "pip is not installed. Please install pip first."
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
call :print_status "Found pip %PIP_VERSION%"

REM Create virtual environment
if not exist "venv" (
    call :print_status "Creating virtual environment..."
    python -m venv venv
    call :print_success "Virtual environment created"
) else (
    call :print_warning "Virtual environment already exists"
)

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    call :print_status "Virtual environment activated"
) else (
    call :print_error "Virtual environment activation script not found"
    pause
    exit /b 1
)

REM Upgrade pip
call :print_status "Upgrading pip..."
python -m pip install --upgrade pip

REM Install dependencies
call :print_status "Installing dependencies..."
if exist "requirements.txt" (
    pip install -r requirements.txt
    call :print_success "Dependencies installed from requirements.txt"
) else (
    call :print_error "requirements.txt not found"
    pause
    exit /b 1
)

REM Install development dependencies
if exist "requirements-dev.txt" (
    pip install -r requirements-dev.txt
    call :print_success "Development dependencies installed"
)

REM Create necessary directories
call :print_status "Creating necessary directories..."
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "uploads" mkdir uploads
if not exist "temp" mkdir temp
if not exist "static" mkdir static
if not exist "backups" mkdir backups
if not exist "scripts" mkdir scripts
call :print_success "All necessary directories created"

REM Setup environment file
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        call :print_status "Created .env from .env.example"
        call :print_warning "Please edit .env file with your configuration"
    ) else (
        call :print_warning ".env.example not found, creating basic .env file"
        echo # Web Scraper AI Configuration > .env
        echo. >> .env
        echo # Application Settings >> .env
        echo APP_NAME=Web Scraper AI >> .env
        echo DEBUG=True >> .env
        echo SECRET_KEY=your-secret-key-here >> .env
        echo JWT_SECRET_KEY=your-jwt-secret-key >> .env
        echo. >> .env
        echo # Database Settings >> .env
        echo DATABASE_URL=sqlite:///./scraper.db >> .env
        echo. >> .env
        echo # Redis Settings >> .env
        echo REDIS_URL=redis://localhost:6379/0 >> .env
        echo. >> .env
        echo # Scraping Settings >> .env
        echo DEFAULT_DELAY=1.0 >> .env
        echo MAX_CONCURRENT_JOBS=5 >> .env
        echo USER_AGENT=WebScraper/1.0 >> .env
        echo. >> .env
        echo # File Storage >> .env
        echo UPLOAD_FOLDER=uploads >> .env
        echo MAX_CONTENT_LENGTH=16777216 >> .env
        echo. >> .env
        echo # API Settings >> .env
        echo API_HOST=0.0.0.0 >> .env
        echo API_PORT=8000 >> .env
        echo CORS_ORIGINS=http://localhost:3000,http://localhost:8080 >> .env
        echo. >> .env
        echo # Monitoring Settings >> .env
        echo MONITORING_ENABLED=True >> .env
        echo LOG_LEVEL=INFO >> .env
        call :print_status "Created basic .env file"
    )
) else (
    call :print_warning ".env file already exists"
)

REM Initialize database
call :print_status "Initializing database..."
python manage.py db migrate
if %errorlevel% neq 0 (
    call :print_warning "Database migration failed, continuing..."
)

python manage.py db seed
if %errorlevel% neq 0 (
    call :print_warning "Database seeding failed, continuing..."
)

call :print_success "Database initialization completed"

REM Initialize Git repository
if not exist ".git" (
    call :print_status "Initializing Git repository..."
    git init >nul 2>&1
    
    if not exist ".gitignore" (
        echo # Byte-compiled / optimized / DLL files > .gitignore
        echo __pycache__/ >> .gitignore
        echo *.py[cod] >> .gitignore
        echo *$py.class >> .gitignore
        echo. >> .gitignore
        echo # C extensions >> .gitignore
        echo *.so >> .gitignore
        echo. >> .gitignore
        echo # Distribution / packaging >> .gitignore
        echo .Python >> .gitignore
        echo build/ >> .gitignore
        echo develop-eggs/ >> .gitignore
        echo dist/ >> .gitignore
        echo downloads/ >> .gitignore
        echo eggs/ >> .gitignore
        echo .eggs/ >> .gitignore
        echo lib/ >> .gitignore
        echo lib64/ >> .gitignore
        echo parts/ >> .gitignore
        echo sdist/ >> .gitignore
        echo var/ >> .gitignore
        echo wheels/ >> .gitignore
        echo pip-wheel-metadata/ >> .gitignore
        echo share/python-wheels/ >> .gitignore
        echo *.egg-info/ >> .gitignore
        echo .installed.cfg >> .gitignore
        echo *.egg >> .gitignore
        echo MANIFEST >> .gitignore
        echo. >> .gitignore
        echo # PyInstaller >> .gitignore
        echo *.manifest >> .gitignore
        echo *.spec >> .gitignore
        echo. >> .gitignore
        echo # Installer logs >> .gitignore
        echo pip-log.txt >> .gitignore
        echo pip-delete-this-directory.txt >> .gitignore
        echo. >> .gitignore
        echo # Unit test / coverage reports >> .gitignore
        echo htmlcov/ >> .gitignore
        echo .tox/ >> .gitignore
        echo .nox/ >> .gitignore
        echo .coverage >> .gitignore
        echo .coverage.* >> .gitignore
        echo .cache >> .gitignore
        echo nosetests.xml >> .gitignore
        echo coverage.xml >> .gitignore
        echo *.cover >> .gitignore
        echo *.py,cover >> .gitignore
        echo .hypothesis/ >> .gitignore
        echo .pytest_cache/ >> .gitignore
        echo. >> .gitignore
        echo # Translations >> .gitignore
        echo *.mo >> .gitignore
        echo *.pot >> .gitignore
        echo. >> .gitignore
        echo # Django stuff: >> .gitignore
        echo *.log >> .gitignore
        echo local_settings.py >> .gitignore
        echo db.sqlite3 >> .gitignore
        echo db.sqlite3-journal >> .gitignore
        echo. >> .gitignore
        echo # Flask stuff: >> .gitignore
        echo instance/ >> .gitignore
        echo .webassets-cache >> .gitignore
        echo. >> .gitignore
        echo # Scrapy stuff: >> .gitignore
        echo .scrapy >> .gitignore
        echo. >> .gitignore
        echo # Sphinx documentation >> .gitignore
        echo docs/_build/ >> .gitignore
        echo. >> .gitignore
        echo # PyBuilder >> .gitignore
        echo target/ >> .gitignore
        echo. >> .gitignore
        echo # Jupyter Notebook >> .gitignore
        echo .ipynb_checkpoints >> .gitignore
        echo. >> .gitignore
        echo # IPython >> .gitignore
        echo profile_default/ >> .gitignore
        echo ipython_config.py >> .gitignore
        echo. >> .gitignore
        echo # pyenv >> .gitignore
        echo .python-version >> .gitignore
        echo. >> .gitignore
        echo # pipenv >> .gitignore
        echo Pipfile.lock >> .gitignore
        echo. >> .gitignore
        echo # PEP 582; used by e.g. github.com/David-OConnor/pyflow >> .gitignore
        echo __pypackages__/ >> .gitignore
        echo. >> .gitignore
        echo # Celery stuff >> .gitignore
        echo celerybeat-schedule >> .gitignore
        echo celerybeat.pid >> .gitignore
        echo. >> .gitignore
        echo # SageMath parsed files >> .gitignore
        echo *.sage.py >> .gitignore
        echo. >> .gitignore
        echo # Environments >> .gitignore
        echo .env >> .gitignore
        echo .venv >> .gitignore
        echo env/ >> .gitignore
        echo venv/ >> .gitignore
        echo ENV/ >> .gitignore
        echo env.bak/ >> .gitignore
        echo venv.bak/ >> .gitignore
        echo. >> .gitignore
        echo # Spyder project settings >> .gitignore
        echo .spyderproject >> .gitignore
        echo .spyproject >> .gitignore
        echo. >> .gitignore
        echo # Rope project settings >> .gitignore
        echo .ropeproject >> .gitignore
        echo. >> .gitignore
        echo # mkdocs documentation >> .gitignore
        echo /site >> .gitignore
        echo. >> .gitignore
        echo # mypy >> .gitignore
        echo .mypy_cache/ >> .gitignore
        echo .dmypy.json >> .gitignore
        echo dmypy.json >> .gitignore
        echo. >> .gitignore
        echo # Pyre type checker >> .gitignore
        echo .pyre/ >> .gitignore
        echo. >> .gitignore
        echo # Project specific >> .gitignore
        echo scraper.db >> .gitignore
        echo scraper.db-journal >> .gitignore
        echo scraper.db-wal >> .gitignore
        echo scraper.db-shm >> .gitignore
        echo. >> .gitignore
        echo # Logs >> .gitignore
        echo logs/ >> .gitignore
        echo *.log >> .gitignore
        echo. >> .gitignore
        echo # Exports >> .gitignore
        echo exports/ >> .gitignore
        echo *.csv >> .gitignore
        echo *.json >> .gitignore
        echo *.xlsx >> .gitignore
        echo *.xls >> .gitignore
        echo. >> .gitignore
        echo # Uploads >> .gitignore
        echo uploads/ >> .gitignore
        echo temp/ >> .gitignore
        echo *.tmp >> .gitignore
        echo. >> .gitignore
        echo # Backups >> .gitignore
        echo backups/ >> .gitignore
        echo *.backup >> .gitignore
        echo *.bak >> .gitignore
        echo. >> .gitignore
        echo # Browser data >> .gitignore
        echo chromedriver* >> .gitignore
        echo geckodriver* >> .gitignore
        echo *.crx >> .gitignore
        echo. >> .gitignore
        echo # IDE >> .gitignore
        echo .vscode/ >> .gitignore
        echo .idea/ >> .gitignore
        echo *.swp >> .gitignore
        echo *.swo >> .gitignore
        echo *~ >> .gitignore
        echo. >> .gitignore
        echo # OS >> .gitignore
        echo .DS_Store >> .gitignore
        echo .DS_Store? >> .gitignore
        echo ._* >> .gitignore
        echo .Spotlight-V100 >> .gitignore
        echo .Trashes >> .gitignore
        echo ehthumbs.db >> .gitignore
        echo Thumbs.db >> .gitignore
        call :print_status "Created .gitignore file"
    )
    
    git add . >nul 2>&1
    git commit -m "Initial commit: Web Scraper AI setup" >nul 2>&1
    call :print_success "Git repository initialized"
) else (
    call :print_warning "Git repository already exists"
)

REM Run tests
call :print_status "Running tests..."
pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_warning "pytest not found, skipping tests"
) else (
    pytest tests/ -v
    if %errorlevel% neq 0 (
        call :print_warning "Some tests failed, but setup completed"
    ) else (
        call :print_success "All tests passed"
    )
)

echo ========================================
call :print_success "Setup completed successfully!"
echo ========================================
echo.
echo Next steps:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Edit .env file with your configuration
echo 3. Run the application: python main.py
echo 4. Access the API: http://localhost:8000
echo 5. View documentation: http://localhost:8000/docs
echo.
echo For more information, see the README.md file.
pause
