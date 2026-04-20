#!/bin/bash

# VitalRadar Dual Sensor System Status Script
# ============================================
# This script checks the status of all VitalRadar components

echo "📊 VitalRadar System Status Check"
echo "================================="

# Change to project directory
cd "$(dirname "$0")" || {
    echo "❌ Error: Could not change to project directory"
    exit 1
}

# Function to check service status
check_service_status() {
    local service_name="$1"
    local process_pattern="$2"
    local port="$3"
    
    echo ""
    echo "🔍 $service_name Status:"
    echo "------------------------"
    
    # Check if process is running
    local pids=$(pgrep -f "$process_pattern")
    if [ -n "$pids" ]; then
        echo "   ✅ Running (PIDs: $pids)"
        
        # Show process details
        ps aux | grep -E "$process_pattern" | grep -v grep | while read line; do
            echo "   📋 $line"
        done
        
        # Check port if specified
        if [ -n "$port" ]; then
            if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
                echo "   🌐 Port $port is open"
            else
                echo "   ⚠️  Port $port is not listening"
            fi
        fi
    else
        echo "   ❌ Not running"
    fi
}

# Check system resources
echo "💻 System Resources:"
echo "-------------------"
echo "   🧠 Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "   💾 Disk: $(df -h . | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "   🌡️  CPU Load: $(uptime | awk -F'load average:' '{print $2}')"

# Check hardware connections
echo ""
echo "🔌 Hardware Status:"
echo "------------------"
if [ -e "/dev/ttyUSB0" ]; then
    echo "   ✅ Left Sensor (/dev/ttyUSB0) connected"
else
    echo "   ❌ Left Sensor (/dev/ttyUSB0) not found"
fi

if [ -e "/dev/ttyUSB1" ]; then
    echo "   ✅ Right Sensor (/dev/ttyUSB1) connected"
else
    echo "   ❌ Right Sensor (/dev/ttyUSB1) not found"
fi

# Check USB devices
echo "   📱 USB Devices:"
lsusb | grep -i "serial\|uart\|cp210" | while read line; do
    echo "      🔗 $line"
done

# Check all services
check_service_status "Deep Learning Dual Sensor" "python.*deep_optimized.py"
check_service_status "Flask Web Interface" "python.*app.py" "5050"
check_service_status "GPS Tracking" "python.*neo6m_runner.py"
check_service_status "Firebase Sync" "python.*firebase_bridge.py"

# Check database
echo ""
echo "🗄️  Database Status:"
echo "-------------------"
if [ -f "app/predictions.db" ]; then
    local db_size=$(du -h app/predictions.db | cut -f1)
    local record_count=$(sqlite3 app/predictions.db "SELECT COUNT(*) FROM predictions;" 2>/dev/null || echo "Error")
    echo "   ✅ Database exists (Size: $db_size)"
    echo "   📊 Total records: $record_count"
    
    # Show latest record
    echo "   🕐 Latest record:"
    sqlite3 app/predictions.db "SELECT datetime(timestamp, 'localtime'), status, left_distance, right_distance FROM predictions ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null | while read line; do
        echo "      📝 $line"
    done
else
    echo "   ❌ Database not found"
fi

# Check API endpoints
echo ""
echo "🌐 API Status:"
echo "-------------"
if curl -s --connect-timeout 5 http://localhost:5050/api/latest > /dev/null; then
    echo "   ✅ Flask API responding"
    echo "   🔗 Web interface: http://localhost:5050"
    
    # Get latest data summary
    local api_data=$(curl -s http://localhost:5050/api/latest)
    local total_records=$(echo "$api_data" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('total_detections', 'N/A'))" 2>/dev/null)
    local breathing_count=$(echo "$api_data" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('breathing_count', 'N/A'))" 2>/dev/null)
    
    echo "   📊 API Summary: $total_records total records, $breathing_count detections"
else
    echo "   ❌ Flask API not responding"
fi

# Check log files
echo ""
echo "📄 Log Files:"
echo "------------"
for log_file in deep_learning.log flask_web.log gps_tracking.log firebase_sync.log; do
    if [ -f "$log_file" ]; then
        local size=$(du -h "$log_file" | cut -f1)
        local lines=$(wc -l < "$log_file")
        echo "   📝 $log_file (Size: $size, Lines: $lines)"
    fi
done

echo ""
echo "✨ Status check complete!"
echo "========================"