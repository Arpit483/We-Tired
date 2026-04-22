#!/bin/bash
# VitalRadar Dual Sensor System Startup Script
# ==============================================
# This script starts all components of the VitalRadar system:
# - Dual LD2410 sensor detection (deep_optimized.py)
# - Flask web interface (app.py)
echo "🎯 Starting VitalRadar Dual Sensor Detection System..."
echo "=================================================="
# Change to project directory
cd "$(dirname "$0")" || {
    echo "❌ Error: Could not change to project directory"
    exit 1
}
# Function to check if a process is running
check_process() {
    local process_name="$1"
    if pgrep -f "$process_name" > /dev/null; then
        echo "✅ $process_name is already running"
        return 0
    else
        return 1
    fi
}
# Function to start a service
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="$3"
    echo "🚀 Starting $service_name..."
    if check_process "$command"; then
        echo "   → Already running, skipping"
        return 0
    fi
    # Start the service
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    # Wait a moment and check if it started successfully
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ $service_name started successfully (PID: $pid)"
        echo "$pid" > "${service_name,,}.pid"
        return 0
    else
        echo "   ❌ Failed to start $service_name"
        return 1
    fi
}
# Kill existing processes first
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*deep_optimized.py" 2>/dev/null && echo "   → Stopped old deep learning processes"
pkill -f "python.*app.py" 2>/dev/null && echo "   → Stopped old Flask processes"
# Wait for processes to fully terminate
sleep 3
echo ""
echo "🔧 Checking system requirements..."
# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create one first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi
# Check if sensors are connected
echo "🔍 Checking sensor connections..."
if [ ! -e "/dev/ttyUSB0" ]; then
    echo "⚠️  Warning: Left sensor (/dev/ttyUSB0) not found"
fi
if [ ! -e "/dev/ttyUSB1" ]; then
    echo "⚠️  Warning: Right sensor (/dev/ttyUSB1) not found"
fi
# Check if model file exists
if [ ! -f "cnn_lstm_fast_final_model.pt" ]; then
    echo "⚠️  Warning: Deep learning model file not found"
fi
echo ""
echo "🚀 Starting all services..."
# Activate virtual environment for all Python processes
source venv/bin/activate
# 1. Start Deep Learning Dual Sensor Detection
start_service "Deep_Learning" "python3 deep_optimized.py" "deep_learning.log"
# 2. Start Flask Web Interface
start_service "Flask_Web" "python app.py" "flask_web.log"
echo ""
echo "📊 System Status Check..."
sleep 3
# Check all services
echo "🔍 Checking running processes:"
ps aux | grep -E "(deep_optimized|app\.py)" | grep -v grep | while read line; do
    echo "   ✅ $line"
done
echo ""
echo "📡 Testing API endpoints..."
# Test Flask API
if curl -s http://localhost:5050/api/latest > /dev/null; then
    echo "   ✅ Flask API responding on http://localhost:5050"
    echo "   🌐 Web interface: http://localhost:5050"
else
    echo "   ❌ Flask API not responding"
fi
echo ""
echo "📋 Log Files Created:"
echo "   📄 Deep Learning: deep_learning.log"
echo "   📄 Flask Web: flask_web.log"
echo ""
echo "🎯 VitalRadar System Started Successfully!"
echo "=================================================="
echo "📱 Access the web interface at: http://localhost:5050"
echo "📊 Monitor logs with: tail -f *.log"
echo "🛑 Stop all services with: ./stop_vitalradar.sh"
echo ""
echo "🔍 Real-time sensor monitoring:"
echo "   Left Sensor (S1): /dev/ttyUSB0"
echo "   Right Sensor (S2): /dev/ttyUSB1"
echo ""
echo "✨ System is ready for person detection!"