#!/usr/bin/env python3
"""
HTTPS Certificate Generation & SSL Setup for ME_CAM

Creates self-signed certificates for secure HTTPS connections.
Valid for 5 years. Automatically used by Flask app.

Usage: python3 setup_https.py [hostname]
Example: python3 setup_https.py mecamdev2.local
"""

import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta


def setup_https(hostname="localhost"):
    """Generate self-signed certificate for HTTPS."""
    
    certs_dir = Path.home() / "ME_CAM-DEV" / "certs"
    certs_dir.mkdir(parents=True, exist_ok=True)
    
    cert_file = certs_dir / "certificate.crt"
    key_file = certs_dir / "private.key"
    
    print(f"📜 HTTPS Certificate Setup for ME_CAM")
    print(f"{'='*60}")
    print(f"Hostname: {hostname}")
    print(f"Certificate path: {cert_file}")
    print(f"Key path: {key_file}")
    print(f"Valid for: 5 years")
    
    # Check if certs already exist
    if cert_file.exists() and key_file.exists():
        print(f"\n⚠️  Certificates already exist.")
        response = input("Regenerate? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Using existing certificates.")
            return True
    
    # Generate self-signed certificate
    print(f"\n🔐 Generating self-signed certificate...")
    
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", "1825",  # 5 years
        "-nodes",  # No password
        "-subj", f"/CN={hostname}/O=ME_CAM/C=US"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"❌ Certificate generation failed: {result.stderr}")
            return False
        
        # Set permissions
        os.chmod(key_file, 0o600)
        os.chmod(cert_file, 0o644)
        
        print(f"✅ Certificate created successfully!")
        print(f"\n📊 Certificate Details:")
        
        # Display cert info
        verify_cmd = ["openssl", "x509", "-in", str(cert_file), "-text", "-noout"]
        result = subprocess.run(verify_cmd, capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        for line in lines:
            if any(x in line for x in ['Subject:', 'Issuer:', 'Not Before', 'Not After', 'Public-Key:']):
                print(f"  {line.strip()}")
        
        print(f"\n✅ Ready for HTTPS! The app will use these certificates.")
        print(f"⚠️  Browsers will show 'Not Secure' warning (expected for self-signed)")
        print(f"   This is normal and doesn't affect security.")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ openssl not found. Install: sudo apt install openssl")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ Certificate generation timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def verify_https_ready():
    """Check if HTTPS is configured and ready."""
    certs_dir = Path.home() / "ME_CAM-DEV" / "certs"
    cert_file = certs_dir / "certificate.crt"
    key_file = certs_dir / "private.key"
    
    if not cert_file.exists():
        print(f"❌ Certificate not found: {cert_file}")
        return False
    
    if not key_file.exists():
        print(f"❌ Private key not found: {key_file}")
        return False
    
    print(f"✅ HTTPS ready!")
    print(f"   Certificate: {cert_file}")
    print(f"   Private Key: {key_file}")
    return True


if __name__ == "__main__":
    hostname = sys.argv[1] if len(sys.argv) > 1 else "me-cam"
    
    if setup_https(hostname):
        verify_https_ready()
        sys.exit(0)
    else:
        sys.exit(1)
