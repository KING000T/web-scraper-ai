-- Database Initialization Script
-- This script initializes the database with basic tables and data

-- Create users table (if using PostgreSQL)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, is_admin, is_active)
VALUES ('admin', 'admin@webscraper.ai', 'pbkdf2:sha256:260000$salt$hash', 'System Administrator', TRUE, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create sample data for testing
INSERT INTO users (username, email, password_hash, full_name, is_admin, is_active)
VALUES ('demo', 'demo@webscraper.ai', 'pbkdf2:sha256:260000$salt$hash', 'Demo User', FALSE, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create settings table for configuration
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT INTO settings (key, value, description)
VALUES 
    ('max_concurrent_jobs', '5', 'Maximum number of concurrent scraping jobs'),
    ('default_delay', '1.0', 'Default delay between requests in seconds'),
    ('max_file_size', '16777216', 'Maximum file size for uploads in bytes'),
    ('backup_retention_days', '30', 'Number of days to keep backups'),
    ('log_retention_days', '7', 'Number of days to keep log files')
ON CONFLICT (key) DO NOTHING;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- Create notification table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    read BOOLEAN DEFAULT FALSE,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- Create API key table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Create system metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    unit VARCHAR(50),
    tags JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for system metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    COUNT(j.id) as total_jobs,
    COUNT(CASE WHEN j.status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN j.status = 'failed' THEN 1 END) as failed_jobs,
    AVG(j.success_rate) as avg_success_rate,
    MAX(j.created_at) as last_job_date
FROM users u
LEFT JOIN jobs j ON u.id = j.user_id
GROUP BY u.id, u.username, u.email, u.created_at;

-- Create view for system statistics
CREATE OR REPLACE VIEW system_stats AS
SELECT 
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN status = 'running' THEN 1 END) as active_jobs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
    AVG(success_rate) as avg_success_rate,
    COUNT(*) as total_users,
    COUNT(CASE WHEN is_admin = TRUE THEN 1 END) as admin_users
FROM jobs
CROSS JOIN users;

-- Grant permissions (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON users TO webscraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON settings TO webscraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON audit_log TO webscraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON notifications TO webscraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO webscraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON system_metrics TO webscraper_user;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO webscraper_user;
GRANT SELECT ON user_stats TO webscraper_user;
GRANT SELECT ON system_stats TO webscraper_user;

-- Create sample data for testing
INSERT INTO settings (key, value, description)
VALUES 
    ('system_version', '1.0.0', 'Current system version'),
    ('maintenance_mode', 'false', 'System maintenance mode'),
    ('registration_enabled', 'true', 'Allow user registration'),
    ('api_rate_limit', '100', 'API rate limit per hour')
ON CONFLICT (key) DO NOTHING;

-- Create sample notifications for demo user
INSERT INTO notifications (user_id, title, message, type, data)
SELECT 
    u.id,
    'Welcome to Web Scraper AI',
    'Thank you for using Web Scraper AI! This is a demo notification to show how the system works.',
    'info',
    '{"source": "system", "type": "welcome"}'
FROM users u WHERE u.username = 'demo'
ON CONFLICT DO NOTHING;

-- Create sample metrics
INSERT INTO system_metrics (metric_name, metric_value, unit, tags)
VALUES 
    ('cpu_usage', 25.5, 'percent', '{"host": "web-server"}'),
    ('memory_usage', 45.2, 'percent', '{"host": "web-server"}'),
    ('disk_usage', 67.8, 'percent', '{"host": "web-server"}'),
    ('active_connections', 12, 'count', '{"host": "web-server"}')
ON CONFLICT DO NOTHING;

-- Create sample audit log entries
INSERT INTO audit_log (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
SELECT 
    u.id,
    'login',
    'user',
    u.id,
    '{"method": "password", "success": true}',
    '127.0.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
FROM users u WHERE u.username = 'demo'
ON CONFLICT DO NOTHING;

-- Output initialization complete message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
    RAISE NOTICE 'Default admin user created: admin / admin123';
    RAISE NOTICE 'Demo user created: demo / demo123';
END $$;
