#!/bin/bash
# Start VitalRadar stack
cd "$(dirname "$0")"
source venv/bin/activate
echo "=========================================="
echo "Starting VitalRadar System"
echo "=========================================="
echo ""
# Check if Flask is already running
if lsof -Pi :5050 -sTCP:LISTEN -t >/dev/null ; then
    echo "[!] Flask is already running on port 5050"
    echo "[*] Stopping existing Flask process..."
    pkill -f "python.*app.py" || true
    sleep 2
fi
# Start Flask app
echo "[*] Starting Flask application..."
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "[✓] Flask started (PID: $FLASK_PID)"
# Wait for Flask to be ready
echo "[*] Waiting for Flask to be ready..."
python wait_for_flask.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Flask failed to start. Check flask.log for details."
    kill $FLASK_PID 2>/dev/null
    exit 1
fi
echo "[✓] Flask is ready!"
# Start deep learning detection
echo "[*] Starting deep learning detection..."
python deep.py > deep.log 2>&1 &
DEEP_PID=$!
echo "[✓] Deep learning started (PID: $DEEP_PID)"
sleep 2
sleep 2
echo ""
echo "=========================================="
echo "All services started!"
echo "=========================================="
echo ""
echo "Service PIDs:"
echo "  Flask:    $FLASK_PID"
echo "  Deep:     $DEEP_PID"
echo ""
echo "Logs:"
echo "  Flask:    flask.log"
echo "  Deep:     deep.log"
echo ""
echo "Access dashboard at: http://localhost:5050"
echo ""
echo ""
# Save PIDs to file for easy stopping
# Wait for all background processes
wait
