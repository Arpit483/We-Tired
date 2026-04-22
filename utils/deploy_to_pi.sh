#!/bin/bash
# Raspberry Pi Deployment Script for VitalRadar Deep Learning Integration
# Usage: ./deploy_to_pi.sh [PI_IP_ADDRESS]
# Configuration
PI_IP="${1:-192.168.1.100}"  # Use provided IP or default
PI_USER="pi"
PROJECT_PATH="/home/pi/vitalradar"
echo "=========================================="
echo "VitalRadar Pi Deployment Script"
echo "=========================================="
echo "Target: $PI_USER@$PI_IP:$PROJECT_PATH"
echo ""
# Check if Pi is reachable
echo "Checking Pi connectivity..."
if ! ping -c 1 -W 3 $PI_IP > /dev/null 2>&1; then
    echo "❌ Error: Cannot reach Raspberry Pi at $PI_IP"
    echo "Please check:"
    echo "  - Pi is powered on and connected to network"
    echo "  - IP address is correct"
    echo "  - SSH is enabled on Pi"
    exit 1
fi
echo "✅ Pi is reachable"
# Sync project files
echo ""
echo "Syncing project files..."
rsync -avz --progress \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.db' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    . $PI_USER@$PI_IP:$PROJECT_PATH
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to sync files to Pi"
    exit 1
fi
echo "✅ Files synced successfully"
# Setup and restart services on Pi
echo ""
echo "Setting up environment and restarting services..."
ssh $PI_USER@$PI_IP << EOF
    set -e
    cd $PROJECT_PATH
    echo "Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
    echo "Setting file permissions..."
    chmod +x *.py *.sh
    echo "Stopping existing services..."
    pkill -f "python3 app.py" 2>/dev/null || true
    pkill -f "python3 deep.py" 2>/dev/null || true
    sleep 2
    echo "Starting Flask web server..."
    nohup python3 app.py > flask.log 2>&1 &
    FLASK_PID=\$!
    echo "Waiting for Flask to start..."
    sleep 3
    echo "Starting deep learning detection system..."
    nohup python3 deep.py > deep.log 2>&1 &
    DEEP_PID=\$!
    echo ""
    echo "✅ Services started successfully!"
    echo "Flask PID: \$FLASK_PID"
    echo "Deep Learning PID: \$DEEP_PID"
    echo ""
    echo "Access web interface at: http://$PI_IP:5050"
    echo ""
    echo "To monitor logs:"
    echo "  Flask: tail -f $PROJECT_PATH/flask.log"
    echo "  Deep Learning: tail -f $PROJECT_PATH/deep.log"
EOF
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "🎉 Deployment completed successfully!"
    echo "=========================================="
    echo "Web Interface: http://$PI_IP:5050"
    echo ""
    echo "Useful commands:"
    echo "  Connect to Pi: ssh $PI_USER@$PI_IP"
    echo "  View Flask logs: ssh $PI_USER@$PI_IP 'tail -f $PROJECT_PATH/flask.log'"
    echo "  View Deep Learning logs: ssh $PI_USER@$PI_IP 'tail -f $PROJECT_PATH/deep.log'"
    echo "  Check processes: ssh $PI_USER@$PI_IP 'ps aux | grep python3'"
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi