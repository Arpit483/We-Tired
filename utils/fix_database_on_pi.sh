#!/bin/bash
# Script to fix database schema on Raspberry Pi
# This deletes the old database so it can be recreated with the new schema

set -e

PI_IP="${1:-192.168.13.16}"
PI_USER="${2:-pi}"
PI_PASSWORD="21291645"

echo "=========================================="
echo "Fixing Database Schema on Raspberry Pi"
echo "=========================================="
echo ""

# Test SSH connection
echo "[*] Testing SSH connection..."
if ! sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$PI_USER@$PI_IP" "echo 'SSH OK'" >/dev/null 2>&1; then
    echo "[ERROR] Cannot connect to Raspberry Pi. Please check:"
    echo "  - Is the Raspberry Pi powered on?"
    echo "  - Is it on the same network?"
    echo "  - Is SSH enabled? (Run 'sudo systemctl status ssh' on the Pi)"
    exit 1
fi

echo "[✓] SSH connection successful"
echo ""

# Backup and delete old database
echo "[*] Backing up old database (if it exists)..."
sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$PI_USER@$PI_IP" << 'ENDSSH'
    cd ~/Map1\ copy || cd ~/Map1_copy || cd ~/vitalradar || pwd
    DB_PATH="app/predictions.db"
    if [ -f "$DB_PATH" ]; then
        BACKUP_NAME="predictions.db.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$DB_PATH" "$BACKUP_NAME"
        echo "[✓] Database backed up to: $BACKUP_NAME"
        rm -f "$DB_PATH"
        echo "[✓] Old database deleted"
    else
        echo "[!] Database file not found at $DB_PATH (this is OK if it's a fresh install)"
    fi
ENDSSH

echo ""
echo "[✓] Database schema fix complete!"
echo ""
echo "Next steps:"
echo "1. Deploy the updated code: ./deploy_to_pi.sh $PI_IP $PI_USER"
echo "2. Restart the Flask application on the Pi"
echo "3. The database will be automatically recreated with the correct schema"
echo ""

