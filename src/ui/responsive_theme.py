"""CSS for ME_CAM V3.0 - Dark Mode + Mobile Responsive

Features:
- Full mobile responsive design
- Dark mode theme (with light mode fallback)
- Professional modern UI
- Touch-friendly controls
- Battery-saving animation optimization
"""

DASHBOARD_CSS = """
:root {
    /* Light mode colors */
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-tertiary: #e8e8e8;
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --border-color: #cccccc;
    --accent-color: #1e88e5;
    --success-color: #43a047;
    --warning-color: #fb8c00;
    --danger-color: #e53935;
    --info-color: #00bcd4;
    
    --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 8px rgba(0,0,0,0.12);
    --shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
}

@media (prefers-color-scheme: dark) {
    :root {
        /* Dark mode colors */
        --bg-primary: #1a1a1a;
        --bg-secondary: #2d2d2d;
        --bg-tertiary: #3a3a3a;
        --text-primary: #ffffff;
        --text-secondary: #aaaaaa;
        --border-color: #444444;
        --accent-color: #42a5f5;
        --success-color: #66bb6a;
        --warning-color: #ffa726;
        --danger-color: #ef5350;
        --info-color: #26c6da;
        
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 8px rgba(0,0,0,0.4);
        --shadow-lg: 0 8px 16px rgba(0,0,0,0.5);
    }
}

/* Reset & Base */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    transition: background-color 0.3s, color 0.3s;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    margin-bottom: 0.5em;
    color: var(--text-primary);
}

h1 { font-size: 2em; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.25em; }

p {
    margin-bottom: 1em;
    color: var(--text-secondary);
}

/* Layout */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
}

/* Cards */
.card {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
    transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.card-title {
    font-size: 1.25em;
    font-weight: 600;
}

.card-subtitle {
    font-size: 0.9em;
    color: var(--text-secondary);
}

/* Video Feed */
.video-container {
    position: relative;
    width: 100%;
    padding-bottom: 75%;
    background-color: #000;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 1rem;
}

.video-container video,
.video-container img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.video-status {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: rgba(0,0,0,0.7);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.9em;
    z-index: 10;
}

.video-status.active {
    background-color: rgba(67, 160, 71, 0.8);
}

.video-status.stopped {
    background-color: rgba(229, 57, 53, 0.8);
}

/* Status Indicators */
.status-badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 500;
    margin: 0.25rem;
}

.status-badge.online {
    background-color: var(--success-color);
    color: white;
}

.status-badge.offline {
    background-color: var(--danger-color);
    color: white;
}

.status-badge.warning {
    background-color: var(--warning-color);
    color: white;
}

/* Battery Bar */
.battery-container {
    margin: 1rem 0;
}

.battery-bar {
    width: 100%;
    height: 30px;
    background-color: var(--bg-tertiary);
    border: 2px solid var(--border-color);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.battery-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--danger-color), var(--warning-color), var(--success-color));
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.9em;
}

.battery-fill.low {
    background-color: var(--danger-color);
}

.battery-fill.medium {
    background-color: var(--warning-color);
}

.battery-fill.good {
    background-color: var(--success-color);
}

/* Buttons */
button, .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1em;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    touch-action: manipulation;
}

.btn-primary {
    background-color: var(--accent-color);
    color: white;
}

.btn-primary:hover {
    background-color: #1565c0;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.btn-primary:active {
    transform: translateY(0);
}

.btn-secondary {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background-color: var(--border-color);
}

.btn-danger {
    background-color: var(--danger-color);
    color: white;
}

.btn-danger:hover {
    background-color: #c62828;
}

.btn-success {
    background-color: var(--success-color);
    color: white;
}

/* Form Elements */
input, select, textarea {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    font-family: inherit;
    font-size: 1em;
}

input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.1);
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

/* Info/Alert Boxes */
.alert {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    border-left: 4px solid;
}

.alert-info {
    background-color: rgba(0, 188, 212, 0.1);
    border-color: var(--info-color);
    color: var(--info-color);
}

.alert-warning {
    background-color: rgba(251, 140, 0, 0.1);
    border-color: var(--warning-color);
    color: var(--warning-color);
}

.alert-error {
    background-color: rgba(229, 57, 53, 0.1);
    border-color: var(--danger-color);
    color: var(--danger-color);
}

.alert-success {
    background-color: rgba(67, 160, 71, 0.1);
    border-color: var(--success-color);
    color: var(--success-color);
}

/* Loading Spinner */
.spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-color);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Navigation */
nav {
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    padding: 1rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-sm);
}

nav a {
    color: var(--text-primary);
    text-decoration: none;
    margin-right: 1.5rem;
    font-weight: 500;
    transition: color 0.2s;
}

nav a:hover {
    color: var(--accent-color);
}

/* Mobile Navbar */
@media (max-width: 768px) {
    nav {
        padding: 0.75rem;
    }
    
    nav a {
        display: inline-block;
        margin: 0.25rem;
        padding: 0.5rem 1rem;
        font-size: 0.9em;
    }
}

/* Responsive Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background-color: var(--bg-tertiary);
    font-weight: 600;
}

tr:hover {
    background-color: var(--bg-tertiary);
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .container {
        padding: 0.5rem;
    }
    
    h1 { font-size: 1.5em; }
    h2 { font-size: 1.25em; }
    
    button, .btn {
        width: 100%;
        padding: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    input, select, textarea {
        font-size: 16px; /* Prevent zoom on iOS */
    }
    
    table {
        font-size: 0.9em;
    }
    
    th, td {
        padding: 0.5rem;
    }
}

/* Hamburger Menu */
.hamburger {
    display: none;
    flex-direction: column;
    cursor: pointer;
    gap: 0.35rem;
}

.hamburger span {
    width: 25px;
    height: 3px;
    background-color: var(--text-primary);
    transition: all 0.3s;
}

@media (max-width: 640px) {
    .hamburger {
        display: flex;
    }
    
    nav {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease-out;
    }
    
    nav.open {
        max-height: 500px;
    }
}

/* Motion Event Cards */
.motion-event {
    background-color: var(--bg-secondary);
    border: 1px solid var(--warning-color);
    border-left: 4px solid var(--warning-color);
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
}

.motion-event.high-confidence {
    border-left-color: var(--danger-color);
}

/* Settings Panel */
.settings-group {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid var(--border-color);
}

.settings-group label {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
}

.settings-group input[type="checkbox"],
.settings-group input[type="radio"] {
    width: auto;
    margin-right: 0.5rem;
    margin-bottom: 0;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* Print Styles */
@media print {
    nav, .hamburger, button {
        display: none;
    }
    
    .card {
        page-break-inside: avoid;
    }
}
"""

DASHBOARD_JS = """
// ME_CAM V3.0 Dashboard JavaScript

// Theme Management
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'auto';
        this.apply();
    }
    
    apply() {
        if (this.theme === 'auto') {
            const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', this.theme);
        }
    }
    
    toggle() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.apply();
    }
}

// API Service
class APIService {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }
    
    async fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    async getBattery() {
        return this.fetch('/battery');
    }
    
    async getDeviceInfo() {
        return this.fetch('/device_info');
    }
    
    async getMotionEvents(limit = 10) {
        return this.fetch(`/motion_events?limit=${limit}`);
    }
}

// Dashboard Manager
class Dashboard {
    constructor() {
        this.api = new APIService();
        this.theme = new ThemeManager();
        this.updateInterval = setInterval(() => this.refresh(), 5000);
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.refresh();
    }
    
    setupEventListeners() {
        // Theme toggle
        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.theme.toggle());
        }
        
        // Hamburger menu
        const hamburger = document.querySelector('.hamburger');
        const nav = document.querySelector('nav');
        if (hamburger) {
            hamburger.addEventListener('click', () => {
                nav.classList.toggle('open');
            });
        }
    }
    
    async refresh() {
        try {
            await this.updateBatteryStatus();
            await this.updateDeviceInfo();
            await this.updateMotionEvents();
        } catch (error) {
            console.error('Refresh failed:', error);
        }
    }
    
    async updateBatteryStatus() {
        const data = await this.api.getBattery();
        const batteryEl = document.getElementById('battery-status');
        
        if (batteryEl && data) {
            const percent = data.percent || 0;
            const runtime = `${data.runtime_hours || 0}h ${data.runtime_minutes || 0}m`;
            const powerSource = data.power_source || 'Unknown';
            
            batteryEl.innerHTML = `
                <div class="battery-bar">
                    <div class="battery-fill" style="width: ${percent}%;">
                        ${percent}%
                    </div>
                </div>
                <p>Power: ${powerSource} | Runtime: ${runtime}</p>
                <p style="font-size: 0.9em; color: var(--text-secondary);">${data.display_text}</p>
            `;
        }
    }
    
    async updateDeviceInfo() {
        const data = await this.api.getDeviceInfo();
        if (data) {
            document.getElementById('device-model').textContent = data.model || 'Unknown';
            document.getElementById('device-storage').textContent = `${data.storage_used}GB / ${data.storage_total}GB`;
            document.getElementById('wifi-signal').textContent = data.wifi_signal || 'N/A';
        }
    }
    
    async updateMotionEvents() {
        const data = await this.api.getMotionEvents(5);
        const container = document.getElementById('recent-events');
        
        if (container) {
            if (!data || data.length === 0) {
                container.innerHTML = '<p>No motion events yet</p>';
                return;
            }
            
            container.innerHTML = data.map(event => `
                <div class="motion-event">
                    <p><strong>${new Date(event.timestamp).toLocaleString()}</strong></p>
                    <p>Confidence: ${(event.confidence * 100).toFixed(0)}%</p>
                    ${event.has_video ? '<p>✓ Video recorded</p>' : ''}
                </div>
            `).join('');
        }
    }
    
    destroy() {
        clearInterval(this.updateInterval);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
"""

def get_dashboard_css():
    """Return dashboard CSS."""
    return DASHBOARD_CSS

def get_dashboard_js():
    """Return dashboard JavaScript."""
    return DASHBOARD_JS
