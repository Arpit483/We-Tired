#!/bin/bash
# Quick deploy and run commands for Raspberry Pi

PI_IP="192.168.13.16"
PI_USER="pi"

echo "=========================================="
echo "VitalRadar - Quick Deploy & Run"
echo "=========================================="
echo ""
echo "Choose an option:"
echo "1. Deploy files to Pi"
echo "2. Commit changes on Pi"
echo "3. Deploy + Commit (all-in-one)"
echo "4. SSH into Pi"
echo "5. Test SSH connection"
echo "6. Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo "[*] Deploying files..."
        ./deploy_to_pi.sh $PI_IP $PI_USER
        ;;
    2)
        read -p "Enter commit message: " msg
        echo "[*] Committing changes..."
        ./commit_on_pi.sh $PI_IP $PI_USER "$msg"
        ;;
    3)
        echo "[*] Deploying and committing..."
        ./deploy_and_commit.sh $PI_IP $PI_USER
        ;;
    4)
        echo "[*] Connecting to Raspberry Pi..."
        ssh raspberrypi
        ;;
    5)
        echo "[*] Testing SSH connection..."
        ./test_ssh_connection.sh $PI_IP $PI_USER
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
