#!/usr/bin/env python3
"""Fix admin credentials on D1 and D4"""
from werkzeug.security import generate_password_hash
import json

# Generate hash for admin account
password = "TestPassword123"
hash_val = generate_password_hash(password, method='pbkdf2:sha256')

print(f"Generated password hash for admin account:")
print(f"Password: {password}")
print(f"Hash: {hash_val}")
print()

# Create proper users.json structure
users_data = {
    "admin": {
        "password_hash": hash_val,
        "pin": "1234",
        "role": "admin"  # IMPORTANT: Must be "admin" not "user"
    }
}

print("Complete users.json structure:")
print(json.dumps(users_data, indent=2))
