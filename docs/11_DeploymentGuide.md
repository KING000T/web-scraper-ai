# Deployment Guide

## 1. Deployment Overview

### 1.1 Deployment Options
The Web Scraping System supports multiple deployment strategies:

- **Local Development**: Single-machine setup with SQLite
- **Docker Container**: Containerized deployment for consistency
- **Cloud Deployment**: Scalable cloud infrastructure (AWS, GCP, Azure)
- **On-Premises**: Enterprise data center deployment

### 1.2 System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB available space
- **Network**: Stable internet connection
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+

#### Recommended Requirements
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: High-speed internet with proxy support
- **OS**: Ubuntu 22.04 LTS

#### Production Requirements
- **CPU**: 8+ cores
- **Memory**: 16GB+ RAM
- **Storage**: 500GB+ SSD with backup
- **Network**: Enterprise-grade with load balancing
- **OS**: Ubuntu 22.04 LTS or RHEL 8+

### 1.3 Dependencies
- **Python**: 3.8+
- **Node.js**: 16+ (for frontend)
- **PostgreSQL**: 13+ (production)
- **Redis**: 6+ (caching and task queue)
- **Docker**: 20.10+ (container deployment)
- **Docker Compose**: 2.0+ (multi-container)

## 2. Local Development Setup

### 2.1 Prerequisites Installation

#### Ubuntu/Debian
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install python3 python3-pip python3-venv git -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install system dependencies
sudo apt install build-essential libpq-dev -y
```

#### macOS
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Install Node.js
brew install node@18

# Install PostgreSQL
brew install postgresql@13

# Install Redis
brew install redis

# Start services
brew services start postgresql@13
brew services start redis
```

#### Windows
```powershell
# Install Chocolatey if not present
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Python
choco install python --version=3.10.8

# Install Node.js
choco install nodejs --version=18.12.1

# Install PostgreSQL
choco install postgresql13

# Install Redis
choco install redis-64
```

### 2.2 Application Setup

#### Clone Repository
```bash
git clone https://github.com/your-org/web-scraper-ai.git
cd web-scraper-ai
```

#### Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Install Dependencies
```bash
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

#### Database Setup
```bash
# Create database user
sudo -u postgres createuser --interactive web_scraper

# Create database
sudo -u postgres createdb -O web_scraper web_scraper_dev

# Run migrations
python manage.py db upgrade

# Load seed data
python manage.py seed
```

#### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

#### Environment Variables (.env)
```bash
# Application Settings
APP_NAME=Web Scraper
DEBUG=True
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Database Settings
DATABASE_URL=postgresql://web_scraper:password@localhost:5432/web_scraper_dev

# Redis Settings
REDIS_URL=redis://localhost:6379/0

# Email Settings (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Storage
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# Scraping Settings
DEFAULT_DELAY=1.0
MAX_CONCURRENT_JOBS=5
USER_AGENT=WebScraper/1.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 2.3 Running the Application

#### Development Server
```bash
# Start backend server
python main.py

# Start frontend development server (in separate terminal)
cd frontend
npm start
```

#### Using Gunicorn (Production-like)
```bash
# Install Gunicorn
pip install gunicorn

# Start application
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Start with configuration file
gunicorn -c gunicorn.conf.py main:app
```

#### Gunicorn Configuration (gunicorn.conf.py)
```python
# Gunicorn configuration
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "web_scraper"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

## 3. Docker Deployment

### 3.1 Dockerfile

#### Backend Dockerfile
```dockerfile
# Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 3.2 Docker Compose

#### Development Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: web_scraper_dev
      POSTGRES_USER: web_scraper
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U web_scraper"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build: .
    environment:
      - DATABASE_URL=postgresql://web_scraper:password@postgres:5432/web_scraper_dev
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=True
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  # Celery Worker
  worker:
    build: .
    command: celery -A worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://web_scraper:password@postgres:5432/web_scraper_dev
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

  # Celery Beat (Scheduler)
  beat:
    build: .
    command: celery -A worker beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://web_scraper:password@postgres:5432/web_scraper_dev
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/var/www/static
    depends_on:
      - backend
      - frontend

  # PostgreSQL Database
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: web_scraper
      POSTGRES_USER: web_scraper
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  # Redis Cluster
  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Backend API (Multiple instances)
  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=postgresql://web_scraper:${POSTGRES_PASSWORD}@postgres:5432/web_scraper
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - static_files:/app/static
      - upload_files:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    volumes:
      - static_files:/var/www/static
    restart: unless-stopped

  # Celery Workers
  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A worker worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://web_scraper:${POSTGRES_PASSWORD}@postgres:5432/web_scraper
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - upload_files:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning

volumes:
  postgres_data:
  redis_data:
  static_files:
  upload_files:
  prometheus_data:
  grafana_data:
```

### 3.3 Docker Deployment Commands

#### Development Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# Scale services
docker-compose up --scale worker=3 -d
```

#### Production Deployment
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose -f docker-compose.prod.yml exec backend python manage.py db upgrade

# Create admin user
docker-compose -f docker-compose.prod.yml exec backend python manage.py create-admin

# View status
docker-compose -f docker-compose.prod.yml ps

# Update services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 4. Cloud Deployment

### 4.1 AWS Deployment

#### Infrastructure as Code (Terraform)
```hcl
# terraform/main.tf
provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "web-scraper-vpc"
  }
}

# Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "web-scraper-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "web-scraper-private-${count.index + 1}"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "web-scraper-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "web-scraper"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "web-scraper"
      image = "${aws_ecr_repository.app.repository_url}:latest"
      
      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://${aws_db_instance.main.username}:${aws_db_instance.main.password}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
        },
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_cluster.main.redis_endpoint.endpoint}:6379/0"
        }
      ]

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "web-scraper-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Environment = var.environment
  }
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier     = "web-scraper-db"
  engine         = "postgres"
  engine_version = "13.7"
  instance_class = "db.t3.medium"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true
  
  db_name  = "web_scraper"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "web-scraper-final-snapshot"
  
  tags = {
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "web-scraper-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "web-scraper-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}
```

#### Deployment Script (AWS)
```bash
#!/bin/bash
# deploy-aws.sh

set -e

# Configuration
AWS_REGION="us-west-2"
ECR_REPOSITORY="web-scraper"
ECS_CLUSTER="web-scraper-cluster"
ECS_SERVICE="web-scraper-service"

# Build and push Docker image
echo "Building Docker image..."
docker build -t $ECR_REPOSITORY:latest .

# Get AWS ECR login
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push image
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

docker tag $ECR_REPOSITORY:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment

# Wait for deployment
echo "Waiting for deployment to complete..."
aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE

echo "Deployment completed successfully!"
```

### 4.2 Google Cloud Platform Deployment

#### Kubernetes Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: web-scraper

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-scraper-config
  namespace: web-scraper
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "web_scraper"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: web-scraper-secrets
  namespace: web-scraper
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded-password>
  SECRET_KEY: <base64-encoded-secret>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>

---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: web-scraper
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: web-scraper-config
              key: DATABASE_NAME
        - name: POSTGRES_USER
          value: web_scraper
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: web-scraper-secrets
              key: DATABASE_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi

---
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: web-scraper
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-scraper-backend
  namespace: web-scraper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-scraper-backend
  template:
    metadata:
      labels:
        app: web-scraper-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project/web-scraper:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://web_scraper:$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)"
        - name: REDIS_URL
          value: "redis://$(REDIS_HOST):$(REDIS_PORT)/0"
        envFrom:
        - configMapRef:
            name: web-scraper-config
        - secretRef:
            name: web-scraper-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-scraper-service
  namespace: web-scraper
spec:
  selector:
    app: web-scraper-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-scraper-ingress
  namespace: web-scraper
  annotations:
    kubernetes.io/ingress.class: "gce"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.webscraper.com
    secretName: web-scraper-tls
  rules:
  - host: api.webscraper.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-scraper-service
            port:
              number: 80
```

#### GCP Deployment Script
```bash
#!/bin/bash
# deploy-gcp.sh

set -e

# Configuration
PROJECT_ID="your-gcp-project"
CLUSTER_NAME="web-scraper-cluster"
ZONE="us-central1-a"
IMAGE_NAME="web-scraper"

# Build and push image to GCR
echo "Building Docker image..."
docker build -t $IMAGE_NAME:latest .

# Tag for GCR
docker tag $IMAGE_NAME:latest gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# Push to GCR
echo "Pushing to GCR..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/

# Wait for deployment
echo "Waiting for deployment..."
kubectl rollout status deployment/web-scraper-backend -n web-scraper

echo "Deployment completed successfully!"
```

## 5. Monitoring and Logging

### 5.1 Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'web-scraper'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 5.2 Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Web Scraper Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Jobs",
        "type": "singlestat",
        "targets": [
          {
            "expr": "scraping_jobs_active",
            "legendFormat": "Active Jobs"
          }
        ]
      }
    ]
  }
}
```

### 5.3 Log Aggregation (ELK Stack)
```yaml
# logging/elasticsearch.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    ports:
      - "5044:5044"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## 6. Backup and Recovery

### 6.1 Database Backup Script
```bash
#!/bin/bash
# scripts/backup-db.sh

set -e

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="web_scraper"
DB_USER="web_scraper"
BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/web_scraper_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
echo "Starting database backup..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "web_scraper_backup_*.sql.gz" -mtime +30 -delete

# Verify backup
if [ -f "${BACKUP_FILE}.gz" ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}.gz"
else
    echo "Backup failed!"
    exit 1
fi

# Upload to cloud storage (optional)
if [ -n "$AWS_S3_BUCKET" ]; then
    aws s3 cp "${BACKUP_FILE}.gz" "s3://$AWS_S3_BUCKET/backups/"
    echo "Backup uploaded to S3"
fi
```

### 6.2 Automated Backup (Cron)
```bash
# Add to crontab: crontab -e
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup-db.sh

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /path/to/scripts/full-backup.sh

# Hourly incremental backup
0 * * * * /path/to/scripts/incremental-backup.sh
```

### 6.3 Recovery Script
```bash
#!/bin/bash
# scripts/restore-db.sh

set -e

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="web_scraper"
DB_USER="web_scraper"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Drop existing database
echo "Dropping existing database..."
psql -h $DB_HOST -p $DB_PORT -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME"

# Create new database
echo "Creating new database..."
psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER"

# Restore backup
echo "Restoring database from backup..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
else
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < "$BACKUP_FILE"
fi

echo "Database restored successfully!"
```

## 7. Security Configuration

### 7.1 SSL/TLS Configuration
```nginx
# nginx/nginx.conf
server {
    listen 443 ssl http2;
    server_name api.webscraper.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.2 Firewall Configuration
```bash
#!/bin/bash
# scripts/setup-firewall.sh

# Allow SSH
ufw allow 22

# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Allow application ports (if needed)
ufw allow 8000

# Allow database access from specific IPs only
ufw allow from 10.0.0.0/8 to any port 5432
ufw allow from 172.16.0.0/12 to any port 5432
ufw allow from 192.168.0.0/16 to any port 5432

# Enable firewall
ufw --force enable

# Show status
ufw status verbose
```

### 7.3 Security Hardening
```bash
#!/bin/bash
# scripts/security-hardening.sh

# Update system packages
apt update && apt upgrade -y

# Install security tools
apt install -y fail2ban ufw unattended-upgrades

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF

# Enable unattended upgrades
dpkg-reconfigure -plow unattended-upgrades

# Configure automatic security updates
cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Only-Install-If "New-Kernel-Package";
EOF

# Restart services
systemctl restart fail2ban
systemctl restart unattended-upgrades

echo "Security hardening completed!"
```

## 8. Troubleshooting

### 8.1 Common Issues and Solutions

#### Database Connection Issues
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check connection
psql -h localhost -U web_scraper -d web_scraper_dev -c "SELECT 1;"

# Reset PostgreSQL
sudo systemctl restart postgresql
sudo -u postgres psql -c "ALTER USER web_scraper PASSWORD 'new_password';"
```

#### Redis Connection Issues
```bash
# Check Redis status
systemctl status redis

# Test connection
redis-cli ping

# Clear Redis cache
redis-cli flushall
```

#### Application Startup Issues
```bash
# Check logs
tail -f logs/app.log

# Check port availability
netstat -tlnp | grep :8000

# Kill existing processes
pkill -f gunicorn
pkill -f python
```

#### Docker Issues
```bash
# Check container status
docker ps -a

# View container logs
docker logs <container_name>

# Restart containers
docker-compose restart

# Clean up
docker system prune -a
```

### 8.2 Performance Tuning

#### Database Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM jobs WHERE status = 'running';

-- Create indexes
CREATE INDEX CONCURRENTLY idx_jobs_status_created ON jobs(status, created_at);

-- Update statistics
ANALYZE jobs;

-- Check database size
SELECT pg_size_pretty(pg_database_size('web_scraper'));
```

#### Application Optimization
```python
# Gunicorn tuning
# gunicorn.conf.py
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

This comprehensive deployment guide provides all necessary information for deploying the web scraping system in various environments, from local development to production cloud infrastructure.
