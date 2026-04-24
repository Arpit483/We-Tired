from flask import current_app as app, request, jsonify, render_template, Response
from app import socketio
import time
import logging
import queue
import json
import psutil
import sqlite3
import subprocess
import os
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scan state — fully self-contained, no deep_optimized import needed (BUG-05)
# ---------------------------------------------------------------------------
_scan_active  = False
_scan_results = []        # list of {"detected": bool, "confidence": float}
_scan_lock    = threading.Lock()

LATEST = {}
terminal_subscribers = []
sensor_subscribers = []

def notify_terminal(line):
    for sub in list(terminal_subscribers):
        try:
            sub.put_nowait(f"data: {json.dumps({'line': line})}\n\n")
        except queue.Full:
            pass

def notify_sensors(data):
    for sub in list(sensor_subscribers):
        try:
            sub.put_nowait(f"data: {json.dumps(data)}\n\n")
        except queue.Full:
            pass

# Serve React App for all paths, fallback to template if not built
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # Serve static assets if they exist (JS, CSS, images)
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    
    # If React index.html is built and available, serve it
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return app.send_static_file("index.html")
        
    # Fallback to the vanilla HTML template if React is not built
    return render_template("index.html")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Accept JSON payload from deep_optimized.py and broadcast to UI.
    """
    global LATEST
    try:
        payload = request.get_json(force=True, silent=False)
        if "timestamp" not in payload:
            payload["timestamp"] = int(time.time() * 1000)
            
        LATEST = payload
        notify_sensors(payload)
        socketio.emit("sensor_update", payload)

        # ── Scan mode: accumulate per-frame result (BUG-04 fix) ─────────────
        global _scan_active, _scan_results
        with _scan_lock:
            if _scan_active:
                _scan_results.append({
                    "detected":   bool(payload.get("breathing", False)),
                    "confidence": float(payload.get("dl_conf",
                                        payload.get("fft_conf",
                                        payload.get("entropy", 0.0)))),
                })

        # Save to DB for history
        try:
            db_path = os.path.join(os.path.dirname(__file__), "predictions.db")
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, raw_json TEXT, timestamp INTEGER)"
                )
                cur.execute(
                    "INSERT INTO predictions (raw_json, timestamp) VALUES (?, ?)",
                    (json.dumps(payload), payload["timestamp"])
                )
        except Exception as db_err:
            logger.error(f"DB Error: {db_err}")
            
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Error in api_predict: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/latest")
def api_latest():
    """Return latest prediction dictionary."""
    if not LATEST:
        return jsonify({
            "breathing": False, "status": "not_detected", "direction": "none",
            "left_detected": False, "left_distance": 0, "right_detected": False,
            "right_distance": 0, "left_confidence": 0, "right_confidence": 0,
            "distance": 0, "freq": 0, "power": 0, "entropy": 0,
            "fft_conf": 0, "dl_conf": 0, "timestamp": int(time.time() * 1000)
        }), 200
    return jsonify(LATEST), 200


# ---------------------------------------------------------------------------
# /api/scan/*  — full scan pipeline with all audit-report fixes applied
# ---------------------------------------------------------------------------

@app.route("/api/scan/start", methods=["POST"])
def api_scan_start():
    """Arm a new scan session. Returns 409 if one is already running."""
    global _scan_active, _scan_results
    with _scan_lock:
        if _scan_active:
            return jsonify({"error": "scan already running"}), 409
        _scan_active = True
        _scan_results = []
    # BUG-05: do NOT import deep_optimized here — that would create a fresh
    # module copy with different Event objects, not the live subprocess.
    socketio.emit("scan_started", {"duration": 10})
    return jsonify({"ok": True, "duration": 10}), 200


@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop():
    """End the current scan and return an aggregated result."""
    global _scan_active, _scan_results
    with _scan_lock:
        _scan_active = False
        frames = list(_scan_results)
        _scan_results = []

    total_frames    = len(frames)
    detected_frames = sum(1 for f in frames if f["detected"])
    confidence_avg  = (
        sum(f["confidence"] for f in frames) / total_frames
        if total_frames > 0 else 0.0
    )

    # BUG-08 fix: return a distinct state when no sensor data arrived,
    # so the UI can show 'Scan Failed' instead of a false 'No Human' result.
    if total_frames == 0:
        final = "scan_failed"
    elif (detected_frames / total_frames) >= 0.5:
        final = "human_detected"
    else:
        final = "no_human"

    result = {
        "ok":              True,
        "result":          final,
        "detected_frames": detected_frames,
        "total_frames":    total_frames,
        "confidence_avg":  round(confidence_avg, 4),
    }
    socketio.emit("scan_complete", result)
    return jsonify(result), 200


@app.route("/api/scan/result", methods=["GET"])
def api_scan_result():
    """Live frame counter — polled by frontend before calling stop (BUG-01 fix)."""
    with _scan_lock:
        active   = _scan_active
        n_frames = len(_scan_results)
    if active:
        return jsonify({"status": "running", "frames_so_far": n_frames}), 200
    return jsonify({"status": "no_scan"}), 200

@app.route("/api/terminal", methods=["POST"])
def api_terminal():
    """
    Accept terminal line from deep_optimized.py and broadcast to UI.
    """
    try:
        payload = request.get_json(force=True, silent=False)
        line = payload.get("line", "")
        if line:
            notify_terminal(line)
            socketio.emit("terminal_update", {"line": line})
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Error in api_terminal: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/system")
def api_system():
    try:
        # psutil mock for CPU temp if on windows
        cpu_temp = 45.0
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps and "cpu_thermal" in temps:
                cpu_temp = temps["cpu_thermal"][0].current
            elif temps and "coretemp" in temps:
                cpu_temp = temps["coretemp"][0].current
        
        # Fallback for some Raspberry Pi kernels where psutil fails
        if cpu_temp == 45.0 and os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    cpu_temp = float(f.read().strip()) / 1000.0
            except:
                pass

        return jsonify({
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_temp": cpu_temp,
            "s1_connected": os.path.exists("/dev/ttyUSB0"),
            "s2_connected": os.path.exists("/dev/ttyUSB1"),
            "uptime": time.time() - psutil.boot_time()
        }), 200
    except Exception as e:
        logger.error(f"Error in api_system: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def api_history():
    try:
        db_path = os.path.join(os.path.dirname(__file__), "predictions.db")
        if not os.path.exists(db_path):
            return jsonify([]), 200

        # Use context manager — auto-commits and closes even on exception (fixes HTTP 500)
        history_data = []
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT raw_json FROM predictions ORDER BY id DESC LIMIT 500")
            rows = cur.fetchall()

        for row in reversed(rows):
            if row[0]:
                try:
                    history_data.append(json.loads(row[0]))
                except json.JSONDecodeError:
                    pass
        return jsonify(history_data), 200
    except Exception as e:
        logger.error(f"Error in api_history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/restart", methods=["POST"])
def api_restart():
    if request.remote_addr != "127.0.0.1" and not request.remote_addr.startswith("192.168."):
        return jsonify({"error": "Unauthorized"}), 403
    try:
        subprocess.run(["pkill", "-f", "deep_optimized.py"])
        subprocess.Popen(["./start.sh"]) # Or specific runner script
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stop", methods=["POST"])
def api_stop():
    if request.remote_addr != "127.0.0.1" and not request.remote_addr.startswith("192.168."):
        return jsonify({"error": "Unauthorized"}), 403
    try:
        subprocess.run(["pkill", "-f", "deep_optimized.py"])
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def sse_stream(subscribers_list):
    q = queue.Queue(maxsize=100)
    subscribers_list.append(q)
    try:
        while True:
            try:
                msg = q.get(timeout=25.0)
                yield msg
            except queue.Empty:
                yield ": keepalive\n\n"
    finally:
        try:
            subscribers_list.remove(q)
        except ValueError:
            pass

@app.route("/stream/terminal")
def stream_terminal():
    return Response(sse_stream(terminal_subscribers), mimetype="text/event-stream")

@app.route("/stream/sensors")
def stream_sensors():
    return Response(sse_stream(sensor_subscribers), mimetype="text/event-stream")
