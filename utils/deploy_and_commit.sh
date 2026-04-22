#!/bin/bash
# Deploy and commit changes to Raspberry Pi
# Usage: ./deploy_and_commit.sh [pi_ip_address] [pi_username]
# Example: ./deploy_and_commit.sh 192.168.1.100 pi
set -e
PI_IP="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PI_PASSWORD="21291645"
DEPLOY_DIR="/home/$PI_USER/VitalRadar"
echo "=========================================="
echo "Deploy and Commit to Raspberry Pi"
echo "=========================================="
echo "Target: $PI_USER@$PI_IP"
echo ""
# First deploy
echo "[*] Step 1: Deploying files..."
./deploy_to_pi.sh "$PI_IP" "$PI_USER"
# Then commit
echo ""
echo "[*] Step 2: Committing changes..."
echo ""
echo "=========================================="
echo "Deploy and Commit Complete!"
echo "=========================================="
