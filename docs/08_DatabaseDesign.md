# Database Design Document

## 1. Database Overview

### 1.1 Database Purpose
The database serves as the central data store for the Web Scraping and Data Extraction Automation System, managing scraping jobs, extracted data, user information, and system logs.

### 1.2 Database Requirements
- **High Performance**: Support for concurrent read/write operations
- **Data Integrity**: ACID compliance for transaction safety
- **Scalability**: Horizontal scaling capability
- **Flexibility**: JSON support for dynamic configurations
- **Security**: Role-based access control and data encryption

### 1.3 Technology Choice
- **Development**: SQLite (MVP) for simplicity and portability
- **Production**: PostgreSQL for enterprise features and performance
- **Cache**: Redis for session management and temporary data

## 2. Database Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Database Architecture                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Application   │    │   ORM Layer     │    │   Database      │           │
│  │                 │    │                 │    │                 │           │
│  │ - FastAPI       │◄──►│ - SQLAlchemy    │◄──►│ - PostgreSQL    │           │
│  │ - Models        │    │ - Migrations    │    │ - Indexes       │           │
│  │ - Sessions      │    │ - Pooling       │    │ - Constraints   │           │
│  │ - Queries       │    │ - Caching       │    │ - Triggers      │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Cache Layer   │    │   Backup        │    │   Monitoring    │           │
│  │                 │    │                 │    │                 │           │
│  │ - Redis         │    │ - Daily Backups │    │ - Performance   │           │
│  │ - Sessions      │    │ - Point-in-Time │    │ - Query Analysis│           │
│  │ - Query Cache   │    │ - Replication   │    │ - Slow Queries  │           │
│  │ - Rate Limits   │    │ - Archive       │    │ - Connection    │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Database Schema Overview
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                Database Schema                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │     Users       │    │      Jobs       │    │    Results      │           │
│  │                 │    │                 │    │                 │           │
│  │ - id (PK)       │    │ - id (PK)       │    │ - id (PK)       │           │
│  │ - username      │    │ - user_id (FK)  │    │ - job_id (FK)   │           │
│  │ - email         │    │ - name          │    │ - url           │           │
│  │ - password_hash │    │ - url           │    │ - raw_data      │           │
│  │ - role          │    │ - selectors     │    │ - processed     │           │
│  │ - created_at    │    │ - config        │    │ - validation    │           │
│  │ - last_login    │    │ - status        │    │ - created_at    │           │
│  │ - is_active     │    │ - priority      │    │                 │           │
│  │                 │    │ - created_at    │    │                 │           │
│  └─────────────────┘    │ - started_at    │    └─────────────────┘           │
│                        │ - completed_at  │                                       │
│  ┌─────────────────┐    │ - records_proc  │    ┌─────────────────┐           │
│  │   Job Configs   │    │ - result_path   │    │      Logs       │           │
│  │                 │    │ - error_msg     │    │                 │           │
│  │ - id (PK)       │    │ - retry_count   │    │ - id (PK)       │           │
│  │ - name          │    │ - max_retries   │    │ - job_id (FK)   │           │
│  │ - url_pattern   │    │                 │    │ - level         │           │
│  │ - selectors     │    └─────────────────┘    │ - message       │           │
│  │ - proc_rules    │                           │ - details       │           │
│  │ - export_conf   │    ┌─────────────────┐    │ - created_at    │           │
│  │ - is_active     │    │   Schedules     │    │                 │           │
│  │ - created_at    │    │                 │    └─────────────────┘           │
│  │ - updated_at    │    │ - id (PK)       │                                       │
│  │                 │    │ - job_id (FK)    │    ┌─────────────────┐           │
│  └─────────────────┘    │ - cron_expr     │    │   Exports      │           │
│                        │ - next_run      │    │                 │           │
│  ┌─────────────────┐    │ - is_active     │    │ - id (PK)       │           │
│  │   API Keys      │    │ - created_at    │    │ - job_id (FK)   │           │
│  │                 │    │                 │    │ - format        │           │
│  │ - id (PK)       │    └─────────────────┘    │ - file_path     │           │
│  │ - user_id (FK)  │                           │ - file_size     │           │
│  │ - key_hash      │    ┌─────────────────┐    │ - download_count│           │
│  │ - name          │    │   System Stats  │    │ - created_at    │           │
│  │ - permissions   │    │                 │    │                 │           │
│  │ - expires_at    │    │ - id (PK)       │    └─────────────────┘           │
│  │ - created_at    │    │ - metric_name   │                                       │
│  │ - last_used     │    │ - metric_value   │    ┌─────────────────┐           │
│  │                 │    │ - timestamp     │    │   Audit Log    │           │
│  └─────────────────┘    │                 │    │                 │           │
│                        └─────────────────┘    │ - id (PK)       │           │
│                                                │ - user_id (FK)  │           │
│                                                │ - action        │           │
│                                                │ - resource      │           │
│                                                │ - details       │           │
│                                                │ - ip_address    │           │
│                                                │ - user_agent    │           │
│                                                │ - timestamp     │           │
│                                                └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 3. Detailed Table Definitions

### 3.1 Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.2 Jobs Table
```sql
CREATE TYPE job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'paused'
);

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    selectors JSONB NOT NULL,
    config JSONB NOT NULL,
    status job_status DEFAULT 'pending',
    priority INTEGER DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_total INTEGER DEFAULT 0,
    result_path TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    estimated_duration INTEGER, -- in minutes
    actual_duration INTEGER, -- in minutes
    tags TEXT[], -- PostgreSQL array for tags
    is_public BOOLEAN DEFAULT FALSE
);

-- Indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_priority ON jobs(priority);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_jobs_started_at ON jobs(started_at);
CREATE INDEX idx_jobs_completed_at ON jobs(completed_at);
CREATE INDEX idx_jobs_tags ON jobs USING GIN(tags);

-- JSON Indexes
CREATE INDEX idx_jobs_selectors ON jobs USING GIN(selectors);
CREATE INDEX idx_jobs_config ON jobs USING GIN(config);

-- Constraints
ALTER TABLE jobs ADD CONSTRAINT chk_jobs_duration 
    CHECK (estimated_duration IS NULL OR estimated_duration > 0);
ALTER TABLE jobs ADD CONSTRAINT chk_jobs_retry_count 
    CHECK (retry_count <= max_retries);
```

### 3.3 Results Table
```sql
CREATE TYPE validation_status AS ENUM (
    'pending',
    'valid',
    'invalid',
    'warning'
);

CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    processed_data JSONB,
    validation_status validation_status DEFAULT 'pending',
    validation_errors JSONB, -- Array of validation error messages
    checksum VARCHAR(64), -- SHA-256 hash for deduplication
    processing_time_ms INTEGER, -- Processing time in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_results_job_id ON results(job_id);
CREATE INDEX idx_results_url ON results(url);
CREATE INDEX idx_results_validation_status ON results(validation_status);
CREATE INDEX idx_results_created_at ON results(created_at);
CREATE INDEX idx_results_checksum ON results(checksum);
CREATE INDEX idx_results_processing_time ON results(processing_time_ms);

-- JSON Indexes
CREATE INDEX idx_results_raw_data ON results USING GIN(raw_data);
CREATE INDEX idx_results_processed_data ON results USING GIN(processed_data);

-- Trigger for updated_at
CREATE TRIGGER update_results_updated_at 
    BEFORE UPDATE ON results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for checksum calculation
CREATE OR REPLACE FUNCTION calculate_checksum()
RETURNS TRIGGER AS $$
BEGIN
    NEW.checksum = encode(sha256(convert_to(NEW.raw_data::text, 'UTF8')), 'hex');
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_results_checksum
    BEFORE INSERT ON results
    FOR EACH ROW EXECUTE FUNCTION calculate_checksum();
```

### 3.4 Job Configs Table
```sql
CREATE TABLE job_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    url_pattern TEXT,
    selectors JSONB NOT NULL,
    processing_rules JSONB,
    export_config JSONB,
    scraper_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_job_configs_user_id ON job_configs(user_id);
CREATE INDEX idx_job_configs_name ON job_configs(name);
CREATE INDEX idx_job_configs_is_active ON job_configs(is_active);
CREATE INDEX idx_job_configs_is_public ON job_configs(is_public);
CREATE INDEX idx_job_configs_usage_count ON job_configs(usage_count DESC);

-- JSON Indexes
CREATE INDEX idx_job_configs_selectors ON job_configs USING GIN(selectors);
CREATE INDEX idx_job_configs_processing_rules ON job_configs USING GIN(processing_rules);
CREATE INDEX idx_job_configs_export_config ON job_configs USING GIN(export_config);

-- Triggers
CREATE TRIGGER update_job_configs_updated_at 
    BEFORE UPDATE ON job_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for usage count
CREATE OR REPLACE FUNCTION increment_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE job_configs 
    SET usage_count = usage_count + 1 
    WHERE id = NEW.config_id;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

### 3.5 Schedules Table
```sql
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    next_run TIMESTAMP,
    last_run TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    max_runs INTEGER, -- NULL for unlimited runs
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_schedules_job_id ON schedules(job_id);
CREATE INDEX idx_schedules_user_id ON schedules(user_id);
CREATE INDEX idx_schedules_next_run ON schedules(next_run);
CREATE INDEX idx_schedules_is_active ON schedules(is_active);

-- Constraints
ALTER TABLE schedules ADD CONSTRAINT chk_schedules_cron 
    CHECK (cron_expression ~ '^(?:[0-5]?\d|\*)\s(?:[01]?\d|2[0-3]|\*)\s(?:[0-2]?\d|3[01]|\*)\s(?:[01]?\d|\*)\s(?:[0-5]?\d|\*)$');
ALTER TABLE schedules ADD CONSTRAINT chk_schedules_runs 
    CHECK (max_runs IS NULL OR run_count <= max_runs);

-- Triggers
CREATE TRIGGER update_schedules_updated_at 
    BEFORE UPDATE ON schedules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.6 Logs Table
```sql
CREATE TYPE log_level AS ENUM (
    'debug',
    'info',
    'warning',
    'error',
    'critical'
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    level log_level NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    context JSONB, -- Additional context information
    source VARCHAR(100), -- Source component (scraper, processor, etc.)
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_logs_job_id ON logs(job_id);
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_created_at ON logs(created_at);
CREATE INDEX idx_logs_source ON logs(source);

-- JSON Indexes
CREATE INDEX idx_logs_details ON logs USING GIN(details);
CREATE INDEX idx_logs_context ON logs USING GIN(context);

-- Partitioning for large log tables (by month)
CREATE TABLE logs_y2024m01 PARTITION OF logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 3.7 Exports Table
```sql
CREATE TYPE export_format AS ENUM (
    'csv',
    'json',
    'xlsx',
    'google_sheets',
    'database'
);

CREATE TABLE exports (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    format export_format NOT NULL,
    file_path TEXT,
    file_name VARCHAR(255),
    file_size BIGINT, -- in bytes
    record_count INTEGER,
    download_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(64) UNIQUE, -- For public sharing
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_downloaded TIMESTAMP
);

-- Indexes
CREATE INDEX idx_exports_job_id ON exports(job_id);
CREATE INDEX idx_exports_user_id ON exports(user_id);
CREATE INDEX idx_exports_format ON exports(format);
CREATE INDEX idx_exports_share_token ON exports(share_token);
CREATE INDEX idx_exports_expires_at ON exports(expires_at);

-- Constraints
ALTER TABLE exports ADD CONSTRAINT chk_exports_file_size 
    CHECK (file_size IS NULL OR file_size > 0);
ALTER TABLE exports ADD CONSTRAINT chk_exports_record_count 
    CHECK (record_count IS NULL OR record_count >= 0);
```

### 3.8 API Keys Table
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(10) NOT NULL, -- First few characters for identification
    permissions JSONB NOT NULL DEFAULT '{"read": true, "write": false}',
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_key_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Constraints
ALTER TABLE api_keys ADD CONSTRAINT chk_api_keys_rate_limit 
    CHECK (rate_limit_per_hour > 0);
```

### 3.9 System Stats Table
```sql
CREATE TABLE system_stats (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB, -- Additional tags for categorization
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_system_stats_metric_name ON system_stats(metric_name);
CREATE INDEX idx_system_stats_timestamp ON system_stats(timestamp);
CREATE INDEX idx_system_stats_tags ON system_stats USING GIN(tags);

-- Unique constraint for time-series data
CREATE UNIQUE INDEX idx_system_stats_unique 
    ON system_stats(metric_name, timestamp, COALESCE((tags::text), '{}'));
```

### 3.10 Audit Log Table
```sql
CREATE TYPE audit_action AS ENUM (
    'create',
    'read',
    'update',
    'delete',
    'login',
    'logout',
    'export',
    'download'
);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    resource_type VARCHAR(50) NOT NULL, -- job, user, config, etc.
    resource_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_ip_address ON audit_log(ip_address);

-- JSON Indexes
CREATE INDEX idx_audit_log_details ON audit_log USING GIN(details);
```

## 4. Database Relationships

### 4.1 Entity Relationship Diagram
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Users    │─────│    Jobs     │─────│   Results   │
│             │ 1..*│             │ 1..*│             │
│ - id (PK)   │     │ - id (PK)   │     │ - id (PK)   │
│ - username  │     │ - user_id   │     │ - job_id    │
│ - email     │     │ - name      │     │ - url       │
│ - password  │     │ - url       │     │ - raw_data  │
│ - role      │     │ - status    │     │ - created   │
│ - created   │     │ - created   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  API Keys   │     │ Schedules   │     │   Exports   │
│             │ 1..*│             │ 1..*│             │
│ - id (PK)   │     │ - id (PK)   │     │ - id (PK)   │
│ - user_id   │     │ - job_id    │     │ - job_id    │
│ - name      │     │ - cron_expr │     │ - format    │
│ - key_hash  │     │ - next_run  │     │ - file_path │
│ - created   │     │ - created   │     │ - created   │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐
│ Job Configs │     │    Logs     │
│             │ 1..*│             │
│ - id (PK)   │     │ - id (PK)   │
│ - name      │     │ - job_id    │
│ - selectors │     │ - level     │
│ - created   │     │ - message   │
└─────────────┘     │ - created   │
       │            └─────────────┘
       │
       ▼
┌─────────────┐
│    Jobs     │
│ 1..*        │
│ - config_id │
└─────────────┘
```

### 4.2 Relationship Definitions

#### One-to-Many Relationships
```sql
-- Users to Jobs (One user has many jobs)
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Jobs to Results (One job has many results)
ALTER TABLE results ADD CONSTRAINT fk_results_job_id 
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;

-- Jobs to Exports (One job has many exports)
ALTER TABLE exports ADD CONSTRAINT fk_exports_job_id 
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;

-- Jobs to Schedules (One job has many schedules)
ALTER TABLE schedules ADD CONSTRAINT fk_schedules_job_id 
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;

-- Jobs to Logs (One job has many logs)
ALTER TABLE logs ADD CONSTRAINT fk_logs_job_id 
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
```

#### Many-to-Many Relationships (via junction tables)
```sql
-- Job Configs usage tracking
CREATE TABLE config_usage (
    config_id INTEGER REFERENCES job_configs(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (config_id, job_id)
);

-- Job Tags (Many-to-many relationship)
CREATE TABLE job_tags (
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    tag_name VARCHAR(50),
    PRIMARY KEY (job_id, tag_name)
);
```

## 5. Database Optimization

### 5.1 Indexing Strategy
```sql
-- Composite indexes for common queries
CREATE INDEX idx_jobs_user_status_created ON jobs(user_id, status, created_at DESC);
CREATE INDEX idx_results_job_validation_created ON results(job_id, validation_status, created_at);
CREATE INDEX idx_logs_job_level_created ON logs(job_id, level, created_at DESC);

-- Partial indexes for better performance
CREATE INDEX idx_active_jobs ON jobs(id) WHERE status IN ('pending', 'running');
CREATE INDEX idx_failed_logs ON logs(id) WHERE level IN ('error', 'critical');
CREATE INDEX idx_recent_exports ON exports(id) WHERE created_at > CURRENT_DATE - INTERVAL '30 days';

-- Functional indexes
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
CREATE INDEX idx_jobs_url_hash ON jobs(md5(url));
```

### 5.2 Partitioning Strategy
```sql
-- Partition logs table by month for better performance
CREATE TABLE logs_partitioned (
    LIKE logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE logs_2024_01 PARTITION OF logs_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE logs_2024_02 PARTITION OF logs_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Partition results table by job_id for large datasets
CREATE TABLE results_partitioned (
    LIKE results INCLUDING ALL
) PARTITION BY HASH (job_id);

-- Create hash partitions
CREATE TABLE results_part_0 PARTITION OF results_partitioned
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE results_part_1 PARTITION OF results_partitioned
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
```

### 5.3 Query Optimization
```sql
-- Materialized views for complex queries
CREATE MATERIALIZED VIEW job_stats AS
SELECT 
    j.id,
    j.name,
    j.status,
    j.created_at,
    COUNT(r.id) as result_count,
    COUNT(CASE WHEN r.validation_status = 'valid' THEN 1 END) as valid_count,
    AVG(r.processing_time_ms) as avg_processing_time,
    MAX(r.created_at) as last_result_at
FROM jobs j
LEFT JOIN results r ON j.id = r.job_id
GROUP BY j.id, j.name, j.status, j.created_at;

-- Refresh materialized view
CREATE OR REPLACE FUNCTION refresh_job_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY job_stats;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh
SELECT cron.schedule('refresh-job-stats', '*/5 * * * *', 'SELECT refresh_job_stats();');
```

## 6. Data Migration and Seeding

### 6.1 Migration Scripts
```sql
-- Migration 001: Initial schema
-- (All tables created above)

-- Migration 002: Add job tags support
ALTER TABLE jobs ADD COLUMN tags TEXT[];
CREATE INDEX idx_jobs_tags ON jobs USING GIN(tags);

-- Migration 003: Add job sharing
ALTER TABLE jobs ADD COLUMN is_public BOOLEAN DEFAULT FALSE;
ALTER TABLE exports ADD COLUMN share_token VARCHAR(64) UNIQUE;
ALTER TABLE exports ADD COLUMN expires_at TIMESTAMP;

-- Migration 004: Add performance metrics
ALTER TABLE results ADD COLUMN processing_time_ms INTEGER;
ALTER TABLE jobs ADD COLUMN estimated_duration INTEGER;
ALTER TABLE jobs ADD COLUMN actual_duration INTEGER;
```

### 6.2 Seed Data
```sql
-- Create admin user
INSERT INTO users (username, email, password_hash, role, first_name, last_name, is_active, email_verified)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LFvOa', -- password: admin123
    'admin',
    'System',
    'Administrator',
    TRUE,
    TRUE
);

-- Create sample job config
INSERT INTO job_configs (name, description, user_id, url_pattern, selectors, processing_rules, export_config)
VALUES (
    'Amazon Product Scraper',
    'Basic Amazon product information scraper',
    1,
    'https://www.amazon.com/s?k=%s',
    '{"title": ".s-result-item .s-link", "price": ".a-price-whole", "rating": ".a-icon-alt .a-icon-alt-text"}',
    '{"clean_html": true, "validate_required": ["title", "price"]}',
    '{"format": "csv", "delimiter": ",", "encoding": "utf-8"}'
);

-- Create sample system stats
INSERT INTO system_stats (metric_name, metric_value, metric_unit, tags)
VALUES 
    ('total_jobs', 0, 'count', '{"type": "system"}'),
    ('active_jobs', 0, 'count', '{"type": "system"}'),
    ('total_users', 1, 'count', '{"type": "system"}'),
    ('system_uptime', 100, 'percent', '{"type": "system"}');
```

## 7. Backup and Recovery

### 7.1 Backup Strategy
```bash
#!/bin/bash
# Daily backup script

# Variables
DB_NAME="scraper_db"
DB_USER="scraper_user"
BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/scraper_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "scraper_backup_*.sql.gz" -mtime +30 -delete

# Log backup
echo "Backup completed: $BACKUP_FILE.gz" >> /var/log/scraper_backup.log
```

### 7.2 Point-in-Time Recovery
```sql
-- Enable WAL archiving
-- In postgresql.conf:
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

-- Recovery configuration
-- In recovery.conf:
-- restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
-- recovery_target_time = '2024-01-15 14:30:00'
-- recovery_target_inclusive = true
```

## 8. Security and Access Control

### 8.1 Row-Level Security
```sql
-- Enable RLS on sensitive tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
ALTER TABLE exports ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY jobs_user_policy ON jobs
    FOR ALL TO authenticated_user
    USING (user_id = current_user_id() OR is_public = TRUE);

CREATE POLICY results_user_policy ON results
    FOR ALL TO authenticated_user
    USING (job_id IN (
        SELECT id FROM jobs WHERE user_id = current_user_id() OR is_public = TRUE
    ));

-- Admin can access all data
CREATE POLICY jobs_admin_policy ON jobs
    FOR ALL TO admin_role
    USING (true);
```

### 8.2 Data Encryption
```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(encrypt(data::bytea, 'encryption_key', 'aes'), 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN convert_from(decrypt(decode(encrypted_data, 'base64'), 'encryption_key', 'aes'), 'UTF8');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 9. Monitoring and Maintenance

### 9.1 Performance Monitoring
```sql
-- Query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Slow query log
-- In postgresql.conf:
-- log_min_duration_statement = 1000  # Log queries taking more than 1 second
-- log_checkpoints = on
-- log_connections = on
-- log_disconnections = on
-- log_lock_waits = on

-- Monitoring queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### 9.2 Maintenance Tasks
```sql
-- Automatic vacuum and analyze
-- In postgresql.conf:
-- autovacuum = on
-- autovacuum_vacuum_scale_factor = 0.1
-- autovacuum_analyze_scale_factor = 0.05

-- Custom maintenance function
CREATE OR REPLACE FUNCTION maintenance_tasks()
RETURNS void AS $$
BEGIN
    -- Update table statistics
    ANALYZE jobs;
    ANALYZE results;
    ANALYZE logs;
    
    -- Rebuild indexes if needed
    REINDEX INDEX CONCURRENTLY idx_jobs_user_status_created;
    
    -- Clean up old data
    DELETE FROM logs WHERE created_at < CURRENT_DATE - INTERVAL '90 days';
    DELETE FROM audit_log WHERE created_at < CURRENT_DATE - INTERVAL '1 year';
    
    -- Update materialized views
    REFRESH MATERIALIZED VIEW CONCURRENTLY job_stats;
    
    RAISE NOTICE 'Maintenance tasks completed';
END;
$$ LANGUAGE plpgsql;

-- Schedule maintenance
SELECT cron.schedule('maintenance-tasks', '0 2 * * *', 'SELECT maintenance_tasks();');
```

This comprehensive database design provides a robust, scalable, and secure foundation for the web scraping system, supporting all required functionality while ensuring data integrity and performance.
