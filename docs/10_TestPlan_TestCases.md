# Test Plan and Test Cases

## 1. Test Strategy Overview

### 1.1 Testing Objectives
- Ensure system reliability and stability under various conditions
- Validate data extraction accuracy and completeness
- Verify system performance meets requirements
- Confirm security measures protect user data and system resources
- Test user interface usability and accessibility

### 1.2 Testing Scope
- **Unit Testing**: Individual component functionality
- **Integration Testing**: Component interactions and data flow
- **System Testing**: End-to-end workflows and user scenarios
- **Performance Testing**: Load, stress, and scalability testing
- **Security Testing**: Vulnerability assessment and penetration testing
- **Usability Testing**: User experience and accessibility validation

### 1.3 Test Environment
- **Development**: Local environment with SQLite database
- **Staging**: Production-like environment with PostgreSQL
- **Production**: Live environment with monitoring and logging

### 1.4 Test Tools and Frameworks
- **Unit Tests**: pytest, unittest
- **Integration Tests**: pytest, testcontainers
- **API Tests**: pytest, requests-mock
- **UI Tests**: Selenium, Playwright
- **Performance Tests**: Locust, JMeter
- **Security Tests**: OWASP ZAP, Bandit

## 2. Unit Testing

### 2.1 Scraper Engine Tests

#### Test Case: UT-SCR-001 - Static HTML Parsing
**Objective**: Verify static HTML content parsing functionality

```python
import pytest
from scrapers.static_scraper import StaticScraper
from scrapers.config import ScraperConfig

def test_static_html_parsing():
    """Test parsing of static HTML content"""
    config = ScraperConfig(
        url="https://example.com",
        selectors={
            "title": "h1",
            "description": ".description",
            "links": "a[href]"
        }
    )
    scraper = StaticScraper(config)
    
    # Mock HTML response
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Test Title</h1>
            <div class="description">Test description</div>
            <a href="https://example.com/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
        </body>
    </html>
    """
    
    # Test data extraction
    extracted_data = scraper.extract_data(html_content, config.selectors)
    
    # Assertions
    assert extracted_data["title"] == ["Test Title"]
    assert extracted_data["description"] == ["Test description"]
    assert len(extracted_data["links"]) == 2
    assert "https://example.com/page1" in extracted_data["links"]
```

#### Test Case: UT-SCR-002 - Dynamic Content Handling
**Objective**: Verify JavaScript-rendered content extraction

```python
def test_dynamic_content_extraction():
    """Test extraction of dynamic JavaScript content"""
    config = ScraperConfig(
        url="https://example.com/dynamic",
        selectors={
            "content": "#dynamic-content",
            "price": ".price"
        },
        scraper_type="dynamic"
    )
    scraper = DynamicScraper(config)
    
    # Mock dynamic content
    with patch('selenium.webdriver.Chrome') as mock_driver:
        mock_driver.page_source = """
        <html>
            <body>
                <div id="dynamic-content">Dynamic content loaded</div>
                <div class="price">$99.99</div>
            </body>
        </html>
        """
        
        result = scraper.scrape_page("https://example.com/dynamic")
        
        assert "Dynamic content loaded" in result.data["content"]
        assert "$99.99" in result.data["price"]
```

#### Test Case: UT-SCR-003 - Error Handling
**Objective**: Verify proper error handling for network issues

```python
def test_network_error_handling():
    """Test handling of network errors"""
    config = ScraperConfig(url="https://invalid-url.com", selectors={})
    scraper = StaticScraper(config)
    
    with patch('requests.Session.get') as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(NetworkError):
            scraper.scrape_page("https://invalid-url.com")
```

### 2.2 Data Processing Tests

#### Test Case: UT-DP-001 - Data Cleaning
**Objective**: Verify HTML tag removal and text normalization

```python
def test_data_cleaning():
    """Test HTML tag removal and text normalization"""
    processor = DataCleaner()
    
    # Test HTML tag removal
    html_text = "<p>Test <strong>content</strong> with <em>formatting</em></p>"
    cleaned = processor.clean_text(html_text)
    
    assert cleaned == "Test content with formatting"
    assert "<" not in cleaned and ">" not in cleaned

def test_whitespace_normalization():
    """Test whitespace normalization"""
    processor = DataCleaner()
    
    # Test multiple spaces and newlines
    messy_text = "Test    text\n\n   with   \t  irregular   spacing"
    normalized = processor.clean_text(messy_text)
    
    assert normalized == "Test text with irregular spacing"

def test_special_character_handling():
    """Test special character handling"""
    processor = DataCleaner()
    
    # Test special characters
    special_text = "Test &amp; content &lt;with&gt; special &quot;chars&quot;"
    cleaned = processor.clean_text(special_text)
    
    assert cleaned == "Test & content <with> special \"chars\""
```

#### Test Case: UT-DP-002 - Data Validation
**Objective**: Verify data validation rules enforcement

```python
def test_email_validation():
    """Test email format validation"""
    rules = {
        "email": ValidationRule(required=True, type="email")
    }
    validator = DataValidator(rules)
    
    # Valid email
    valid_data = {"email": "test@example.com"}
    result = validator.validate(valid_data)
    assert result.is_valid
    
    # Invalid email
    invalid_data = {"email": "invalid-email"}
    result = validator.validate(invalid_data)
    assert not result.is_valid
    assert "email" in str(result.errors)

def test_required_field_validation():
    """Test required field validation"""
    rules = {
        "name": ValidationRule(required=True),
        "email": ValidationRule(required=True)
    }
    validator = DataValidator(rules)
    
    # Missing required field
    incomplete_data = {"email": "test@example.com"}
    result = validator.validate(incomplete_data)
    assert not result.is_valid
    assert "name" in str(result.errors)

def test_type_validation():
    """Test data type validation"""
    rules = {
        "price": ValidationRule(type="number"),
        "url": ValidationRule(type="url")
    }
    validator = DataValidator(rules)
    
    # Valid types
    valid_data = {"price": "99.99", "url": "https://example.com"}
    result = validator.validate(valid_data)
    assert result.is_valid
    
    # Invalid types
    invalid_data = {"price": "not-a-number", "url": "not-a-url"}
    result = validator.validate(invalid_data)
    assert not result.is_valid
```

#### Test Case: UT-DP-003 - Data Transformation
**Objective**: Verify data transformation functions

```python
def test_price_transformation():
    """Test price string to number transformation"""
    transformer = NumberTransformer()
    
    # Test various price formats
    assert transformer.transform("$99.99") == 99.99
    assert transformer.transform("€1,234.56") == 1234.56
    assert transformer.transform("Free") == 0.0
    assert transformer.transform("") == 0.0

def test_date_transformation():
    """Test date string to datetime transformation"""
    transformer = DateTransformer()
    
    # Test various date formats
    assert transformer.transform("2024-01-15") == datetime(2024, 1, 15)
    assert transformer.transform("01/15/2024") == datetime(2024, 1, 15)
    assert transformer.transform("Jan 15, 2024") == datetime(2024, 1, 15)
```

### 2.3 Export Engine Tests

#### Test Case: UT-EXP-001 - CSV Export
**Objective**: Verify CSV export functionality

```python
def test_csv_export():
    """Test CSV export functionality"""
    exporter = CSVExporter()
    
    test_data = [
        {"name": "Product 1", "price": 99.99, "rating": 4.5},
        {"name": "Product 2", "price": 149.99, "rating": 4.8}
    ]
    
    file_path = exporter.export(test_data, "test_products")
    
    # Verify file creation
    assert os.path.exists(file_path)
    
    # Verify CSV content
    with open(file_path, 'r') as f:
        content = f.read()
        assert "name,price,rating" in content
        assert "Product 1,99.99,4.5" in content
    
    # Clean up
    os.remove(file_path)

def test_csv_custom_delimiter():
    """Test CSV export with custom delimiter"""
    exporter = CSVExporter()
    
    test_data = [{"name": "Product 1", "price": 99.99}]
    
    file_path = exporter.export(test_data, "test", delimiter=";")
    
    with open(file_path, 'r') as f:
        content = f.read()
        assert "name;price" in content
    
    os.remove(file_path)
```

#### Test Case: UT-EXP-002 - JSON Export
**Objective**: Verify JSON export functionality

```python
def test_json_export():
    """Test JSON export functionality"""
    exporter = JSONExporter()
    
    test_data = [
        {"name": "Product 1", "price": 99.99, "features": ["feature1", "feature2"]},
        {"name": "Product 2", "price": 149.99, "features": ["feature3"]}
    ]
    
    file_path = exporter.export(test_data, "test_products")
    
    # Verify file creation
    assert os.path.exists(file_path)
    
    # Verify JSON content
    with open(file_path, 'r') as f:
        exported_data = json.load(f)
        assert len(exported_data) == 2
        assert exported_data[0]["name"] == "Product 1"
        assert isinstance(exported_data[0]["features"], list)
    
    os.remove(file_path)
```

### 2.4 Job Management Tests

#### Test Case: UT-JM-001 - Job Creation
**Objective**: Verify job creation and validation

```python
def test_job_creation():
    """Test job creation with valid configuration"""
    job_config = JobConfig(
        name="Test Job",
        url="https://example.com",
        selectors={"title": "h1", "price": ".price"},
        config={"delay": 1.0, "max_retries": 3}
    )
    
    job = job_manager.create_job(job_config)
    
    assert job.name == "Test Job"
    assert job.status == JobStatus.PENDING
    assert job.created_at is not None

def test_job_validation():
    """Test job configuration validation"""
    # Invalid URL
    with pytest.raises(ValidationError):
        JobConfig(
            name="Invalid Job",
            url="invalid-url",
            selectors={}
        )
    
    # Missing required selectors
    with pytest.raises(ValidationError):
        JobConfig(
            name="Invalid Job",
            url="https://example.com",
            selectors={}
        )
```

#### Test Case: UT-JM-002 - Job Status Updates
**Objective**: Verify job status transitions

```python
def test_job_status_transitions():
    """Test valid job status transitions"""
    job = Job(name="Test Job", status=JobStatus.PENDING)
    
    # Valid transitions
    job.start()
    assert job.status == JobStatus.RUNNING
    
    job.complete()
    assert job.status == JobStatus.COMPLETED
    
    # Invalid transition
    with pytest.raises(InvalidStatusTransition):
        job.start()  # Can't start completed job

def test_job_failure_handling():
    """Test job failure and retry logic"""
    job = Job(name="Test Job", max_retries=3)
    
    # First failure
    job.fail("Network error")
    assert job.status == JobStatus.FAILED
    assert job.retry_count == 1
    
    # Retry
    job.retry()
    assert job.status == JobStatus.PENDING
    
    # Max retries exceeded
    for i in range(2, 4):
        job.fail(f"Attempt {i} failed")
    
    assert job.retry_count == 3
    assert job.can_retry() == False
```

## 3. Integration Testing

### 3.1 End-to-End Workflow Tests

#### Test Case: IT-E2E-001 - Complete Scraping Workflow
**Objective**: Verify complete scraping job from creation to export

```python
def test_complete_scraping_workflow():
    """Test complete scraping workflow"""
    # 1. Create job configuration
    job_config = JobConfig(
        name="E-commerce Test",
        url="https://test-ecommerce.com/products",
        selectors={
            "name": ".product-name",
            "price": ".product-price",
            "rating": ".product-rating"
        }
    )
    
    # 2. Create job
    job = job_manager.create_job(job_config)
    assert job.status == JobStatus.PENDING
    
    # 3. Start job execution
    job_manager.start_job(job.id)
    
    # 4. Monitor progress
    while job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
        job = job_manager.get_job(job.id)
        time.sleep(0.1)
    
    # 5. Verify completion
    assert job.status == JobStatus.COMPLETED
    assert job.records_processed > 0
    
    # 6. Export results
    export_path = export_engine.export_csv(job.id, "test_export")
    assert os.path.exists(export_path)
    
    # 7. Verify data quality
    results = result_manager.get_job_results(job.id)
    assert len(results) > 0
    
    for result in results:
        assert result.validation_status == ValidationStatus.VALID
        assert "name" in result.processed_data
        assert "price" in result.processed_data
```

#### Test Case: IT-E2E-002 - Error Recovery Workflow
**Objective**: Verify system behavior during errors and recovery

```python
def test_error_recovery_workflow():
    """Test error handling and recovery"""
    # Create job with invalid URL to simulate error
    job_config = JobConfig(
        name="Error Test",
        url="https://invalid-domain.com",
        selectors={"title": "h1"}
    )
    
    job = job_manager.create_job(job_config)
    job_manager.start_job(job.id)
    
    # Wait for job to fail
    while job.status == JobStatus.RUNNING:
        job = job_manager.get_job(job.id)
        time.sleep(0.1)
    
    # Verify failure handling
    assert job.status == JobStatus.FAILED
    assert job.error_message is not None
    assert job.retry_count > 0
    
    # Verify retry mechanism
    if job.can_retry():
        job_manager.retry_job(job.id)
        job = job_manager.get_job(job.id)
        assert job.status == JobStatus.PENDING
```

### 3.2 Database Integration Tests

#### Test Case: IT-DB-001 - Database Operations
**Objective**: Verify database CRUD operations

```python
def test_database_crud_operations():
    """Test database create, read, update, delete operations"""
    # Create
    job = Job(name="DB Test Job", url="https://example.com")
    db.session.add(job)
    db.session.commit()
    
    job_id = job.id
    assert job_id is not None
    
    # Read
    retrieved_job = Job.query.get(job_id)
    assert retrieved_job.name == "DB Test Job"
    
    # Update
    retrieved_job.name = "Updated Job Name"
    db.session.commit()
    
    updated_job = Job.query.get(job_id)
    assert updated_job.name == "Updated Job Name"
    
    # Delete
    db.session.delete(updated_job)
    db.session.commit()
    
    deleted_job = Job.query.get(job_id)
    assert deleted_job is None
```

#### Test Case: IT-DB-002 - Database Transactions
**Objective**: Verify transaction handling and rollback

```python
def test_database_transaction_rollback():
    """Test database transaction rollback on error"""
    try:
        # Start transaction
        job = Job(name="Transaction Test", url="https://example.com")
        db.session.add(job)
        db.session.flush()  # Get ID without committing
        
        # Add result
        result = Result(
            job_id=job.id,
            url="https://example.com/page1",
            raw_data={"test": "data"}
        )
        db.session.add(result)
        
        # Simulate error
        raise ValueError("Simulated error")
        
    except ValueError:
        # Rollback transaction
        db.session.rollback()
    
    # Verify rollback
    job = Job.query.filter_by(name="Transaction Test").first()
    assert job is None
    
    result = Result.query.filter_by(url="https://example.com/page1").first()
    assert result is None
```

### 3.3 API Integration Tests

#### Test Case: IT-API-001 - API Endpoints
**Objective**: Verify API endpoint functionality

```python
def test_api_job_creation():
    """Test API job creation endpoint"""
    client = app.test_client()
    
    job_data = {
        "name": "API Test Job",
        "url": "https://example.com",
        "selectors": {"title": "h1", "price": ".price"},
        "config": {"delay": 1.0}
    }
    
    response = client.post('/api/v1/jobs', json=job_data)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "job" in data["data"]
    assert data["data"]["job"]["name"] == "API Test Job"

def test_api_job_retrieval():
    """Test API job retrieval endpoint"""
    client = app.test_client()
    
    # Create job first
    job = Job(name="API Retrieval Test", url="https://example.com")
    db.session.add(job)
    db.session.commit()
    
    # Retrieve via API
    response = client.get(f'/api/v1/jobs/{job.id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["job"]["id"] == job.id

def test_api_error_handling():
    """Test API error handling"""
    client = app.test_client()
    
    # Invalid job data
    invalid_data = {
        "name": "",  # Empty name
        "url": "invalid-url",  # Invalid URL
        "selectors": {}
    }
    
    response = client.post('/api/v1/jobs', json=invalid_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "error" in data
```

## 4. System Testing

### 4.1 User Interface Tests

#### Test Case: ST-UI-001 - Dashboard Functionality
**Objective**: Verify dashboard displays and interactions

```python
def test_dashboard_job_list():
    """Test dashboard job listing"""
    driver = webdriver.Chrome()
    
    try:
        # Login
        driver.get("http://localhost:8000/login")
        driver.find_element(By.ID, "email").send_keys("test@example.com")
        driver.find_element(By.ID, "password").send_keys("password")
        driver.find_element(By.ID, "login-btn").click()
        
        # Navigate to dashboard
        driver.get("http://localhost:8000/dashboard")
        
        # Verify job list
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card")
        assert len(job_cards) > 0
        
        # Verify job status indicators
        status_indicators = driver.find_elements(By.CSS_SELECTOR, ".status-indicator")
        for indicator in status_indicators:
            assert indicator.is_displayed()
        
        # Test job filtering
        filter_dropdown = driver.find_element(By.ID, "status-filter")
        filter_dropdown.send_keys("completed")
        filter_dropdown.send_keys(Keys.RETURN)
        
        # Wait for filter to apply
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card.completed"))
        )
        
    finally:
        driver.quit()
```

#### Test Case: ST-UI-002 - Job Configuration
**Objective**: Verify job configuration interface

```python
def test_job_configuration_wizard():
    """Test job configuration wizard"""
    driver = webdriver.Chrome()
    
    try:
        # Login and navigate to job creation
        driver.get("http://localhost:8000/jobs/new")
        
        # Step 1: Basic Information
        driver.find_element(By.ID, "job-name").send_keys("UI Test Job")
        driver.find_element(By.ID, "job-url").send_keys("https://example.com")
        driver.find_element(By.ID, "next-step").click()
        
        # Step 2: Field Selection
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "field-selection"))
        )
        
        # Test field selection
        title_field = driver.find_element(By.CSS_SELECTOR, "[data-field='title']")
        title_field.click()
        
        # Test CSS selector input
        selector_input = driver.find_element(By.ID, "title-selector")
        selector_input.send_keys("h1")
        
        # Test selector validation
        validate_btn = driver.find_element(By.ID, "validate-selector")
        validate_btn.click()
        
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".validation-success"))
        )
        
        # Complete wizard
        driver.find_element(By.ID, "create-job").click()
        
        # Verify job creation
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".job-created-success"))
        )
        
    finally:
        driver.quit()
```

### 4.2 Performance Tests

#### Test Case: ST-PERF-001 - Load Testing
**Objective**: Verify system performance under load

```python
class LoadTest(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
    
    @task(3)
    def create_job(self):
        """Create scraping job"""
        job_data = {
            "name": f"Load Test Job {random.randint(1000, 9999)}",
            "url": "https://example.com",
            "selectors": {"title": "h1"}
        }
        
        response = self.client.post("/api/v1/jobs", json=job_data)
        if response.status_code == 201:
            job_id = response.json()["data"]["job"]["id"]
            self.job_ids.append(job_id)
    
    @task(2)
    def check_job_status(self):
        """Check job status"""
        if self.job_ids:
            job_id = random.choice(self.job_ids)
            self.client.get(f"/api/v1/jobs/{job_id}/status")
    
    @task(1)
    def get_results(self):
        """Get job results"""
        if self.job_ids:
            job_id = random.choice(self.job_ids)
            self.client.get(f"/api/v1/jobs/{job_id}/results")
    
    def on_stop(self):
        """Clean up test data"""
        for job_id in self.job_ids:
            self.client.delete(f"/api/v1/jobs/{job_id}")
```

#### Test Case: ST-PERF-002 - Stress Testing
**Objective**: Verify system behavior under extreme load

```python
def test_stress_scraping_performance():
    """Test scraping performance under stress"""
    # Create multiple concurrent jobs
    job_configs = []
    for i in range(50):
        config = JobConfig(
            name=f"Stress Test Job {i}",
            url=f"https://example.com/page{i}",
            selectors={"title": "h1"}
        )
        job_configs.append(config)
    
    # Start all jobs concurrently
    start_time = time.time()
    jobs = []
    
    for config in job_configs:
        job = job_manager.create_job(config)
        job_manager.start_job(job.id)
        jobs.append(job)
    
    # Wait for all jobs to complete
    completed_jobs = []
    for job in jobs:
        while job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job = job_manager.get_job(job.id)
            time.sleep(0.1)
        completed_jobs.append(job)
    
    end_time = time.time()
    
    # Verify performance metrics
    total_time = end_time - start_time
    avg_time_per_job = total_time / len(jobs)
    
    assert avg_time_per_job < 30  # Each job should complete within 30 seconds
    assert all(job.status == JobStatus.COMPLETED for job in completed_jobs)
```

### 4.3 Security Tests

#### Test Case: ST-SEC-001 - Authentication Security
**Objective**: Verify authentication and authorization

```python
def test_authentication_security():
    """Test authentication security measures"""
    client = app.test_client()
    
    # Test unauthorized access
    response = client.get('/api/v1/jobs')
    assert response.status_code == 401
    
    # Test invalid credentials
    response = client.post('/api/v1/auth/login', json={
        "email": "invalid@example.com",
        "password": "wrong_password"
    })
    assert response.status_code == 401
    
    # Test JWT token validation
    invalid_token = "invalid.jwt.token"
    response = client.get('/api/v1/jobs', headers={
        'Authorization': f'Bearer {invalid_token}'
    })
    assert response.status_code == 401
    
    # Test expired token
    expired_token = generate_expired_token()
    response = client.get('/api/v1/jobs', headers={
        'Authorization': f'Bearer {expired_token}'
    })
    assert response.status_code == 401

def test_authorization_controls():
    """Test role-based access control"""
    # Create regular user
    regular_user = User(username="regular", email="regular@example.com", role="user")
    db.session.add(regular_user)
    db.session.commit()
    
    # Create admin user
    admin_user = User(username="admin", email="admin@example.com", role="admin")
    db.session.add(admin_user)
    db.session.commit()
    
    # Test regular user limitations
    regular_token = generate_token(regular_user)
    client = app.test_client()
    
    # Regular user should not access admin endpoints
    response = client.get('/api/v1/admin/users', headers={
        'Authorization': f'Bearer {regular_token}'
    })
    assert response.status_code == 403
    
    # Admin should access admin endpoints
    admin_token = generate_token(admin_user)
    response = client.get('/api/v1/admin/users', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    assert response.status_code == 200
```

#### Test Case: ST-SEC-002 - Input Validation
**Objective**: Verify input validation and XSS prevention

```python
def test_input_validation():
    """Test input validation for security"""
    client = app.test_client()
    
    # Test SQL injection attempts
    malicious_inputs = [
        "'; DROP TABLE jobs; --",
        "' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users --"
    ]
    
    for malicious_input in malicious_inputs:
        job_data = {
            "name": malicious_input,
            "url": "https://example.com",
            "selectors": {"title": "h1"}
        }
        
        response = client.post('/api/v1/jobs', json=job_data)
        assert response.status_code == 400  # Should be rejected
    
    # Test XSS attempts
    xss_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ]
    
    for xss_input in xss_inputs:
        job_data = {
            "name": xss_input,
            "url": "https://example.com",
            "selectors": {"title": "h1"}
        }
        
        response = client.post('/api/v1/jobs', json=job_data)
        if response.status_code == 201:
            # If accepted, verify XSS is sanitized in response
            data = response.get_json()
            job_name = data["data"]["job"]["name"]
            assert "<script>" not in job_name
            assert "javascript:" not in job_name
```

## 5. Test Automation

### 5.1 Continuous Integration Pipeline

#### GitHub Actions Configuration
```yaml
name: Test Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: scraper_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/scraper_test
        REDIS_URL: redis://localhost:6379/0

  ui-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Start application
      run: |
        python main.py &
        sleep 10
    
    - name: Run UI tests
      run: |
        pytest tests/ui/ -v --driver=Chrome

  performance-tests:
    runs-on: ubuntu-latest
    needs: ui-tests
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install locust
    
    - name: Start application
      run: |
        python main.py &
        sleep 10
    
    - name: Run performance tests
      run: |
        locust -f tests/performance/locustfile.py --headless \
          --users 50 --spawn-rate 5 --run-time 60s \
          --host http://localhost:8000
```

### 5.2 Test Data Management

#### Test Data Factory
```python
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_job(**overrides):
        """Create test job with default values"""
        defaults = {
            "name": "Test Job",
            "url": "https://example.com",
            "selectors": {"title": "h1"},
            "config": {"delay": 1.0, "max_retries": 3},
            "status": JobStatus.PENDING
        }
        defaults.update(overrides)
        return Job(**defaults)
    
    @staticmethod
    def create_user(**overrides):
        """Create test user with default values"""
        defaults = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True
        }
        defaults.update(overrides)
        return User(**defaults)
    
    @staticmethod
    def create_result(job_id, **overrides):
        """Create test result with default values"""
        defaults = {
            "job_id": job_id,
            "url": "https://example.com/page1",
            "raw_data": {"title": "Test Title", "price": "$99.99"},
            "validation_status": ValidationStatus.VALID
        }
        defaults.update(overrides)
        return Result(**defaults)
```

### 5.3 Test Utilities

#### Mock Services
```python
class MockScrapingService:
    """Mock scraping service for testing"""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
    
    def set_response(self, url, response_data):
        """Set mock response for URL"""
        self.responses[url] = response_data
    
    def scrape_page(self, url, selectors):
        """Mock scrape page method"""
        self.call_count += 1
        return self.responses.get(url, ScrapedPage(url=url, data={}))

class MockNotificationService:
    """Mock notification service for testing"""
    
    def __init__(self):
        self.notifications = []
    
    def send_notification(self, recipient, message, level="info"):
        """Mock send notification"""
        self.notifications.append({
            "recipient": recipient,
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow()
        })
```

## 6. Test Reporting

### 6.1 Coverage Requirements
- **Unit Tests**: ≥90% code coverage
- **Integration Tests**: ≥80% endpoint coverage
- **UI Tests**: ≥70% user flow coverage
- **Security Tests**: 100% authentication and authorization coverage

### 6.2 Test Metrics
- **Test Execution Time**: Unit tests < 5 minutes, Integration tests < 15 minutes
- **Test Success Rate**: ≥95% pass rate across all test suites
- **Defect Detection**: ≥80% of defects caught by automated tests
- **Regression Prevention**: Zero critical regressions in production

### 6.3 Reporting Format
```json
{
  "test_run": {
    "timestamp": "2024-01-15T10:30:00Z",
    "environment": "staging",
    "version": "1.2.3",
    "duration": "12m 45s",
    "total_tests": 1247,
    "passed": 1198,
    "failed": 49,
    "skipped": 0,
    "coverage": {
      "unit": 92.3,
      "integration": 85.7,
      "overall": 89.1
    },
    "categories": {
      "unit_tests": {"passed": 856, "failed": 23, "duration": "4m 12s"},
      "integration_tests": {"passed": 234, "failed": 18, "duration": "6m 33s"},
      "ui_tests": {"passed": 108, "failed": 8, "duration": "2m 00s"}
    }
  }
}
```

This comprehensive test plan ensures the web scraping system meets all quality, performance, and security requirements through systematic testing across all levels of the application.
