/**
 * Web Scraper AI Dashboard JavaScript
 * Frontend functionality for the web scraping dashboard
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Global state
let currentSection = 'dashboard';
let wsConnection = null;
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupNavigation();
    setupWebSocket();
    loadDashboardData();
});

// Initialize dashboard
function initializeDashboard() {
    console.log('Dashboard initialized');
    
    // Setup event listeners
    setupFormListeners();
    setupModalListeners();
    
    // Initialize charts
    initializeCharts();
    
    // Load initial data
    loadJobsData();
    loadExportsData();
}

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('href').substring(1);
            showSection(section);
        });
    });
}

function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('active');
        
        // Update navigation
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${sectionId}`) {
                link.classList.add('active');
            }
        });
        
        currentSection = sectionId;
        
        // Load section-specific data
        loadSectionData(sectionId);
    }
}

function loadSectionData(sectionId) {
    switch(sectionId) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'jobs':
            loadJobsData();
            break;
        case 'scrapers':
            // No additional data needed for scrapers
            break;
        case 'exports':
            loadExportsData();
            break;
        case 'monitoring':
            loadMonitoringData();
            break;
    }
}

// WebSocket connection
function setupWebSocket() {
    try {
        wsConnection = new WebSocket('ws://localhost:8000/ws/realtime');
        
        wsConnection.onopen = function() {
            console.log('WebSocket connected');
            showNotification('Connected to real-time updates', 'success');
        };
        
        wsConnection.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        wsConnection.onclose = function() {
            console.log('WebSocket disconnected');
            setTimeout(setupWebSocket, 5000); // Reconnect after 5 seconds
        };
        
        wsConnection.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    } catch (error) {
        console.error('WebSocket setup error:', error);
    }
}

function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'metrics':
            updateMetrics(data.data);
            break;
        case 'job_update':
            updateJobStatus(data.data);
            break;
        case 'alert':
            showAlert(data.data);
            break;
        default:
            console.log('Unknown WebSocket message type:', data.type);
    }
}

// API Functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// Dashboard Data Loading
async function loadDashboardData() {
    try {
        // Load job statistics
        const stats = await apiCall('/jobs/statistics');
        updateDashboardStats(stats);
        
        // Load recent jobs
        const recentJobs = await apiCall('/jobs?per_page=10');
        updateRecentJobsTable(recentJobs);
        
        // Update charts
        updateCharts(stats);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Error loading dashboard data', 'error');
    }
}

function updateDashboardStats(stats) {
    document.getElementById('total-jobs').textContent = stats.total_jobs || 0;
    document.getElementById('active-jobs').textContent = stats.active_jobs || 0;
    document.getElementById('completed-jobs').textContent = stats.completed_jobs || 0;
    document.getElementById('failed-jobs').textContent = stats.failed_jobs || 0;
}

function updateRecentJobsTable(jobs) {
    const tbody = document.querySelector('#recent-jobs-table tbody');
    tbody.innerHTML = '';
    
    jobs.forEach(job => {
        const row = createJobRow(job);
        tbody.appendChild(row);
    });
}

function createJobRow(job) {
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td>${job.name}</td>
        <td><span class="badge ${getStatusClass(job.status)}">${job.status}</span></td>
        <td>${formatDate(job.created_at)}</td>
        <td>
            <div class="progress job-progress">
                <div class="progress-bar" style="width: ${job.success_rate}%"></div>
            </div>
            <small>${job.success_rate}%</small>
        </td>
        <td>
            <button class="btn btn-sm btn-action btn-primary" onclick="viewJob(${job.id})">
                <i class="fas fa-eye"></i>
            </button>
            ${job.status === 'running' ? 
                `<button class="btn btn-sm btn-action btn-warning" onclick="stopJob(${job.id})">
                    <i class="fas fa-stop"></i>
                </button>` : ''
            }
        </td>
    `;
    
    return row;
}

function getStatusClass(status) {
    const statusClasses = {
        'pending': 'status-pending',
        'running': 'status-running',
        'completed': 'status-completed',
        'failed': 'status-failed',
        'cancelled': 'status-cancelled'
    };
    
    return statusClasses[status] || 'status-pending';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Jobs Management
async function loadJobsData() {
    try {
        const jobs = await apiCall('/jobs');
        updateJobsTable(jobs);
    } catch (error) {
        console.error('Error loading jobs:', error);
        showNotification('Error loading jobs', 'error');
    }
}

function updateJobsTable(jobs) {
    const tbody = document.querySelector('#jobs-table tbody');
    tbody.innerHTML = '';
    
    jobs.forEach(job => {
        const row = createJobRow(job);
        tbody.appendChild(row);
    });
}

async function createJob() {
    const form = document.getElementById('create-job-form');
    const formData = new FormData(form);
    
    const jobData = {
        name: formData.get('name'),
        url: formData.get('url'),
        scraper_type: formData.get('scraper_type'),
        priority: formData.get('priority'),
        delay: parseFloat(formData.get('delay')),
        max_retries: parseInt(formData.get('retries')),
        selectors: JSON.parse(formData.get('selectors'))
    };
    
    try {
        const result = await apiCall('/jobs', {
            method: 'POST',
            body: JSON.stringify(jobData)
        });
        
        showNotification('Job created successfully', 'success');
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('createJobModal'));
        modal.hide();
        
        // Reload jobs data
        loadJobsData();
        
        // Reset form
        form.reset();
        
    } catch (error) {
        console.error('Error creating job:', error);
        showNotification('Error creating job', 'error');
    }
}

async function viewJob(jobId) {
    try {
        const job = await apiCall(`/jobs/${jobId}`);
        showJobDetails(job);
    } catch (error) {
        console.error('Error viewing job:', error);
        showNotification('Error viewing job', 'error');
    }
}

async function stopJob(jobId) {
    if (!confirm('Are you sure you want to stop this job?')) {
        return;
    }
    
    try {
        await apiCall(`/jobs/${jobId}/stop`, {
            method: 'POST'
        });
        
        showNotification('Job stopped successfully', 'success');
        loadJobsData();
    } catch (error) {
        console.error('Error stopping job:', error);
        showNotification('Error stopping job', 'error');
    }
}

// Scraping Functions
async function quickScrape() {
    const form = document.getElementById('quick-scrape-form');
    const formData = new FormData(form);
    
    const scrapeData = {
        url: formData.get('scrape-url'),
        selectors: JSON.parse(formData.get('scrape-selectors')),
        scraper_type: formData.get('scrape-type')
    };
    
    try {
        showLoading('scraping-results');
        
        const result = await apiCall('/scrapers/scrape', {
            method: 'POST',
            body: JSON.stringify(scrapeData)
        });
        
        displayScrapingResults(result);
        
    } catch (error) {
        console.error('Error scraping:', error);
        showNotification('Error scraping data', 'error');
        hideLoading('scraping-results');
    }
}

function displayScrapingResults(results) {
    const resultsDiv = document.getElementById('scraping-results-content');
    const resultsSection = document.getElementById('scraping-results');
    
    if (results.success) {
        resultsDiv.innerHTML = `
            <div class="alert alert-success">
                <h6>Scraping Successful!</h6>
                <p>Records extracted: ${results.record_count}</p>
                <p>Processing time: ${results.extraction_time}s</p>
                <div class="mt-3">
                    <h6>Sample Data:</h6>
                    <pre class="bg-light p-3 rounded">${JSON.stringify(results.data[0], null, 2)}</pre>
                </div>
            </div>
        `;
    } else {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <h6>Scraping Failed</h6>
                <p>${results.error_message}</p>
            </div>
        `;
    }
    
    resultsSection.style.display = 'block';
    hideLoading('scraping-results');
}

async function validateSelectors() {
    const url = document.getElementById('scrape-url').value;
    const selectors = document.getElementById('scrape-selectors').value;
    
    if (!url || !selectors) {
        showNotification('Please provide URL and selectors', 'warning');
        return;
    }
    
    try {
        const result = await apiCall('/scrapers/validate-selectors', {
            method: 'POST',
            body: JSON.stringify({
                url: url,
                selectors: JSON.parse(selectors)
            })
        });
        
        if (result.validation_results) {
            let message = 'Selectors validation:\n';
            for (const [field, validation] of Object.entries(result.validation_results)) {
                message += `\n${field}: ${validation.valid ? '✓' : '✗'} (${validation.count} items)`;
            }
            
            showNotification(message, result.validation_results.every(v => v.valid) ? 'success' : 'warning');
        }
        
    } catch (error) {
        console.error('Error validating selectors:', error);
        showNotification('Error validating selectors', 'error');
    }
}

// Exports Management
async function loadExportsData() {
    try {
        const exports = await apiCall('/exports/list');
        updateExportsTable(exports);
        
        // Populate job dropdown in export modal
        populateJobDropdown(exports);
        
    } catch (error) {
        console.error('Error loading exports:', error);
        showNotification('Error loading exports', 'error');
    }
}

function updateExportsTable(exports) {
    const tbody = document.querySelector('#exports-table tbody');
    tbody.innerHTML = '';
   
    exports.forEach(export => {
        const row = createExportRow(export);
        tbody.appendChild(row);
    });
}

function createExportRow(export) {
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td>${export.job_name}</td>
        <td><span class="badge bg-secondary">${export.format}</span></td>
        <td>${formatFileSize(export.file_size)}</td>
        <td>${export.record_count}</td>
        <td>${formatDate(export.created_at)}</td>
        <td>
            <button class="btn btn-sm btn-action btn-success" onclick="downloadExport('${export.file_name}')">
                <i class="fas fa-download"></i>
            </button>
            <button class="btn btn-sm btn-action btn-danger" onclick="deleteExport('${export.file_name}')">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    return row;
} 

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function populateJobDropdown(exports) {
    const select = document.getElementById('export-job');
    select.innerHTML = '<option value="">Select a job...</option>';
    
    // Get unique job names
    const jobNames = [...new Set(exports.map(exp => exp.job_name))];
    jobNames.forEach(jobName => {
        const option = document.createElement('option');
        option.value = jobName;
        option.textContent = jobName;
        select.appendChild(option);
    });
}

async function exportData() {
    const jobName = document.getElementById('export-job').value;
    const format = document.getElementById('export-format').value;
    const filename = document.getElementById('export-filename').value;
    
    if (!jobName) {
        showNotification('Please select a job', 'warning');
        return;
    }
    
    try {
        const result = await apiCall('/exports/export', {
            method: 'POST',
            body: JSON.stringify({
                job_name: jobName,
                format: format,
                filename: filename
            })
        });
        
        if (result.success) {
            showNotification('Export completed successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('exportModal'));
            modal.hide();
            
            // Reload exports data
            loadExportsData();
        } else {
            showNotification('Export failed', 'error');
        }
        
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('Error exporting data', 'error');
    }
}

async function downloadExport(filename) {
    try {
        window.open(`${API_BASE_URL}/exports/download/${filename}`, '_blank');
    } catch (error) {
        console.error('Error downloading export:', error);
        showNotification('Error downloading export', 'error');
    }
}

async function deleteExport(filename) {
    if (!confirm('Are you sure you want to delete this export?')) {
        return;
    }
    
    try {
        await apiCall(`/exports/delete/${filename}`, {
            method: 'DELETE'
        });
        
        showNotification('Export deleted successfully', 'success');
        loadExportsData();
    } catch (error) {
        console.error('Error deleting export:', error);
        showNotification('Error deleting export', 'error');
    }
}

// Monitoring Functions
async function loadMonitoringData() {
    try {
        const metrics = await apiCall('/monitoring/metrics');
        updateMetrics(metrics);
        
        const health = await apiCall('/health');
        updateHealthStatus(health);
        
    } catch (error) {
        console.error('Error loading monitoring data:', error);
        showNotification('Error loading monitoring data', 'error');
    }
}

function updateMetrics(metrics) {
    // Update CPU usage
    const cpuUsage = metrics.cpu ? metrics.cpu.usage_percent : 0;
    document.getElementById('cpu-usage').textContent = cpuUsage.toFixed(1) + '%';
    document.getElementById('cpu-progress').style.width = cpuUsage + '%';
    
    // Update memory usage
    const memoryUsage = metrics.memory ? metrics.memory.percent : 0;
    document.getElementById('memory-usage').textContent = memoryUsage.toFixed(1) + '%';
    document.getElementById('memory-progress').style.width = memoryUsage + '%';
    
    // Update disk usage
    const diskUsage = metrics.disk ? metrics.disk.percent : 0;
    document.getElementById('disk-usage').textContent = diskUsage.toFixed(1) + '%';
    document.getElementById('disk-progress').style.width = diskUsage + '%';
    
    // Update queue size
    const queueSize = metrics.system ? metrics.system.process_count : 0;
    document.getElementById('queue-size').textContent = queueSize;
}

function updateHealthStatus(health) {
    // Update database status
    const dbStatus = document.getElementById('db-status');
    const dbDetails = document.getElementById('db-details');
    
    if (health.database_status === 'healthy') {
        dbStatus.className = 'badge bg-success';
        dbStatus.textContent = 'Connected';
    } else {
        dbStatus.className = 'badge bg-danger';
        dbStatus.textContent = 'Disconnected';
    }
    
    // Update queue status
    const queueStatus = document.getElementById('queue-status');
    const queueDetails = document.getElementById('queue-details');
    
    if (health.queue_status === 'healthy') {
        queueStatus.className = 'badge bg-success';
        queueStatus.textContent = 'Healthy';
    } else {
        queueStatus.className = 'badge bg-danger';
        queueStatus.textContent = 'Unhealthy';
    }
}

async function refreshMetrics() {
    showLoading('monitoring');
    
    try {
        const metrics = await apiCall('/monitoring/metrics');
        updateMetrics(metrics);
        
        const health = await apiCall('/health');
        updateHealthStatus(health);
        
        showNotification('Metrics refreshed', 'success');
    } catch (error) {
        console.error('Error refreshing metrics:', error);
        showNotification('Error refreshing metrics', 'error');
    } finally {
        hideLoading('monitoring');
    }
}

// Charts
function initializeCharts() {
    // Job Activity Chart
    const jobActivityCtx = document.getElementById('jobActivityChart').getContext('2d');
    charts.jobActivity = new Chart(jobActivityCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Jobs Created',
                data: [],
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // Success Rate Chart
    const successRateCtx = document.getElementById('successRateChart').getContext('2d');
    charts.successRate = new Chart(successRateCtx, {
        type: 'doughnut',
        data: {
            labels: ['Success', 'Failed'],
            datasets: [{
                data: [75, 25],
                backgroundColor: [
                    '#28a745',
                    '#dc3545'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        });
}

function updateCharts(stats) {
    // Update job activity chart
    if (charts.jobActivity && stats.job_activity) {
        charts.jobActivity.data.labels = stats.job_activity.labels;
        charts.jobActivity.data.datasets[0].data = stats.job_activity.data;
        charts.jobActivity.update();
    }
    
    // Update success rate chart
    if (charts.successRate) {
        const successRate = stats.success_rate || 0;
        charts.successRate.data.datasets[0].data = [successRate, 100 - successRate];
        charts.successRate.update();
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('loading');
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('loading');
    }
}

function refreshDashboard() {
    loadDashboardData();
    showNotification('Dashboard refreshed', 'success');
}

// Form Listeners
function setupFormListeners() {
    // Quick scrape form
    const quickScrapeForm = document.getElementById('quick-scrape-form');
    if (quickScrapeForm) {
        quickScrapeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            quickScrape();
        });
    }
}

function setupModalListeners() {
    // Create job modal
    const createJobModal = document.getElementById('createJobModal');
    if (createJobModal) {
        createJobModal.addEventListener('show.bs.modal', function() {
            // Load jobs for dropdown
            loadJobsData();
        });
    }
    
    // Export modal
    const exportModal = document.getElementById('exportModal');
    if (exportModal) {
        exportModal.addEventListener('show.bs.modal', function() {
            // Load exports for dropdown
            loadExportsData();
        });
    }
}

// Helper function to show job details
function showJobDetails(job) {
    // This would open a modal with detailed job information
    console.log('Job details:', job);
    showNotification(`Job details for ${job.name}`, 'info');
}

// Auto-refresh
setInterval(() => {
    if (currentSection === 'dashboard') {
        loadDashboardData();
    } else if (currentSection === 'monitoring') {
        refreshMetrics();
    }
}, 30000); // Refresh every 30 seconds

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e);
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Initialize popovers
document.addEventListener('DOMContentLoaded', function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});
