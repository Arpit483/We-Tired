#!/bin/bash
# Commit changes directly on Raspberry Pi
# Usage: ./commit_on_pi.sh [pi_ip_address] [pi_username] [commit_message]
set -e
PI_IP="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PI_PASSWORD="21291645"
DEPLOY_DIR="/home/$PI_USER/VitalRadar"
echo "=========================================="
echo "Committing Changes on Raspberry Pi"
echo "=========================================="
echo "Target: $PI_USER@$PI_IP"
echo "Directory: $DEPLOY_DIR"
echo "Commit Message: $COMMIT_MSG"
echo ""
# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "[*] Installing sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            echo "[ERROR] Please install Homebrew first"
            exit 1
        fi
        brew install hudochenkov/sshpass/sshpass 2>/dev/null || echo "[!] sshpass install failed, continuing..."
    else
        sudo apt-get update && sudo apt-get install -y sshpass 2>/dev/null || echo "[!] sshpass install failed, continuing..."
    fi
fi
# Test SSH connection
echo "[*] Testing SSH connection..."
echo "    Attempting to connect to $PI_USER@$PI_IP..."
# First test ping
if ! ping -c 1 -W 2 "$PI_IP" > /dev/null 2>&1; then
    echo "[ERROR] Cannot reach Raspberry Pi at $PI_IP"
    echo "  Run diagnostic: ./test_ssh_connection.sh $PI_IP $PI_USER"
    exit 1
fi
# Then test SSH
if ! sshpass -p "$PI_PASSWORD" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$PI_USER@$PI_IP" "echo 'Connection successful'" 2>/dev/null; then
    echo "[ERROR] Cannot connect to Raspberry Pi via SSH"
    echo "  Run diagnostic: ./test_ssh_connection.sh $PI_IP $PI_USER"
    exit 1
fi
echo "[✓] SSH connection successful"
echo ""
# Commit changes on Raspberry Pi
echo "[*] Committing changes on Raspberry Pi..."
sshpass -p "$PI_PASSWORD" ssh "$PI_USER@$PI_IP" << ENDSSH
cd $DEPLOY_DIR
# Initialize git if not exists
if [ ! -d ".git" ]; then
    echo "[*] Initializing git repository..."
    git init
    echo "*.log" > .gitignore
    echo "*.db" >> .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo "venv/" >> .gitignore
    echo ".pids" >> .gitignore
fi
# Add all files
echo "[*] Adding files to git..."
git add -A
# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "[!] No changes to commit"
    exit 0
fi
# Commit
echo "[*] Committing changes..."
git commit -m "$COMMIT_MSG" || {
    echo "[!] Commit failed or no changes"
    exit 0
}
# Show commit info
echo ""
echo "[✓] Commit successful!"
echo ""
git log -1 --stat
echo ""
echo "Repository status:"
git status --short
ENDSSH
echo ""
echo "=========================================="
echo "Commit Complete!"
echo "=========================================="
echo ""
echo "To view commits on Raspberry Pi:"
echo "  ssh $PI_USER@$PI_IP"
echo "  cd $DEPLOY_DIR"
echo "  git log"
echo ""
