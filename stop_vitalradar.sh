#!/bin/bash
# VitalRadar Dual Sensor System Stop Script
# ==========================================
# This script stops all components of the VitalRadar system
echo "🛑 Stopping VitalRadar Dual Sensor Detection System..."
echo "====================================================="
# Change to project directory
cd "$(dirname "$0")" || {
    echo "❌ Error: Could not change to project directory"
    exit 1
}
# Function to stop a service by name
stop_service() {
    local service_name="$1"
    local process_pattern="$2"
    echo "🛑 Stopping $service_name..."
    # Find and kill processes
    local pids=$(pgrep -f "$process_pattern")
    if [ -n "$pids" ]; then
        echo "$pids" | while read pid; do
            if kill -TERM "$pid" 2>/dev/null; then
                echo "   ✅ Stopped process $pid"
            fi
        done
        # Wait for graceful shutdown
        sleep 2
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_pattern")
        if [ -n "$remaining_pids" ]; then
            echo "   🔨 Force killing remaining processes..."
            echo "$remaining_pids" | while read pid; do
                kill -KILL "$pid" 2>/dev/null && echo "   ✅ Force killed process $pid"
            done
        fi
    else
        echo "   ℹ️  No $service_name processes found"
    fi
    # Remove PID file if exists
    local pid_file="${service_name,,}.pid"
    [ -f "$pid_file" ] && rm -f "$pid_file"
}
# Stop all services
stop_service "Deep_Learning" "python.*deep_optimized.py"
stop_service "Flask_Web" "python.*app.py"
echo ""
echo "🔍 Checking for remaining processes..."
remaining=$(ps aux | grep -E "(deep_optimized|app\.py)" | grep -v grep)
if [ -n "$remaining" ]; then
    echo "⚠️  Some processes may still be running:"
    echo "$remaining"
else
    echo "✅ All VitalRadar processes stopped successfully"
fi
echo ""
echo "🧹 Cleaning up..."
# Optional: Clean up old log files (uncomment if desired)
# echo "   📄 Archiving old logs..."
# mkdir -p logs_archive
# mv *.log logs_archive/ 2>/dev/null || true
echo ""
echo "✅ VitalRadar System Stopped Successfully!"
echo "=========================================="