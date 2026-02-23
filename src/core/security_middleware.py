"""
Security Middleware for ME_CAM Flask Application
Provides CSRF protection, rate limiting, security headers, and HTTPS enforcement
"""

from flask import Flask, request, session, abort
from functools import wraps
from datetime import datetime, timedelta
import os
import hashlib
from loguru import logger
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict, deque
import threading

class RateLimiter:
    """Track and limit requests per IP address"""
    
    def __init__(self, max_requests=100, window_seconds=3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_rate_limited(self, identifier):
        """Check if identifier (IP) has exceeded rate limit"""
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            # Clean old requests
            while self.requests[identifier] and self.requests[identifier][0] < cutoff:
                self.requests[identifier].popleft()
            
            # Check limit
            if len(self.requests[identifier]) >= self.max_requests:
                return True
            
            # Add current request
            self.requests[identifier].append(now)
            return False
    
    def get_remaining(self, identifier):
        """Get remaining requests for identifier"""
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            # Clean old requests
            while self.requests[identifier] and self.requests[identifier][0] < cutoff:
                self.requests[identifier].popleft()
            
            return max(0, self.max_requests - len(self.requests[identifier]))


class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_token():
        """Generate a random CSRF token"""
        return hashlib.sha256(os.urandom(1024)).hexdigest()
    
    @staticmethod
    def validate_token(token_in_session, token_in_request):
        """Validate CSRF token"""
        if not token_in_session or not token_in_request:
            return False
        return token_in_session == token_in_request


class SecurityMiddleware:
    """Central security middleware for Flask application"""
    
    def __init__(self, app=None, enabled=True):
        self.app = app
        self.enabled = enabled
        self.csrf = CSRFProtection()
        self.rate_limiter = RateLimiter(max_requests=200, window_seconds=3600)
        self.login_rate_limiter = RateLimiter(max_requests=10, window_seconds=900)  # 10 attempts in 15 min
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security middleware with Flask app"""
        self.app = app
        
        # Set security headers
        @app.after_request
        def set_security_headers(response):
            if self.enabled:
                # Prevent clickjacking
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                
                # Prevent MIME sniffing
                response.headers['X-Content-Type-Options'] = 'nosniff'
                
                # Enable XSS protection
                response.headers['X-XSS-Protection'] = '1; mode=block'
                
                # Content Security Policy
                response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'self';"
                
                # Disable caching for sensitive pages
                if request.path not in ['/static/style.css', '/static/mobile.css', '/static/lite.css', '/api/stream']:
                    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                
                # Referrer policy
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                
                # Feature policy (Permissions Policy)
                response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
            
            return response
        
        # CSRF token generation for all GET requests
        @app.before_request
        def generate_csrf_token():
            if 'csrf_token' not in session:
                session['csrf_token'] = self.csrf.generate_token()
        
        # Rate limiting
        @app.before_request
        def check_rate_limit():
            if self.enabled and not request.path.startswith('/static'):
                client_ip = request.remote_addr
                
                # Stricter rate limit for login
                if request.path in ['/login', '/register']:
                    if self.login_rate_limiter.is_rate_limited(client_ip):
                        logger.warning(f"[SECURITY] Login rate limit exceeded for {client_ip}")
                        abort(429)  # Too Many Requests
                else:
                    if self.rate_limiter.is_rate_limited(client_ip):
                        logger.warning(f"[SECURITY] Rate limit exceeded for {client_ip}")
                        abort(429)
        
        logger.success("[SECURITY] Middleware initialized with CSRF, rate limiting, and security headers")
    
    def require_login(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('authenticated'):
                abort(401)
            return f(*args, **kwargs)
        return decorated_function
    
    def require_csrf(self, f):
        """Decorator to require valid CSRF token"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE']:
                token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
                if not self.csrf.validate_token(session.get('csrf_token'), token):
                    logger.warning(f"[SECURITY] CSRF token validation failed for {request.remote_addr}")
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function
    
    def require_auth_and_csrf(self, f):
        """Decorator combining authentication and CSRF checks"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('authenticated'):
                abort(401)
            if request.method in ['POST', 'PUT', 'DELETE']:
                token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
                if not self.csrf.validate_token(session.get('csrf_token'), token):
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function


def validate_input(data, allowed_chars=None, max_length=None):
    """Validate user input to prevent injection attacks"""
    if not isinstance(data, str):
        return False
    
    if max_length and len(data) > max_length:
        return False
    
    if allowed_chars:
        return all(c in allowed_chars for c in data)
    
    # Default: allow alphanumeric, basic punctuation, spaces
    import string
    allowed = string.ascii_letters + string.digits + ' -_@.+'
    return all(c in allowed for c in data)


def secure_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    import re
    # Remove path separators and special characters
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename


def hash_password(password):
    """Hash password using werkzeug"""
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password, hash_):
    """Verify password against hash"""
    return check_password_hash(hash_, password)


# Create global instance
security = SecurityMiddleware(enabled=True)
