#!/bin/bash
# Generate self-signed SSL certificates for ME_CAM

CERT_DIR="$HOME/ME_CAM-DEV/certs"
mkdir -p "$CERT_DIR"

echo "[1/3] Generating self-signed certificate..."
openssl req -x509 -newkey rsa:2048 -keyout "$CERT_DIR/mecam.key" -out "$CERT_DIR/mecam.crt" \
    -days 365 -nodes -subj "/CN=ME_CAM.com/O=ME Camera/C=US" 2>/dev/null

echo "[2/3] Setting permissions..."
chmod 600 "$CERT_DIR/mecam.key"
chmod 644 "$CERT_DIR/mecam.crt"

echo "[3/3] Restarting service..."
sudo systemctl restart mecamera
sleep 3

if sudo systemctl is-active --quiet mecamera; then
    echo ""
    echo "✓ HTTPS enabled!"
    echo "  Access: https://ME_CAM.com:8080"
    echo "  Or: https://10.2.1.47:8080"
    echo ""
    echo "To add ME_CAM.com to your computer:"
    echo "  Windows: C:\Windows\System32\drivers\etc\hosts"
    echo "           Add: 10.2.1.47   ME_CAM.com"
    echo "  Mac/Linux: /etc/hosts"
    echo "             Add: 10.2.1.47   ME_CAM.com"
else
    echo "✗ Service failed to start. Check logs:"
    sudo journalctl -u mecamera -n 20 --no-pager
fi
