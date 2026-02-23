"""
Integration patch for web/app.py
Shows how to integrate the new security middleware into your Flask application
Copy these code blocks into the appropriate locations in app.py
"""

# ============================================================
# SECTION 1: Add imports at the top of app.py
# ============================================================

# Add these imports after existing imports:
from src.core.security_middleware import security, validate_input, secure_filename, hash_password, verify_password

# ============================================================
# SECTION 2: Initialize security middleware right after app creation
# ============================================================

# After this line:
# app = Flask(__name__, template_folder='templates', static_folder='static')
# app.secret_key = os.urandom(24)

# Add this:
security.init_app(app)  # Initialize security middleware with CSRF, rate limiting, security headers
logger.success("[APP] Security middleware initialized")

# ============================================================
# SECTION 3: Protect all state-changing routes with CSRF
# ============================================================

# Example: Protect the login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Optional: Validate input to prevent injection
        username = request.form.get("username", "").strip()
        if not validate_input(username, max_length=50):
            return render_template("login.html", error="Invalid username format")
        
        password = request.form.get("password", "")
        if not authenticate(username, password):
            return render_template("login.html", error="Invalid credentials")
        
        session["username"] = username
        session["authenticated"] = True
        logger.info(f"[AUTH] User logged in: {username}")
        return redirect(url_for("index"))
    
    return render_template("login.html")


# Example: Protect a configuration update route
@app.route("/config/save", methods=["POST"])
@security.require_auth_and_csrf
def save_config():
    """Protected route: requires authentication and valid CSRF token"""
    cfg = get_config()
    
    # Validate and sanitize all inputs
    device_name = request.form.get("device_name", "").strip()
    if not validate_input(device_name, max_length=50):
        return jsonify({"error": "Invalid device name"}), 400
    
    cfg["device_name"] = device_name
    save_config(cfg)
    
    logger.info(f"[CONFIG] Settings updated by {session.get('username')}")
    return jsonify({"success": True})


# ============================================================
# SECTION 4: Add password hashing to user creation
# ============================================================

# Update register route:
@app.route("/register", methods=["GET", "POST"])
def register():
    cfg = get_config()
    if cfg.get("bootstrap_required"):
        return render_template("register.html", error="Registration is disabled until the customer account is created by admin.")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        
        # Validation
        if not username or len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters")
        
        if not validate_input(username, max_length=50):
            return render_template("register.html", error="Username contains invalid characters")
        
        if not password or len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")
        
        if password != password_confirm:
            return render_template("register.html", error="Passwords don't match")
        
        if user_exists(username):
            return render_template("register.html", error="Username already exists")
        
        # Hash password before storing
        hashed_password = hash_password(password)
        
        # Create user with hashed password
        if create_user(username, hashed_password):
            logger.info(f"[AUTH] New user registered: {username}")
            return render_template("register.html", success="Account created! Please login.")
        else:
            return render_template("register.html", error="Error creating account")
    
    return render_template("register.html")


# ============================================================
# SECTION 5: Add file upload protection
# ============================================================

@app.route("/upload/video", methods=["POST"])
@security.require_auth_and_csrf
def upload_video():
    """Protected file upload with validation"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Sanitize filename
    safe_name = secure_filename(file.filename)
    if not safe_name:
        return jsonify({"error": "Invalid filename"}), 400
    
    # Validate file type
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
    if not any(safe_name.lower().endswith(ext) for ext in allowed_extensions):
        return jsonify({"error": "Invalid file type"}), 400
    
    # Save file
    cfg = get_config()
    upload_path = os.path.join(BASE_DIR, cfg.get("storage", {}).get("uploads_dir", "uploads"))
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, safe_name)
    file.save(file_path)
    
    logger.info(f"[UPLOAD] File uploaded: {safe_name} by {session.get('username')}")
    return jsonify({"success": True, "filename": safe_name})


# ============================================================
# SECTION 6: Add HTTPS context for production
# ============================================================

# At the bottom of app.py, replace:
# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0', port=8080)

# With:
if __name__ == '__main__':
    import ssl
    
    # Development: HTTP only
    if os.getenv('FLASK_ENV') == 'development':
        app.run(debug=False, host='0.0.0.0', port=8080)
    
    # Production: HTTPS with self-signed certificate
    else:
        cert_path = '/opt/me_cam/certs/cert.pem'
        key_path = '/opt/me_cam/certs/key.pem'
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_path, key_path)
            
            app.run(
                ssl_context=ssl_context,
                host='0.0.0.0',
                port=443,
                debug=False
            )
        else:
            logger.warning("[SSL] Certificate not found, running in HTTP mode")
            app.run(debug=False, host='0.0.0.0', port=8080)


# ============================================================
# SECTION 7: Test security features
# ============================================================

# Add this test route (remove in production):
@app.route("/test/security", methods=["GET"])
def test_security():
    """Test security features - REMOVE IN PRODUCTION"""
    if not os.getenv('DEBUG_MODE'):
        return "Not found", 404
    
    return {
        "csrf_token": session.get('csrf_token'),
        "rate_limiter": {
            "max_requests": security.rate_limiter.max_requests,
            "window_seconds": security.rate_limiter.window_seconds,
            "remaining": security.rate_limiter.get_remaining(request.remote_addr)
        },
        "security_headers": "✓ Enabled"
    }


# ============================================================
# USAGE EXAMPLES
# ============================================================

"""
1. CSRF PROTECTION - Automatic
   - Every GET request generates a CSRF token in session
   - Every POST/PUT/DELETE validates the token
   - Token is automatically injected into all forms by layout.html

2. RATE LIMITING - Automatic
   - 200 requests per hour per IP (general)
   - 10 requests per 15 minutes for /login and /register

3. SECURITY HEADERS - Automatic
   - All responses include X-Frame-Options, CSP, etc.
   - No caching for sensitive pages

4. INPUT VALIDATION - Manual
   from src.core.security_middleware import validate_input
   
   if not validate_input(user_input, max_length=50):
       return "Invalid input", 400

5. FILENAME SANITIZATION - Manual
   from src.core.security_middleware import secure_filename
   
   safe_name = secure_filename(request.files['file'].filename)

6. PASSWORD HASHING - Manual
   from src.core.security_middleware import hash_password, verify_password
   
   hash = hash_password("user_password")
   if verify_password("user_password", hash):
       # Correct password
       pass

7. DECORATOR USAGE
   @security.require_auth_and_csrf      # Requires login + CSRF
   @security.require_auth               # Requires login only
   @security.require_csrf               # Requires CSRF only
"""
