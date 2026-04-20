#!/bin/bash
# Test SSH connection to Raspberry Pi with detailed diagnostics
# Usage: ./test_ssh_connection.sh [pi_ip_address] [pi_username]

set -e

PI_IP="${1:-192.168.13.16}"
PI_USER="${2:-pi}"
PI_PASSWORD="21291645"

echo "=========================================="
echo "SSH Connection Diagnostic Tool"
echo "=========================================="
echo "Target: $PI_USER@$PI_IP"
echo ""

# Test 1: Ping test
echo "[*] Test 1: Checking network connectivity..."
if ping -c 2 -W 2 "$PI_IP" > /dev/null 2>&1; then
    echo "[✓] Pi is reachable on network"
else
    echo "[✗] Pi is NOT reachable on network"
    echo "    - Check if Pi is powered on"
    echo "    - Check if Pi is on the same network"
    echo "    - Try: ping $PI_IP"
    echo ""
    echo "    Attempting to find Pi on network..."
    echo "    Scanning for Raspberry Pi devices..."
    if command -v arp > /dev/null; then
        arp -a | grep -i "b8:27:eb\|dc:a6:32\|e4:5f:01" || echo "    No Raspberry Pi MAC addresses found"
    fi
    exit 1
fi
echo ""

# Test 2: Port 22 (SSH) test
echo "[*] Test 2: Checking if SSH port (22) is open..."
if command -v nc > /dev/null; then
    if nc -z -w 2 "$PI_IP" 22 2>/dev/null; then
        echo "[✓] SSH port (22) is open"
    else
        echo "[✗] SSH port (22) is NOT open"
        echo "    - SSH service may not be running on Pi"
        echo "    - Firewall may be blocking port 22"
        echo "    - Try enabling SSH on Pi: sudo systemctl enable ssh && sudo systemctl start ssh"
    fi
else
    echo "[!] 'nc' (netcat) not found, skipping port test"
    echo "    Install with: brew install netcat (Mac) or apt-get install netcat (Linux)"
fi
echo ""

# Test 3: SSH connection test
echo "[*] Test 3: Testing SSH connection..."
echo "    Attempting connection (this may take a few seconds)..."
if sshpass -p "$PI_PASSWORD" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$PI_USER@$PI_IP" "echo 'SSH connection successful'" 2>&1; then
    echo "[✓] SSH connection successful!"
    echo ""
    echo "[*] Test 4: Testing remote command execution..."
    if sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_IP" "whoami && hostname && pwd" 2>&1; then
        echo "[✓] Remote commands working correctly"
    fi
else
    echo "[✗] SSH connection FAILED"
    echo ""
    echo "Common issues and solutions:"
    echo ""
    echo "1. SSH not enabled on Pi:"
    echo "   On Pi, run: sudo systemctl enable ssh && sudo systemctl start ssh"
    echo ""
    echo "2. Wrong IP address:"
    echo "   On Pi, run: hostname -I"
    echo "   Or try: ping raspberrypi.local"
    echo ""
    echo "3. Wrong username/password:"
    echo "   Default username: pi"
    echo "   Check password is correct"
    echo ""
    echo "4. SSH key issues:"
    echo "   Try: ssh-keygen -R $PI_IP"
    echo ""
    echo "5. Try manual connection:"
    echo "   ssh $PI_USER@$PI_IP"
    echo "   (Enter password when prompted)"
    exit 1
fi

echo ""
echo "=========================================="
echo "All tests passed! SSH is working."
echo "=========================================="
echo ""
echo "You can now run:"
echo "  ./deploy_to_pi.sh $PI_IP $PI_USER"
echo "  ./commit_on_pi.sh $PI_IP $PI_USER 'Your message'"
echo ""

