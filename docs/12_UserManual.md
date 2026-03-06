# User Manual

## 1. Getting Started

### 1.1 Welcome to Web Scraper AI
Web Scraper AI is a powerful, user-friendly platform for extracting structured data from websites. Whether you're a data scientist, business analyst, or researcher, our system makes web data collection simple, reliable, and efficient.

### 1.2 What You Can Do With Web Scraper AI
- **Extract Product Information**: Monitor e-commerce sites for pricing and availability
- **Collect Market Data**: Gather competitive intelligence and market trends
- **Aggregate Content**: Build datasets for research and analysis
- **Monitor Websites**: Track changes and updates automatically
- **Export Data**: Download clean datasets in multiple formats

### 1.3 System Requirements
- **Web Browser**: Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+
- **Internet Connection**: Stable connection for web scraping
- **Account**: Free or paid subscription (see pricing plans)

### 1.4 Quick Start Guide
1. **Sign Up**: Create your account at https://app.webscraper.ai
2. **Create Your First Job**: Use our simple wizard to configure scraping
3. **Run the Scraper**: Start extracting data with one click
4. **Download Results**: Export data in CSV, JSON, or other formats

## 2. Account Management

### 2.1 Creating an Account

#### Sign Up Process
1. Visit https://app.webscraper.ai/signup
2. Fill in your information:
   - **Email Address**: Valid email for account verification
   - **Username**: Unique identifier for your account
   - **Password**: Minimum 8 characters with letters and numbers
   - **First Name**: Your first name
   - **Last Name**: Your last name
3. Click "Create Account"
4. Check your email for verification link
5. Click the verification link to activate your account

#### Account Types
- **Free Plan**: 100 requests/month, basic features
- **Pro Plan**: 10,000 requests/month, advanced features
- **Enterprise Plan**: Unlimited requests, custom features

### 2.2 Logging In

#### Standard Login
1. Go to https://app.webscraper.ai/login
2. Enter your email and password
3. Click "Sign In"
4. You'll be redirected to your dashboard

#### Two-Factor Authentication (Optional)
If enabled, after entering your password:
1. Enter the 6-digit code from your authenticator app
2. Click "Verify"

### 2.3 Managing Your Profile

#### Updating Personal Information
1. Click your profile picture in the top-right corner
2. Select "Profile Settings"
3. Update your information:
   - Name
   - Email
   - Timezone
   - Language preferences
4. Click "Save Changes"

#### Changing Password
1. Go to Profile Settings
2. Click "Change Password"
3. Enter your current password
4. Enter your new password (minimum 8 characters)
5. Confirm your new password
6. Click "Update Password"

#### API Key Management
1. Go to Profile Settings → API Keys
2. Click "Generate New API Key"
3. Give your key a descriptive name
4. Set permissions (read, write, delete)
5. Set rate limits if needed
6. Copy the key (shown only once)
7. Click "Create API Key"

## 3. Creating Scraping Jobs

### 3.1 Job Creation Wizard

#### Step 1: Basic Information
1. Click "New Job" on your dashboard
2. Fill in basic information:
   - **Job Name**: Descriptive name for your reference
   - **Description**: Optional details about the job
   - **Target URL**: Website URL you want to scrape
   - **Job Type**: One-time or recurring

**Example:**
```
Job Name: Amazon Laptop Prices
Description: Track laptop prices on Amazon
Target URL: https://www.amazon.com/s?k=laptops
Job Type: Recurring (weekly)
```

#### Step 2: Data Field Selection
1. **URL Preview**: The target website loads in a preview pane
2. **Field Selection**: Click on elements to extract:
   - Product names
   - Prices
   - Ratings
   - Descriptions
   - Images
3. **CSS Selectors**: Automatically generated selectors appear
4. **Manual Configuration**: Enter custom CSS selectors if needed

**Field Selection Tips:**
- Hover over elements to highlight them
- Click to select elements for extraction
- Use "Inspect Element" in your browser for complex selectors
- Test selectors with the "Validate" button

#### Step 3: Processing Rules
1. **Data Cleaning**: Enable automatic HTML removal and text normalization
2. **Validation Rules**: Set required fields and data types
3. **Transformations**: Convert text to numbers, format dates, etc.

**Common Processing Rules:**
- Remove HTML tags
- Normalize whitespace
- Validate email formats
- Convert prices to numbers
- Format dates consistently

#### Step 4: Export Configuration
1. **Format Selection**: Choose export format (CSV, JSON, Excel)
2. **File Settings**: Set delimiter, encoding, and naming
3. **Delivery Options**: Download, email, or cloud storage

### 3.2 Advanced Configuration

#### Custom CSS Selectors
For complex websites, you can use advanced CSS selectors:

**Basic Selectors:**
```css
/* Element by tag */
h1

/* Element by class */
.product-title

/* Element by ID */
#main-content

/* Attribute selector */
a[href="/products"]
```

**Advanced Selectors:**
```css
/* Nested elements */
.product-card .price .amount

/* Multiple selectors */
.title, .name, .product-name

/* Attribute contains */
div[class*="price"]

/* nth-child */
.product-item:nth-child(odd)
```

#### JavaScript Handling
For dynamic websites:
1. Enable "JavaScript Rendering" in job settings
2. Set wait time for content to load
3. Configure scroll behavior for infinite pages
4. Set up click actions for tabbed content

#### Rate Limiting
Be respectful to websites:
1. **Request Delay**: Time between requests (1-10 seconds)
2. **Concurrent Requests**: Number of simultaneous requests
3. **Respect robots.txt**: Automatically follows website rules
4. **User Agent**: Identify your scraper appropriately

## 4. Managing Jobs

### 4.1 Job Dashboard

#### Viewing All Jobs
1. Click "Jobs" in the navigation menu
2. See all your scraping jobs with:
   - Status indicators (pending, running, completed, failed)
   - Last run time
   - Number of records extracted
   - Progress bars for active jobs

#### Job Status Indicators
- **🟡 Pending**: Job is queued and waiting to start
- **🔵 Running**: Job is currently scraping data
- **🟢 Completed**: Job finished successfully
- **🔴 Failed**: Job encountered an error
- **⚪ Cancelled**: Job was stopped by user

#### Filtering and Sorting
- **Filter by Status**: Show only jobs with specific status
- **Filter by Date**: View jobs from specific time periods
- **Search**: Find jobs by name or description
- **Sort**: Order by creation date, last run, or name

### 4.2 Job Actions

#### Starting a Job
1. Find the job in your dashboard
2. Click the "Start" button
3. Monitor progress in real-time
4. Receive notification when complete

#### Pausing a Job
1. Click the "Pause" button on a running job
2. Job stops at current position
3. Click "Resume" to continue from where it stopped

#### Stopping a Job
1. Click "Stop" to immediately terminate a job
2. Partial results are saved
3. You can restart the job later

#### Editing a Job
1. Click the "Edit" button
2. Modify configuration as needed
3. Save changes
4. Changes apply to future runs

#### Deleting a Job
1. Click the "Delete" button
2. Confirm deletion
3. All job data and results are permanently removed

### 4.3 Scheduling Jobs

#### Setting Up Recurring Jobs
1. Create or edit a job
2. Select "Recurring" as job type
3. Choose schedule frequency:
   - **Hourly**: Every hour
   - **Daily**: Once per day
   - **Weekly**: Once per week
   - **Monthly**: Once per month
   - **Custom**: Cron expression for advanced users

#### Cron Expressions
For custom scheduling:
```
# Every day at 9 AM
0 9 * * *

# Every Monday at 9 AM
0 9 * * 1

# Every weekday at 9 AM
0 9 * * 1-5

# Every 2 hours
0 */2 * * *
```

#### Managing Schedules
- **View Schedule**: See upcoming run times
- **Pause Schedule**: Temporarily stop recurring runs
- **Edit Schedule**: Change frequency or timing
- **Delete Schedule**: Remove recurring behavior

## 5. Working with Results

### 5.1 Viewing Results

#### Results Preview
1. Click on a completed job
2. See preview of extracted data
3. Navigate through pages of results
4. Use search and filter functions

#### Data Quality Indicators
- **✅ Valid**: Data passed all validation rules
- **⚠️ Warnings**: Data has minor issues
- **❌ Invalid**: Data failed validation

#### Result Statistics
- **Total Records**: Number of items extracted
- **Valid Records**: Records that passed validation
- **Success Rate**: Percentage of successful extractions
- **Processing Time**: Time taken to complete job

### 5.2 Data Validation

#### Validation Rules
Your data is automatically checked for:
- **Required Fields**: Ensures essential data is present
- **Data Types**: Verifies numbers, dates, emails, etc.
- **Format Compliance**: Checks standard formats
- **Uniqueness**: Identifies duplicate records

#### Handling Validation Issues
1. **Review Invalid Records**: See specific validation errors
2. **Adjust Rules**: Modify validation criteria if too strict
3. **Manual Correction**: Edit individual records if needed
4. **Re-process**: Run validation again with new rules

### 5.3 Exporting Data

#### Export Formats

**CSV (Comma-Separated Values)**
- Best for spreadsheet applications
- Compatible with Excel, Google Sheets
- Small file size
- Easy to process programmatically

**JSON (JavaScript Object Notation)**
- Best for web applications
- Preserves data structure
- Supports nested data
- API-friendly format

**Excel (.xlsx)**
- Rich formatting options
- Built-in analysis tools
- Multiple worksheets
- Chart and graph support

**Google Sheets**
- Cloud-based collaboration
- Real-time sharing
- Automatic backups
- Integration with Google Workspace

#### Export Options
1. **Select Format**: Choose your preferred format
2. **Configure Settings**:
   - File name
   - Delimiter (for CSV)
   - Encoding
   - Include headers
3. **Filter Data**: Export specific records or time ranges
4. **Download**: Get your file immediately

#### Automated Exports
Set up automatic exports:
1. Go to job settings
2. Enable "Auto Export"
3. Choose format and destination
4. Set schedule (same as job schedule)
5. Configure email notifications

## 6. Advanced Features

### 6.1 Templates and Configurations

#### Saving Templates
1. Create a job with your desired settings
2. Click "Save as Template"
3. Give your template a name
4. Add description for future reference
5. Templates are available for new jobs

#### Using Templates
1. Click "New Job"
2. Choose "Use Template"
3. Select your saved template
4. Modify URL or settings as needed
5. Save and run your job

#### Sharing Templates
- **Public Templates**: Share with other users
- **Team Templates**: Share within your organization
- **Private Templates**: Keep for your use only

### 6.2 API Access

#### Getting Started with API
1. Generate API key in profile settings
2. Read API documentation
3. Use SDKs for Python, JavaScript, or other languages
4. Test with API explorer

#### Common API Tasks

**Create a Job**
```bash
curl -X POST "https://api.webscraper.ai/v1/jobs" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test Job",
    "url": "https://example.com",
    "selectors": {"title": "h1"}
  }'
```

**Check Job Status**
```bash
curl -X GET "https://api.webscraper.ai/v1/jobs/123/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Download Results**
```bash
curl -X GET "https://api.webscraper.ai/v1/jobs/123/results" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o results.csv
```

### 6.3 Webhooks and Notifications

#### Setting Up Webhooks
1. Go to job settings
2. Enable "Webhook Notifications"
3. Enter webhook URL
4. Choose events to notify:
   - Job started
   - Job completed
   - Job failed
   - Results ready

#### Webhook Payload
```json
{
  "event": "job.completed",
  "job_id": 123,
  "job_name": "Amazon Scraper",
  "status": "completed",
  "records": 1250,
  "timestamp": "2024-01-15T10:30:00Z",
  "download_url": "https://api.webscraper.ai/jobs/123/download"
}
```

#### Email Notifications
Configure email alerts for:
- Job completion
- Job failures
- Daily summary reports
- Storage limits

### 6.4 Data Processing

#### Custom Transformations
Apply custom data transformations:
- **Text Processing**: Clean, trim, normalize
- **Number Formatting**: Currency, percentages, units
- **Date Processing**: Multiple format support
- **URL Processing**: Extract domains, validate links

#### Data Enrichment
Enhance extracted data:
- **Geocoding**: Convert addresses to coordinates
- **Currency Conversion**: Convert prices to base currency
- **Language Detection**: Identify text language
- **Sentiment Analysis**: Analyze product reviews

## 7. Troubleshooting

### 7.1 Common Issues

#### Job Won't Start
**Symptoms:** Job stays in "Pending" status
**Solutions:**
1. Check your plan limits (free plans have concurrent job limits)
2. Verify target URL is accessible
3. Check for system maintenance notifications
4. Try stopping and restarting the job

#### Slow Performance
**Symptoms:** Job taking longer than expected
**Solutions:**
1. Increase delay between requests
2. Reduce concurrent requests
3. Check website response time
4. Consider using a different time of day

#### No Data Extracted
**Symptoms:** Job completes but returns no data
**Solutions:**
1. Verify CSS selectors are correct
2. Check if website uses JavaScript
3. Test selectors in browser console
4. Use preview mode to debug

#### Website Blocking
**Symptoms:** Job fails with access denied errors
**Solutions:**
1. Respect robots.txt rules
2. Increase delay between requests
3. Use different user agent
4. Consider proxy rotation

#### Data Quality Issues
**Symptoms:** Extracted data is incomplete or incorrect
**Solutions:**
1. Review validation rules
2. Check for website structure changes
3. Update CSS selectors
4. Enable data cleaning options

### 7.2 Getting Help

#### Self-Service Resources
- **Knowledge Base**: Detailed articles and tutorials
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Common questions and answers
- **Community Forum**: Get help from other users

#### Contact Support
1. **Email Support**: support@webscraper.ai
2. **Live Chat**: Available on website during business hours
3. **Support Ticket**: Submit detailed issue report
4. **Priority Support**: Available for Pro and Enterprise plans

#### When Contacting Support
Include the following information:
- Job ID and name
- Description of the issue
- Steps to reproduce
- Screenshots if applicable
- Browser and operating system

### 7.3 Best Practices

#### Efficient Scraping
1. **Plan Your Strategy**: Know what data you need before starting
2. **Test Selectors**: Validate CSS selectors before running full jobs
3. **Start Small**: Test with small datasets first
4. **Monitor Performance**: Keep an eye on job progress and errors
5. **Respect Websites**: Follow robots.txt and use reasonable delays

#### Data Quality
1. **Validate Input**: Ensure target URLs are correct
2. **Set Appropriate Rules**: Don't over-validate or under-validate
3. **Review Results**: Check sample data before full extraction
4. **Clean Data**: Use built-in cleaning features
5. **Document Everything**: Keep notes on job configurations

#### Security and Privacy
1. **Secure Your Account**: Use strong passwords and 2FA
2. **Protect API Keys**: Don't share or commit to repositories
3. **Respect Privacy**: Don't scrape personal data without permission
4. **Comply with Laws**: Follow data protection regulations
5. **Use HTTPS**: Ensure secure connections

## 8. Pricing and Plans

### 8.1 Plan Comparison

#### Free Plan
- **Requests**: 100 per month
- **Concurrent Jobs**: 1
- **Storage**: 100 MB
- **Support**: Community forum
- **Features**: Basic scraping, CSV export

#### Pro Plan ($49/month)
- **Requests**: 10,000 per month
- **Concurrent Jobs**: 5
- **Storage**: 10 GB
- **Support**: Email support
- **Features**: Advanced scraping, all formats, API access

#### Enterprise Plan (Custom)
- **Requests**: Unlimited
- **Concurrent Jobs**: Unlimited
- **Storage**: Custom
- **Support**: Priority support, dedicated account manager
- **Features**: Custom features, SLA, on-premise deployment

### 8.2 Usage Tracking

#### Monitoring Your Usage
1. Go to Account Settings → Usage
2. View current month's usage
3. See historical usage trends
4. Get notifications when approaching limits

#### Managing Limits
- **Upgrade Plan**: Increase limits anytime
- **Purchase Credits**: One-time credit purchases
- **Optimize Jobs**: Reduce unnecessary requests
- **Clean Storage**: Delete old jobs and results

## 9. Integration Guide

### 9.1 Popular Integrations

#### Google Sheets
1. Install Google Sheets add-on
2. Connect your Web Scraper account
3. Import data directly to spreadsheets
4. Set up automatic updates

#### Zapier
1. Connect Web Scraper to Zapier
2. Create automated workflows
3. Trigger actions based on job completion
4. Connect to 3000+ apps

#### Microsoft Excel
1. Use Power Query to connect
2. Import data directly into Excel
3. Refresh data automatically
4. Create reports and dashboards

#### Python/R
1. Use official SDKs
2. Integrate into data science workflows
3. Automate with scripts
4. Process data with pandas/R

### 9.2 Custom Integrations

#### Webhooks
Set up webhooks to:
- Trigger other systems when jobs complete
- Send data to external databases
- Create custom notifications
- Integrate with existing workflows

#### API Integration
Build custom applications:
- Mobile apps
- Internal dashboards
- Third-party tools
- Automated reporting systems

## 10. Frequently Asked Questions

### General Questions
**Q: Is web scraping legal?**
A: Web scraping is generally legal when done responsibly. We recommend following robots.txt, respecting terms of service, and not overwhelming websites with requests.

**Q: Can you scrape any website?**
A: Most websites can be scraped, but some have protections or prohibit scraping. Always check the website's terms of service.

**Q: What happens if a website blocks me?**
A: The system will detect blocks and retry with different strategies. You can also adjust settings like delays and user agents.

### Technical Questions
**Q: How do I handle JavaScript content?**
A: Enable "JavaScript Rendering" in job settings. This uses a real browser to render the page before extraction.

**Q: Can I scrape behind a login?**
A: Yes, you can configure login credentials in advanced settings. The system will handle authentication automatically.

**Q: What's the difference between CSS and XPath selectors?**
A: CSS selectors are simpler and more commonly used. XPath is more powerful for complex document structures. We support both.

### Billing Questions
**Q: How are requests counted?**
A: Each page scraped counts as one request. API calls and result downloads don't count toward your limit.

**Q: Can I roll over unused requests?**
A: Free plan requests don't roll over. Pro and Enterprise plans include rollover options.

**Q: What happens if I exceed my limit?**
A: Jobs will pause until the next billing cycle or you upgrade your plan.

### Support Questions
**Q: How quickly do you respond to support requests?**
A: Free users: community forum. Pro users: within 24 hours. Enterprise users: within 4 hours.

**Q: Do you offer training?**
A: Yes, Enterprise plans include personalized training and onboarding.

**Q: Can I get a refund?**
A: We offer a 30-day money-back guarantee for new Pro plan subscriptions.

---

## Need More Help?

- **Documentation**: https://docs.webscraper.ai
- **Community**: https://community.webscraper.ai
- **Support**: support@webscraper.ai
- **Status**: https://status.webscraper.ai

Thank you for choosing Web Scraper AI! Happy scraping!
