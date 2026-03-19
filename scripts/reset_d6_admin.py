#!/usr/bin/env python3
# Reset D6 admin account - Run on D6 via SSH

import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = "instance/users.db"

try:
    os.makedirs("instance", exist_ok=True)
    
    # Backup existing if it exists
    if os.path.exists(db_path):
        import shutil
        backup_path = db_path + ".backup"
        shutil.copy2(db_path, backup_path)
        print(f"✓ Backed up existing DB to {backup_path}")
    
    # Create/reset users table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop old table
    cursor.execute("DROP TABLE IF EXISTS user")
    
    # Create new users table
    cursor.execute("""
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            pin TEXT DEFAULT '1234',
            role TEXT DEFAULT 'admin'
        )
    """)
    
    # Insert admin user
    admin_password_hash = generate_password_hash("admin123")
    cursor.execute(
        "INSERT INTO user (username, password, pin, role) VALUES (?, ?, ?, ?)",
        ("admin", admin_password_hash, "1234", "admin")
    )
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT username, role FROM user")
    users = cursor.fetchall()
    print(f"✓ Admin account created")
    print(f"✓ Users in DB: {users}")
    
    conn.close()
    print("\n✓ SUCCESS: Login with admin / admin123")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
