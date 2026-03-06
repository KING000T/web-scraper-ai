# UI/UX Design Document

## 1. Design Overview

### 1.1 Design Philosophy
The Web Scraping System UI follows a clean, intuitive, and professional design philosophy focused on usability and efficiency. The interface is designed to be accessible to both technical and non-technical users while providing advanced features for power users.

### 1.2 Design Principles
- **Simplicity**: Clean, uncluttered interface with minimal cognitive load
- **Consistency**: Uniform design patterns and interactions
- **Efficiency**: Quick access to common actions and workflows
- **Feedback**: Clear visual feedback for all user actions
- **Accessibility**: WCAG 2.1 AA compliance for inclusive design

### 1.3 Target User Experience
- **Beginner Users**: Guided setup with wizards and tooltips
- **Intermediate Users**: Efficient workflows with keyboard shortcuts
- **Advanced Users**: Power features and customization options

## 2. Visual Design System

### 2.1 Color Palette
```css
/* Primary Colors */
--primary-blue: #2563eb;      /* Main action buttons, links */
--primary-dark: #1e40af;     /* Hover states, active elements */
--primary-light: #dbeafe;    /* Backgrounds, highlights */

/* Secondary Colors */
--secondary-green: #16a34a;  /* Success states, completed jobs */
--secondary-orange: #ea580c;  /* Warning states, processing */
--secondary-red: #dc2626;    /* Error states, failed jobs */

/* Neutral Colors */
--gray-50: #f9fafb;          /* Page background */
--gray-100: #f3f4f6;         /* Card backgrounds */
--gray-200: #e5e7eb;         /* Borders, dividers */
--gray-300: #d1d5db;         /* Disabled elements */
--gray-400: #9ca3af;         /* Placeholders */
--gray-500: #6b7280;         /* Secondary text */
--gray-600: #4b5563;         /* Primary text */
--gray-700: #374151;         /* Headings */
--gray-800: #1f2937;         /* Dark mode text */
--gray-900: #111827;         /* Dark mode backgrounds */

/* Semantic Colors */
--success: #16a34a;
--warning: #ea580c;
--error: #dc2626;
--info: #2563eb;
```

### 2.2 Typography
```css
/* Font Family */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;

/* Font Sizes */
--text-xs: 0.75rem;     /* 12px - Labels, captions */
--text-sm: 0.875rem;    /* 14px - Small text */
--text-base: 1rem;     /* 16px - Body text */
--text-lg: 1.125rem;   /* 18px - Large body */
--text-xl: 1.25rem;     /* 20px - Small headings */
--text-2xl: 1.5rem;    /* 24px - Section headings */
--text-3xl: 1.875rem;  /* 30px - Page headings */
--text-4xl: 2.25rem;   /* 36px - Hero headings */

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### 2.3 Spacing System
```css
/* Spacing Scale (8px base unit) */
--space-1: 0.25rem;    /* 4px */
--space-2: 0.5rem;     /* 8px */
--space-3: 0.75rem;    /* 12px */
--space-4: 1rem;       /* 16px */
--space-5: 1.25rem;    /* 20px */
--space-6: 1.5rem;     /* 24px */
--space-8: 2rem;       /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
--space-20: 5rem;      /* 80px */
```

### 2.4 Component Design

#### Buttons
```css
/* Primary Button */
.btn-primary {
  background-color: var(--primary-blue);
  color: white;
  padding: var(--space-2) var(--space-4);
  border-radius: 0.375rem;
  font-weight: var(--font-medium);
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* Secondary Button */
.btn-secondary {
  background-color: transparent;
  color: var(--primary-blue);
  border: 1px solid var(--primary-blue);
  padding: var(--space-2) var(--space-4);
  border-radius: 0.375rem;
  font-weight: var(--font-medium);
}

.btn-secondary:hover {
  background-color: var(--primary-light);
}

/* Status Buttons */
.btn-success { background-color: var(--success); color: white; }
.btn-warning { background-color: var(--warning); color: white; }
.btn-error { background-color: var(--error); color: white; }
```

#### Cards
```css
.card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: var(--space-6);
  border: 1px solid var(--gray-200);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  border-bottom: 1px solid var(--gray-200);
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-4);
}
```

## 3. Layout Architecture

### 3.1 Application Layout
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Navigation Header                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────────────┐ │
│  │             │    │                  Main Content                         │ │
│  │   Sidebar   │    │                                                     │ │
│  │             │    │  ┌─────────────────────────────────────────────┐   │ │
│  │ - Dashboard │    │  │            Page Header                      │   │ │
│  │ - Jobs      │    │  └─────────────────────────────────────────────┘   │ │
│  │ - Results   │    │                                                     │ │
│  │ - Settings  │    │  ┌─────────────────────────────────────────────┐   │ │
│  │ - Help      │    │  │            Content Area                      │   │ │
│  │             │    │  │                                             │   │ │
│  │             │    │  │                                             │   │ │
│  │             │    │  │                                             │   │ │
│  │             │    │  │                                             │   │ │
│  └─────────────┘    │  └─────────────────────────────────────────────┘   │ │
│                     │                                                     │ │
│                     └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Responsive Breakpoints
```css
/* Breakpoint System */
--breakpoint-sm: 640px;   /* Mobile landscape */
--breakpoint-md: 768px;   /* Tablet */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large desktop */
--breakpoint-2xl: 1536px; /* Extra large desktop */

/* Responsive Layout */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -100%;
    transition: left 0.3s ease;
    z-index: 50;
  }
  
  .sidebar.open {
    left: 0;
  }
  
  .main-content {
    margin-left: 0;
  }
}

@media (min-width: 769px) {
  .sidebar {
    position: static;
    width: 256px;
  }
  
  .main-content {
    margin-left: 256px;
  }
}
```

## 4. Page Designs

### 4.1 Dashboard Page

#### 4.1.1 Layout Structure
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Dashboard Header                                  │
│  Welcome back, User! | Last login: 2 hours ago | System Status: ● Online     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Active Jobs   │  │  Completed Jobs │  │   Failed Jobs   │  │  Total Data │ │
│  │                 │  │                 │  │                 │  │  Extracted  │ │
│  │       12        │  │       156       │  │        3        │  │   1.2M      │ │
│  │   ▲ 2 from yesterday│  │   ▲ 15 today   │  │   ▼ 1 from yesterday│  │   ▲ 50K     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Recent Activity                                   │ │
│  │                                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│  │  │ Job: "Amazon Products" - Status: Running - Progress: 45% - ETA: 5m │   │ │
│  │  │ Job: "News Articles" - Status: Completed - Records: 2,345 - Time: 12m│   │ │
│  │  │ Job: "Social Media" - Status: Failed - Error: Rate limit exceeded   │   │ │
│  │  └─────────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Quick Actions                                     │ │
│  │                                                                             │ │ │
│  │  [+] New Scraping Job    [📊] View Reports    [⚙️] Settings    [❓] Help   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 4.1.2 Component Specifications
```html
<!-- Stats Cards -->
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-icon active-jobs">🔄</div>
    <div class="stat-content">
      <h3 class="stat-number">12</h3>
      <p class="stat-label">Active Jobs</p>
      <span class="stat-change positive">▲ 2 from yesterday</span>
    </div>
  </div>
  
  <div class="stat-card">
    <div class="stat-icon completed-jobs">✅</div>
    <div class="stat-content">
      <h3 class="stat-number">156</h3>
      <p class="stat-label">Completed Jobs</p>
      <span class="stat-change positive">▲ 15 today</span>
    </div>
  </div>
  
  <div class="stat-card">
    <div class="stat-icon failed-jobs">❌</div>
    <div class="stat-content">
      <h3 class="stat-number">3</h3>
      <p class="stat-label">Failed Jobs</p>
      <span class="stat-change negative">▼ 1 from yesterday</span>
    </div>
  </div>
  
  <div class="stat-card">
    <div class="stat-icon total-data">📊</div>
    <div class="stat-content">
      <h3 class="stat-number">1.2M</h3>
      <p class="stat-label">Total Data Extracted</p>
      <span class="stat-change positive">▲ 50K</span>
    </div>
  </div>
</div>

<!-- Recent Activity Feed -->
<div class="activity-feed">
  <h3>Recent Activity</h3>
  <div class="activity-items">
    <div class="activity-item running">
      <div class="activity-icon">🔄</div>
      <div class="activity-content">
        <h4>Amazon Products</h4>
        <p>Status: Running | Progress: 45% | ETA: 5m</p>
        <div class="progress-bar">
          <div class="progress-fill" style="width: 45%"></div>
        </div>
      </div>
      <div class="activity-actions">
        <button class="btn-sm btn-secondary">Pause</button>
        <button class="btn-sm btn-error">Cancel</button>
      </div>
    </div>
    
    <div class="activity-item completed">
      <div class="activity-icon">✅</div>
      <div class="activity-content">
        <h4>News Articles</h4>
        <p>Status: Completed | Records: 2,345 | Time: 12m</p>
      </div>
      <div class="activity-actions">
        <button class="btn-sm btn-primary">View Results</button>
        <button class="btn-sm btn-secondary">Download</button>
      </div>
    </div>
  </div>
</div>
```

### 4.2 Job Configuration Page

#### 4.2.1 Multi-Step Wizard
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Job Configuration Wizard                           │
│                                                                                 │
│  Step 1: Basic Info ●───● Step 2: Scraping ○───○ Step 3: Processing ○───○     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Step 1: Basic Information                         │ │
│  │                                                                             │ │
│  │  Job Name: [Amazon Product Scraper                               ]         │ │
│  │  Description: [Extract product information from Amazon search results]        │ │
│  │                                                                             │ │
│  │  Target URL: [https://www.amazon.com/s?k=laptops                   ]       │ │
│  │              [🔍 Test URL] [✓ Valid]                                    │ │
│  │                                                                             │ │
│  │  Job Type: ◉ One-time scraping ○ Recurring schedule                        │ │
│  │                                                                             │ │
│  │  Priority:  High ○ Medium ◉ Low                                           │ │
│  │                                                                             │ │
│  │                              [Previous] [Next →]                           │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 Field Selection Interface
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Step 2: Data Extraction                           │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────────┐ │
│  │   Page Preview  │    │                  Field Selection                    │ │
│  │                 │    │                                                     │ │
│  │  [Browser View] │    │  ┌─────────────────────────────────────────────┐   │ │
│  │                 │    │  │ Selected Fields                              │   │ │
│  │  🖱️ Click on    │    │  │                                             │ │ │
│  │     elements    │    │  │  📝 Product Name: .s-result-item .s-link     │   │ │
│  │     to select   │    │  │  💰 Price: .a-price-whole                    │   │ │
│  │                 │    │  │  ⭐ Rating: .a-icon-alt .a-icon-alt-text      │   │ │
│  │                 │    │  │  📦 Availability: .a-color-success           │   │ │
│  │                 │    │  │                                             │ │ │
│  │                 │    │  │  [+] Add Field                               │   │ │
│  │                 │    │  └─────────────────────────────────────────────┘   │ │
│  │                 │    │                                                     │ │
│  │                 │    │  ┌─────────────────────────────────────────────┐   │ │
│  │                 │    │  │ CSS Selector                               │   │ │
│  │                 │    │  │ [                                           │   │ │
│  │                 │    │  │  .product-title                            │   │ │
│  │                 │    │  │ ]                                           │   │ │
│  │                 │    │  │                                             │ │ │
│  │                 │    │  │  [🔍 Test Selector] [✓ 5 elements found]   │   │ │
│  │                 │    │  └─────────────────────────────────────────────┘   │ │
│  └─────────────────┘    └─────────────────────────────────────────────────────┘ │
│                                                                                 │
│                              [← Previous] [Next →]                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Job Monitoring Page

#### 4.3.1 Real-time Monitoring Dashboard
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Job Monitoring                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  Job: Amazon Product Scraper | Status: 🔄 Running | Started: 10:23 AM     │ │
│  │                                                                             │ │
│  │  Progress: ████████████████████████████████████░░░░ 85% (4,250/5,000)     │ │
│  │  Speed: 45 pages/min | ETA: 2m 15s | Errors: 0                              │ │
│  │                                                                             │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │ │
│  │  │   Statistics    │  │   Live Log      │  │   Actions       │             │ │
│  │  │                 │  │                 │  │                 │             │ │
│  │  │ Pages: 4,250   │  │ [10:45:23] Scraping page... │  │ [⏸️] Pause     │ │ │
│  │  │ Success: 4,250 │  │ [10:45:22] Extracted data... │  │ [⏹️] Stop      │ │ │
│  │  │ Errors: 0      │  │ [10:45:21] Processing page... │  │ [📥] Download  │ │ │
│  │  │ Rate: 45/min   │  │ [10:45:20] Loading page...     │  │ [🔄] Restart   │ │ │
│  │  │ Memory: 245MB  │  │ [10:45:19] Navigating to...   │  │ [📊] View Data │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Results Viewer Page

#### 4.4.1 Data Table with Export Options
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Results Viewer                                    │
│                                                                                 │
│  Job: Amazon Products | Records: 2,345 | Exported: 2,345 | Last Updated: Now   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  🔍 Search: [laptop...]  📊 Filter: [All ▼]  📅 Date: [Today ▼]          │ │
│  │                                                                             │ │
│  │  [📥 CSV] [📄 JSON] [📊 Google Sheets] [🗃️ Database] [📧 Email]          │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  ☑️  Product Name       │  💰 Price    │  ⭐ Rating │  📦 Availability    │ │
│  │  ☑️  Dell XPS 13         │  $899.99    │  4.5/5    │  In Stock          │ │
│  │  ☑️  MacBook Pro M2      │  $1,299.00  │  4.8/5    │  In Stock          │ │
│  │  ☑️  HP Spectre x360     │  $1,149.99  │  4.3/5    │  2-3 days          │ │
│  │  ☑️  Lenovo ThinkPad     │  $1,059.00  │  4.6/5    │  In Stock          │ │
│  │  ☑️  ASUS ZenBook        │  $799.99    │  4.4/5    │  Limited Stock     │ │
│  │  ...                    │  ...        │  ...      │  ...               │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  Showing 1-10 of 2,345 records  ◀ 1 2 3 4 5 ... 235 ▶                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 5. Interactive Elements

### 5.1 Micro-interactions

#### Button States
```css
.btn {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
```

#### Loading States
```css
.loading {
  position: relative;
  pointer-events: none;
}

.loading::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  margin: -10px 0 0 -10px;
  border: 2px solid var(--primary-blue);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

#### Progress Indicators
```css
.progress-bar {
  width: 100%;
  height: 8px;
  background-color: var(--gray-200);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-blue);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

### 5.2 Form Interactions

#### Input Validation
```css
.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  display: block;
  font-weight: var(--font-medium);
  margin-bottom: var(--space-2);
  color: var(--gray-700);
}

.form-input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--gray-300);
  border-radius: 0.375rem;
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-input.error {
  border-color: var(--error);
}

.form-input.success {
  border-color: var(--success);
}

.error-message {
  color: var(--error);
  font-size: var(--text-sm);
  margin-top: var(--space-1);
}

.success-message {
  color: var(--success);
  font-size: var(--text-sm);
  margin-top: var(--space-1);
}
```

#### Tooltips
```css
.tooltip {
  position: relative;
  display: inline-block;
}

.tooltip::before {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--gray-800);
  color: white;
  padding: var(--space-1) var(--space-2);
  border-radius: 0.25rem;
  font-size: var(--text-sm);
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 1000;
}

.tooltip:hover::before {
  opacity: 1;
}
```

## 6. Responsive Design

### 6.1 Mobile Layout
```
┌─────────────────────────────────────────┐
│              ☰ Web Scraper              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │           Dashboard                 │ │
│  │                                     │ │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │ │
│  │  │ 12  │ │ 156 │ │  3  │ │1.2M │  │ │
│  │  │Jobs │ │Done │ │Fail │ │Data │  │ │
│  │  └─────┘ └─────┘ └─────┘ └─────┘  │ │
│  │                                     │ │
│  │  Recent Activity                   │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │ 🔄 Amazon Products - 45%        │ │ │
│  │  │ ✅ News Articles - 2,345 rec   │ │ │
│  │  │ ❌ Social Media - Failed        │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │           Quick Actions             │ │
│  │                                     │ │
│  │  [+] New Job  [📊] Reports  [⚙️]    │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 6.2 Tablet Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Web Scraper Dashboard                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────────────────────────────────────────────┐ │
│  │   Sidebar   │  │                  Main Content                         │ │
│  │             │  │                                                     │ │
│  │ - Dashboard │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  ┌─────────────┐   │ │
│  │ - Jobs      │  │  │ 12  │ │ 156 │ │  3  │ │1.2M │  │ Recent Act  │   │ │
│  │ - Results   │  │  │Jobs │ │Done │ │Fail │ │Data │  │             │   │ │
│  │ - Settings  │  │  └─────┘ └─────┘ └─────┘ └─────┘  └─────────────┘   │ │
│  │ - Help      │  │                                                     │ │
│  │             │  │  ┌─────────────────────────────────────────────┐   │ │
│  │             │  │  │           Quick Actions                       │   │ │
│  │             │  │  │                                             │   │ │
│  │             │  │  │  [+] New Job  [📊] Reports  [⚙️] Settings   │   │ │
│  │             │  │  └─────────────────────────────────────────────┘   │ │
│  └─────────────┘  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 7. Accessibility Features

### 7.1 Keyboard Navigation
```css
/* Focus Styles */
.focusable:focus {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
}

/* Skip Links */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--primary-blue);
  color: white;
  padding: 8px;
  text-decoration: none;
  border-radius: 4px;
  z-index: 1000;
}

.skip-link:focus {
  top: 6px;
}
```

### 7.2 Screen Reader Support
```html
<!-- Semantic HTML -->
<main role="main" aria-label="Main content">
  <section aria-labelledby="dashboard-heading">
    <h2 id="dashboard-heading">Dashboard</h2>
    <!-- Content -->
  </section>
</main>

<!-- ARIA Labels -->
<button aria-label="Start new scraping job" aria-describedby="new-job-help">
  + New Job
</button>
<div id="new-job-help" class="sr-only">
  Create a new web scraping job configuration
</div>

<!-- Live Regions -->
<div aria-live="polite" aria-atomic="true" id="status-updates">
  Job status updates will be announced here
</div>
```

## 8. Dark Mode Support

### 8.1 Dark Mode Color Palette
```css
/* Dark Mode Variables */
[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --border-color: #334155;
  --shadow-color: rgba(0, 0, 0, 0.3);
}
```

### 8.2 Dark Mode Implementation
```css
/* Theme Toggle */
.theme-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-2);
  border-radius: 0.375rem;
  transition: background-color 0.2s ease;
}

.theme-toggle:hover {
  background-color: var(--gray-100);
}

[data-theme="dark"] .theme-toggle:hover {
  background-color: var(--bg-tertiary);
}

/* Dark Mode Styles */
[data-theme="dark"] .card {
  background-color: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--text-primary);
}

[data-theme="dark"] .form-input {
  background-color: var(--bg-tertiary);
  border-color: var(--border-color);
  color: var(--text-primary);
}
```

## 9. Performance Optimization

### 9.1 CSS Optimization
```css
/* CSS Custom Properties for Performance */
:root {
  --transition-fast: 0.15s ease;
  --transition-normal: 0.2s ease;
  --transition-slow: 0.3s ease;
}

/* Hardware Acceleration */
.smooth-transition {
  transform: translateZ(0);
  will-change: transform;
  backface-visibility: hidden;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 9.2 Image Optimization
```css
/* Responsive Images */
.responsive-image {
  width: 100%;
  height: auto;
  object-fit: cover;
  loading: lazy;
}

/* Image Placeholders */
.image-placeholder {
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

This comprehensive UI/UX design document provides a complete visual and interaction design system for the web scraping application, ensuring a professional, accessible, and user-friendly experience across all devices and user types.
