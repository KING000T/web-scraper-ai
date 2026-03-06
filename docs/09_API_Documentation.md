# API Documentation

## 1. API Overview

### 1.1 Introduction
The Web Scraping System REST API provides programmatic access to all system functionality, including job management, data extraction, result retrieval, and system monitoring. The API follows RESTful principles and uses JSON for data exchange.

### 1.2 Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.webscraper.com/v1`

### 1.3 Authentication
The API uses JWT (JSON Web Token) authentication for secure access.

#### Authentication Methods
- **Bearer Token**: Include JWT token in Authorization header
- **API Key**: Alternative authentication for programmatic access

#### Request Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
X-API-Key: <api_key>  # Alternative to JWT
```

### 1.4 Rate Limiting
- **Default**: 100 requests per hour
- **Authenticated**: 1,000 requests per hour
- **Premium**: 10,000 requests per hour

#### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### 1.5 Response Format
All API responses follow a consistent format:

#### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "url",
      "reason": "Invalid URL format"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 2. Authentication Endpoints

### 2.1 User Registration
```http
POST /auth/register
```

#### Request Body
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "user",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "User registered successfully"
}
```

### 2.2 User Login
```http
POST /auth/login
```

#### Request Body
```json
{
  "email": "john@example.com",
  "password": "secure_password123"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400
  },
  "message": "Login successful"
}
```

### 2.3 Token Refresh
```http
POST /auth/refresh
```

#### Request Headers
```http
Authorization: Bearer <expired_token>
```

#### Response
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400
  },
  "message": "Token refreshed successfully"
}
```

### 2.4 Logout
```http
POST /auth/logout
```

#### Request Headers
```http
Authorization: Bearer <token>
```

#### Response
```json
{
  "success": true,
  "message": "Logout successful"
}
```

## 3. Job Management Endpoints

### 3.1 Create Scraping Job
```http
POST /jobs
```

#### Request Body
```json
{
  "name": "Amazon Product Scraper",
  "description": "Extract product information from Amazon",
  "url": "https://www.amazon.com/s?k=laptops",
  "selectors": {
    "title": ".s-result-item .s-link",
    "price": ".a-price-whole",
    "rating": ".a-icon-alt .a-icon-alt-text",
    "availability": ".a-color-success"
  },
  "config": {
    "scraper_type": "static",
    "delay": 2.0,
    "max_retries": 3,
    "timeout": 30,
    "user_agent": "WebScraper/1.0"
  },
  "processing_rules": {
    "clean_html": true,
    "validate_required": ["title", "price"],
    "transformations": {
      "price": "number"
    }
  },
  "export_config": {
    "format": "csv",
    "delimiter": ",",
    "encoding": "utf-8"
  },
  "priority": 5,
  "tags": ["amazon", "products", "electronics"]
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "name": "Amazon Product Scraper",
      "status": "pending",
      "priority": 5,
      "created_at": "2024-01-15T10:30:00Z",
      "estimated_duration": 15
    }
  },
  "message": "Job created successfully"
}
```

### 3.2 List Jobs
```http
GET /jobs
```

#### Query Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `status`: Filter by status (`pending`, `running`, `completed`, `failed`, `cancelled`)
- `user_id`: Filter by user ID (admin only)
- `tags`: Filter by tags (comma-separated)
- `sort`: Sort field (`created_at`, `updated_at`, `priority`)
- `order`: Sort order (`asc`, `desc`)

#### Example Request
```http
GET /jobs?page=1&limit=10&status=completed&sort=created_at&order=desc
```

#### Response
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": 123,
        "name": "Amazon Product Scraper",
        "description": "Extract product information from Amazon",
        "status": "completed",
        "priority": 5,
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:30:05Z",
        "completed_at": "2024-01-15T10:45:23Z",
        "records_processed": 245,
        "records_total": 250,
        "tags": ["amazon", "products"]
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 45,
      "pages": 5
    }
  }
}
```

### 3.3 Get Job Details
```http
GET /jobs/{job_id}
```

#### Path Parameters
- `job_id`: Job ID

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "name": "Amazon Product Scraper",
      "description": "Extract product information from Amazon",
      "url": "https://www.amazon.com/s?k=laptops",
      "selectors": {
        "title": ".s-result-item .s-link",
        "price": ".a-price-whole",
        "rating": ".a-icon-alt .a-icon-alt-text"
      },
      "config": {
        "scraper_type": "static",
        "delay": 2.0,
        "max_retries": 3
      },
      "status": "completed",
      "priority": 5,
      "created_at": "2024-01-15T10:30:00Z",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:45:23Z",
      "records_processed": 245,
      "records_total": 250,
      "result_path": "/exports/job_123_20240115_104523.csv",
      "tags": ["amazon", "products"],
      "performance": {
        "pages_per_minute": 16.3,
        "success_rate": 98.0,
        "average_processing_time": 125
      }
    }
  }
}
```

### 3.4 Update Job
```http
PUT /jobs/{job_id}
```

#### Request Body
```json
{
  "name": "Updated Amazon Scraper",
  "description": "Updated description",
  "priority": 8,
  "tags": ["amazon", "products", "updated"]
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "name": "Updated Amazon Scraper",
      "description": "Updated description",
      "priority": 8,
      "updated_at": "2024-01-15T11:00:00Z"
    }
  },
  "message": "Job updated successfully"
}
```

### 3.5 Start Job
```http
POST /jobs/{job_id}/start
```

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "status": "running",
      "started_at": "2024-01-15T11:05:00Z"
    }
  },
  "message": "Job started successfully"
}
```

### 3.6 Stop Job
```http
POST /jobs/{job_id}/stop
```

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "status": "cancelled",
      "completed_at": "2024-01-15T11:10:00Z"
    }
  },
  "message": "Job stopped successfully"
}
```

### 3.7 Pause Job
```http
POST /jobs/{job_id}/pause
```

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "status": "paused"
    }
  },
  "message": "Job paused successfully"
}
```

### 3.8 Resume Job
```http
POST /jobs/{job_id}/resume
```

#### Response
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "status": "running"
    }
  },
  "message": "Job resumed successfully"
}
```

### 3.9 Delete Job
```http
DELETE /jobs/{job_id}
```

#### Response
```json
{
  "success": true,
  "message": "Job deleted successfully"
}
```

## 4. Job Status and Monitoring

### 4.1 Get Job Status
```http
GET /jobs/{job_id}/status
```

#### Response
```json
{
  "success": true,
  "data": {
    "job_id": 123,
    "status": "running",
    "progress": {
      "current": 150,
      "total": 250,
      "percentage": 60.0
    },
    "performance": {
      "pages_per_minute": 15.2,
      "success_rate": 98.5,
      "error_count": 2
    },
    "eta": "5 minutes",
    "started_at": "2024-01-15T10:30:05Z",
    "updated_at": "2024-01-15T10:40:15Z"
  }
}
```

### 4.2 Get Job Progress
```http
GET /jobs/{job_id}/progress
```

#### Response
```json
{
  "success": true,
  "data": {
    "job_id": 123,
    "progress": {
      "current": 150,
      "total": 250,
      "percentage": 60.0,
      "processed": 148,
      "failed": 2
    },
    "performance": {
      "pages_per_minute": 15.2,
      "average_processing_time": 125,
      "total_processing_time": 18750
    },
    "eta_seconds": 300
  }
}
```

### 4.3 Get Job Logs
```http
GET /jobs/{job_id}/logs
```

#### Query Parameters
- `level`: Filter by log level (`debug`, `info`, `warning`, `error`, `critical`)
- `limit`: Number of log entries (default: 50)
- `offset`: Offset for pagination

#### Response
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 4567,
        "level": "info",
        "message": "Starting job execution",
        "details": {
          "job_id": 123,
          "url_count": 250
        },
        "source": "job_manager",
        "created_at": "2024-01-15T10:30:05Z"
      },
      {
        "id": 4568,
        "level": "info",
        "message": "Processing page: https://www.amazon.com/s?page=1",
        "details": {
          "page_number": 1,
          "processing_time": 120
        },
        "source": "scraper_engine",
        "created_at": "2024-01-15T10:30:10Z"
      }
    ],
    "total": 245
  }
}
```

## 5. Results and Data Management

### 5.1 Get Job Results
```http
GET /jobs/{job_id}/results
```

#### Query Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 100, max: 1000)
- `format`: Response format (`json`, `csv`)
- `fields`: Comma-separated list of fields to return
- `filter`: Filter expression (JSON)

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 789,
        "url": "https://www.amazon.com/dp/B08N5WRWNW",
        "raw_data": {
          "title": "Dell XPS 13 Laptop",
          "price": "$899.99",
          "rating": "4.5 out of 5 stars"
        },
        "processed_data": {
          "title": "Dell XPS 13 Laptop",
          "price": 899.99,
          "rating": 4.5
        },
        "validation_status": "valid",
        "created_at": "2024-01-15T10:35:23Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 245,
      "pages": 3
    },
    "statistics": {
      "total_records": 245,
      "valid_records": 240,
      "invalid_records": 5,
      "validation_rate": 97.96
    }
  }
}
```

### 5.2 Get Single Result
```http
GET /results/{result_id}
```

#### Response
```json
{
  "success": true,
  "data": {
    "result": {
      "id": 789,
      "job_id": 123,
      "url": "https://www.amazon.com/dp/B08N5WRWNW",
      "raw_data": {
        "title": "Dell XPS 13 Laptop",
        "price": "$899.99",
        "rating": "4.5 out of 5 stars",
        "availability": "In Stock"
      },
      "processed_data": {
        "title": "Dell XPS 13 Laptop",
        "price": 899.99,
        "rating": 4.5,
        "availability": true
      },
      "validation_status": "valid",
      "processing_time_ms": 125,
      "created_at": "2024-01-15T10:35:23Z",
      "updated_at": "2024-01-15T10:35:24Z"
    }
  }
}
```

### 5.3 Export Results
```http
POST /jobs/{job_id}/export
```

#### Request Body
```json
{
  "format": "csv",
  "filename": "amazon_products",
  "delimiter": ",",
  "encoding": "utf-8",
  "include_headers": true,
  "fields": ["title", "price", "rating", "availability"],
  "filters": {
    "validation_status": "valid"
  }
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "export": {
      "id": 456,
      "job_id": 123,
      "format": "csv",
      "file_name": "amazon_products_20240115_104523.csv",
      "file_path": "/exports/amazon_products_20240115_104523.csv",
      "file_size": 15420,
      "record_count": 240,
      "download_url": "/exports/456/download",
      "share_url": "/exports/456/share",
      "expires_at": "2024-01-22T10:45:23Z"
    }
  },
  "message": "Export created successfully"
}
```

### 5.4 Download Export
```http
GET /exports/{export_id}/download
```

#### Response
Binary file download with appropriate headers:
```http
Content-Type: text/csv
Content-Disposition: attachment; filename="amazon_products_20240115_104523.csv"
Content-Length: 15420
```

### 5.5 Share Export
```http
POST /exports/{export_id}/share
```

#### Request Body
```json
{
  "expires_in": 7, // days
  "password": null, // optional password protection
  "download_limit": 10 // optional download limit
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "share_url": "https://api.webscraper.com/exports/456/share?token=abc123def456",
    "expires_at": "2024-01-22T10:45:23Z",
    "download_limit": 10,
    "download_count": 0
  },
  "message": "Export shared successfully"
}
```

## 6. Configuration Management

### 6.1 Create Job Configuration
```http
POST /configs
```

#### Request Body
```json
{
  "name": "Amazon Product Template",
  "description": "Template for scraping Amazon product pages",
  "url_pattern": "https://www.amazon.com/s?k={search_term}",
  "selectors": {
    "title": ".s-result-item .s-link",
    "price": ".a-price-whole",
    "rating": ".a-icon-alt .a-icon-alt-text",
    "availability": ".a-color-success"
  },
  "processing_rules": {
    "clean_html": true,
    "validate_required": ["title", "price"],
    "transformations": {
      "price": "number",
      "rating": "float"
    }
  },
  "export_config": {
    "format": "csv",
    "delimiter": ",",
    "encoding": "utf-8"
  },
  "scraper_config": {
    "scraper_type": "static",
    "delay": 2.0,
    "max_retries": 3,
    "timeout": 30
  },
  "is_public": false
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "config": {
      "id": 789,
      "name": "Amazon Product Template",
      "description": "Template for scraping Amazon product pages",
      "is_public": false,
      "usage_count": 0,
      "created_at": "2024-01-15T10:20:00Z"
    }
  },
  "message": "Configuration created successfully"
}
```

### 6.2 List Configurations
```http
GET /configs
```

#### Query Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `is_public`: Filter by public status
- `user_id`: Filter by user ID (admin only)
- `search`: Search in name and description

#### Response
```json
{
  "success": true,
  "data": {
    "configs": [
      {
        "id": 789,
        "name": "Amazon Product Template",
        "description": "Template for scraping Amazon product pages",
        "is_public": false,
        "usage_count": 5,
        "created_at": "2024-01-15T10:20:00Z",
        "updated_at": "2024-01-15T10:20:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 12,
      "pages": 1
    }
  }
}
```

### 6.3 Get Configuration Details
```http
GET /configs/{config_id}
```

#### Response
```json
{
  "success": true,
  "data": {
    "config": {
      "id": 789,
      "name": "Amazon Product Template",
      "description": "Template for scraping Amazon product pages",
      "url_pattern": "https://www.amazon.com/s?k={search_term}",
      "selectors": {
        "title": ".s-result-item .s-link",
        "price": ".a-price-whole",
        "rating": ".a-icon-alt .a-icon-alt-text"
      },
      "processing_rules": {
        "clean_html": true,
        "validate_required": ["title", "price"]
      },
      "export_config": {
        "format": "csv",
        "delimiter": ","
      },
      "scraper_config": {
        "scraper_type": "static",
        "delay": 2.0
      },
      "is_public": false,
      "usage_count": 5,
      "created_at": "2024-01-15T10:20:00Z",
      "updated_at": "2024-01-15T10:20:00Z"
    }
  }
}
```

## 7. Scheduling and Automation

### 7.1 Create Schedule
```http
POST /schedules
```

#### Request Body
```json
{
  "job_id": 123,
  "cron_expression": "0 9 * * 1", // Every Monday at 9 AM
  "timezone": "America/New_York",
  "is_active": true,
  "max_runs": 52, // Run for 52 weeks
  "name": "Weekly Amazon Product Update"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "schedule": {
      "id": 101,
      "job_id": 123,
      "cron_expression": "0 9 * * 1",
      "timezone": "America/New_York",
      "next_run": "2024-01-22T09:00:00-05:00",
      "is_active": true,
      "max_runs": 52,
      "run_count": 0,
      "created_at": "2024-01-15T10:50:00Z"
    }
  },
  "message": "Schedule created successfully"
}
```

### 7.2 List Schedules
```http
GET /schedules
```

#### Response
```json
{
  "success": true,
  "data": {
    "schedules": [
      {
        "id": 101,
        "job_id": 123,
        "job_name": "Amazon Product Scraper",
        "cron_expression": "0 9 * * 1",
        "timezone": "America/New_York",
        "next_run": "2024-01-22T09:00:00-05:00",
        "last_run": "2024-01-15T09:00:00-05:00",
        "is_active": true,
        "run_count": 1,
        "max_runs": 52
      }
    ]
  }
}
```

### 7.3 Update Schedule
```http
PUT /schedules/{schedule_id}
```

#### Request Body
```json
{
  "cron_expression": "0 9 * * 1,3,5", // Monday, Wednesday, Friday
  "is_active": false
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "schedule": {
      "id": 101,
      "cron_expression": "0 9 * * 1,3,5",
      "is_active": false,
      "updated_at": "2024-01-15T11:00:00Z"
    }
  },
  "message": "Schedule updated successfully"
}
```

### 7.4 Delete Schedule
```http
DELETE /schedules/{schedule_id}
```

#### Response
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

## 8. System Monitoring and Statistics

### 8.1 Get System Statistics
```http
GET /stats/system
```

#### Response
```json
{
  "success": true,
  "data": {
    "statistics": {
      "jobs": {
        "total": 1234,
        "pending": 12,
        "running": 3,
        "completed": 1150,
        "failed": 69
      },
      "users": {
        "total": 156,
        "active": 89,
        "new_today": 5
      },
      "performance": {
        "average_processing_time": 125,
        "jobs_per_hour": 45.2,
        "success_rate": 94.4
      },
      "resources": {
        "cpu_usage": 45.6,
        "memory_usage": 67.8,
        "disk_usage": 23.4,
        "active_workers": 3
      }
    },
    "timestamp": "2024-01-15T11:15:00Z"
  }
}
```

### 8.2 Get User Statistics
```http
GET /stats/user
```

#### Response
```json
{
  "success": true,
  "data": {
    "statistics": {
      "jobs": {
        "total": 45,
        "this_month": 12,
        "completed": 38,
        "failed": 7
      },
      "data": {
        "records_extracted": 15420,
        "exports_created": 23,
        "storage_used": "125.4 MB"
      },
      "usage": {
        "api_calls_this_month": 567,
        "rate_limit_remaining": 433,
        "plan": "premium"
      }
    }
  }
}
```

### 8.3 Get Performance Metrics
```http
GET /stats/performance
```

#### Query Parameters
- `period`: Time period (`hour`, `day`, `week`, `month`)
- `metric`: Specific metric (`jobs`, `processing_time`, `success_rate`)

#### Response
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "jobs_completed": 5,
        "average_processing_time": 120,
        "success_rate": 96.0
      },
      {
        "timestamp": "2024-01-15T11:00:00Z",
        "jobs_completed": 8,
        "average_processing_time": 115,
        "success_rate": 97.5
      }
    ],
    "period": "hour",
    "summary": {
      "total_jobs": 13,
      "avg_processing_time": 117.5,
      "avg_success_rate": 96.75
    }
  }
}
```

## 9. API Key Management

### 9.1 Create API Key
```http
POST /api-keys
```

#### Request Body
```json
{
  "name": "Production API Key",
  "permissions": {
    "read": true,
    "write": true,
    "delete": false
  },
  "rate_limit_per_hour": 5000,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "api_key": {
      "id": 456,
      "name": "Production API Key",
      "key": "sk_live_abc123def456ghi789", // Only shown once
      "key_prefix": "sk_live_abc123",
      "permissions": {
        "read": true,
        "write": true,
        "delete": false
      },
      "rate_limit_per_hour": 5000,
      "expires_at": "2024-12-31T23:59:59Z",
      "created_at": "2024-01-15T11:20:00Z"
    }
  },
  "message": "API key created successfully"
}
```

### 9.2 List API Keys
```http
GET /api-keys
```

#### Response
```json
{
  "success": true,
  "data": {
    "api_keys": [
      {
        "id": 456,
        "name": "Production API Key",
        "key_prefix": "sk_live_abc123",
        "permissions": {
          "read": true,
          "write": true,
          "delete": false
        },
        "rate_limit_per_hour": 5000,
        "is_active": true,
        "expires_at": "2024-12-31T23:59:59Z",
        "last_used": "2024-01-15T10:45:00Z",
        "usage_count": 156
      }
    ]
  }
}
```

### 9.3 Revoke API Key
```http
DELETE /api-keys/{api_key_id}
```

#### Response
```json
{
  "success": true,
  "message": "API key revoked successfully"
}
```

## 10. WebSocket API

### 10.1 Real-time Job Updates
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/jobs/123');

// Subscribe to job updates
ws.send(JSON.stringify({
  action: 'subscribe',
  job_id: 123,
  token: 'jwt_token_here'
}));

// Receive updates
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
};
```

#### WebSocket Message Format
```json
{
  "type": "job_update",
  "data": {
    "job_id": 123,
    "status": "running",
    "progress": {
      "current": 150,
      "total": 250,
      "percentage": 60.0
    },
    "performance": {
      "pages_per_minute": 15.2,
      "success_rate": 98.5
    },
    "timestamp": "2024-01-15T10:40:15Z"
  }
}
```

### 10.2 System Notifications
```javascript
// Connect to system notifications
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.send(JSON.stringify({
  action: 'subscribe',
  token: 'jwt_token_here'
}));
```

#### Notification Message Format
```json
{
  "type": "notification",
  "data": {
    "level": "info",
    "title": "Job Completed",
    "message": "Amazon Product Scraper completed successfully",
    "job_id": 123,
    "timestamp": "2024-01-15T10:45:23Z"
  }
}
```

## 11. Error Codes

### 11.1 Authentication Errors
- `AUTH_001`: Invalid credentials
- `AUTH_002`: Token expired
- `AUTH_003`: Invalid token
- `AUTH_004`: Insufficient permissions
- `AUTH_005`: Account locked

### 11.2 Validation Errors
- `VALIDATION_001`: Required field missing
- `VALIDATION_002`: Invalid URL format
- `VALIDATION_003`: Invalid email format
- `VALIDATION_004`: Invalid JSON structure
- `VALIDATION_005`: Invalid cron expression

### 11.3 Job Errors
- `JOB_001`: Job not found
- `JOB_002`: Job already running
- `JOB_003`: Invalid job status transition
- `JOB_004`: Job configuration invalid
- `JOB_005`: Maximum retry limit exceeded

### 11.4 System Errors
- `SYSTEM_001`: Internal server error
- `SYSTEM_002`: Database connection failed
- `SYSTEM_003`: Service unavailable
- `SYSTEM_004`: Rate limit exceeded
- `SYSTEM_005`: Maintenance mode

## 12. SDK Examples

### 12.1 Python SDK
```python
from webscraper import WebScraperClient

# Initialize client
client = WebScraperClient(
    api_key='sk_live_abc123def456',
    base_url='https://api.webscraper.com/v1'
)

# Create job
job = client.jobs.create(
    name='Amazon Scraper',
    url='https://www.amazon.com/s?k=laptops',
    selectors={
        'title': '.s-result-item .s-link',
        'price': '.a-price-whole'
    }
)

# Start job
client.jobs.start(job.id)

# Monitor progress
for update in client.jobs.monitor(job.id):
    print(f"Progress: {update.progress.percentage}%")
    if update.status == 'completed':
        break

# Download results
results = client.jobs.get_results(job.id)
client.exports.download(results.export_id)
```

### 12.2 JavaScript SDK
```javascript
import { WebScraperClient } from 'webscraper-js';

// Initialize client
const client = new WebScraperClient({
  apiKey: 'sk_live_abc123def456',
  baseUrl: 'https://api.webscraper.com/v1'
});

// Create job
const job = await client.jobs.create({
  name: 'Amazon Scraper',
  url: 'https://www.amazon.com/s?k=laptops',
  selectors: {
    title: '.s-result-item .s-link',
    price: '.a-price-whole'
  }
});

// Start job
await client.jobs.start(job.id);

// Monitor with WebSocket
client.jobs.onUpdate(job.id, (update) => {
  console.log(`Progress: ${update.progress.percentage}%`);
  if (update.status === 'completed') {
    client.jobs.offUpdate(job.id);
  }
});
```

This comprehensive API documentation provides complete coverage of all system functionality, enabling developers to integrate the web scraping system into their applications effectively.
