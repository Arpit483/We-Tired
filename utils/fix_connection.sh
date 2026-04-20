#!/bin/bash
# Quick fix script for connection refused errors
# Run this on Raspberry Pi when services can't connect

cd "$(dirname "$0")"
source venv/bin/activate

echo "=========================================="
echo "Fixing Connection Issues"
echo "=========================================="
echo ""

# Kill all existing processes
echo "[*] Stopping all services..."
pkill -f 'python.*(app|deep|neo6m|firebase)' || true
sleep 2

# Check for port conflicts
echo "[*] Checking port 5050..."
if lsof -Pi :5050 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[!] Port 5050 is in use, killing process..."
    sudo kill -9 $(lsof -t -i:5050) 2>/dev/null || true
    sleep 2
fi

# Start Flask
echo "[*] Starting Flask..."
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "[✓] Flask started (PID: $FLASK_PID)"

# Wait for Flask to be ready
echo "[*] Waiting for Flask to be ready..."
python wait_for_flask.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Flask failed to start. Check flask.log:"
    tail -20 flask.log
    kill $FLASK_PID 2>/dev/null
    exit 1
fi

# Start other services
echo "[*] Starting other services..."
python deep.py > deep.log 2>&1 &
DEEP_PID=$!
echo "[✓] Deep learning started (PID: $DEEP_PID)"

python neo6m_runner.py > gps.log 2>&1 &
GPS_PID=$!
echo "[✓] GPS module started (PID: $GPS_PID)"

python firebase_bridge.py > firebase.log 2>&1 &
FIREBASE_PID=$!
echo "[✓] Firebase bridge started (PID: $FIREBASE_PID)"

echo ""
echo "=========================================="
echo "All Services Started!"
echo "=========================================="
echo ""
echo "Test Flask API:"
echo "  curl http://localhost:5050/api/latest"
echo ""
echo "Check logs:"
echo "  tail -f flask.log deep.log gps.log firebase.log"
echo ""

