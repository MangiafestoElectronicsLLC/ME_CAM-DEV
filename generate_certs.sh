#!/bin/bash
# Generate self-signed SSL certificates for ME_CAM
# Run on the Pi or copy generated files from Windows
# 
# Usage: bash generate_certs.sh

set -e

CERT_DIR="$HOME/ME_CAM-DEV/certs"
CERT_FILE="$CERT_DIR/certificate.pem"
KEY_FILE="$CERT_DIR/private_key.pem"

echo "🔐 ME_CAM SSL Certificate Generator"
echo "===================================="
echo ""

# Create certs directory
mkdir -p "$CERT_DIR"
echo "📁 Created certificates directory: $CERT_DIR"
echo ""

# Check if certificates already exist
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "⚠️  Certificates already exist:"
    echo "   Certificate: $CERT_FILE"
    echo "   Private Key: $KEY_FILE"
    echo ""
    echo "To regenerate, delete these files first:"
    echo "   rm $CERT_DIR/certificate.pem $CERT_DIR/private_key.pem"
    exit 0
fi

echo "Generating self-signed SSL certificate for ME_CAM..."
echo "This certificate will:"
echo "  ✅ Work for HTTPS connections"
echo "  ✅ Support VPN access"
echo "  ✅ Support domain: me_cam.com"
echo "  ✅ Support localhost and 127.0.0.1"
echo ""

# Generate private key
echo "🔑 Generating 2048-bit RSA private key..."
openssl genrsa -out "$KEY_FILE" 2048 2>/dev/null
echo "✅ Private key generated"
echo ""

# Generate certificate with Subject Alternative Names
echo "🔒 Generating self-signed certificate..."
openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 \
    -subj "/C=US/ST=NY/L=Brockport/O=ME_CAM/CN=me_cam.com" \
    -addext "subjectAltName=DNS:me_cam.com,DNS:localhost,DNS:*.local,IP:127.0.0.1,IP:192.168.1.1/8,IP:10.0.0.0/8" \
    2>/dev/null

echo "✅ Certificate generated"
echo ""

# Set correct permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"
echo "✅ File permissions set correctly"
echo ""

# Verify certificates
echo "📋 Verifying certificate..."
openssl x509 -in "$CERT_FILE" -text -noout | head -20
echo ""

# Show expiration
expiration=$(openssl x509 -in "$CERT_FILE" -noout -enddate | cut -d= -f2)
echo "📅 Certificate expires: $expiration"
echo ""

echo "✅ SSL Certificates Generated Successfully!"
echo ""
echo "Certificates saved to:"
echo "  📄 Certificate: $CERT_FILE"
echo "  🔑 Private Key: $KEY_FILE"
echo ""
echo "Next steps:"
echo "  1. Restart ME_CAM service: sudo systemctl restart mecamera"
echo "  2. Check logs: tail -20 ~/ME_CAM-DEV/logs/mecam_lite.log"
echo "  3. Should see: [HTTPS] Running with SSL/TLS"
echo ""
