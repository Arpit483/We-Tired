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

LATEST = {}
terminal_subscribers = []
sensor_subscribers = []
_sub_lock = threading.Lock()

# Module-level TCN engine singleton (loaded on first distance_series request)
_tcn_engine = None
_tcn_engine_lock = threading.Lock()

def _get_tcn_engine():
    global _tcn_engine
    with _tcn_engine_lock:
        if _tcn_engine is None:
            import sys
            import numpy as np
            model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
            sys.path.insert(0, model_dir)
            from model_tcn_attention_v2 import TCNInferenceEngine
            _tcn_engine = TCNInferenceEngine(
                os.path.join(model_dir, 'tcn_attention_vitalradar_v2.pt'))
    return _tcn_engine

def notify_terminal(line):
    with _sub_lock:
        subs = list(terminal_subscribers)
    for sub in subs:
        try:
            sub.put_nowait(f"data: {json.dumps({'line': line})}\n\n")
        except queue.Full:
            pass

def notify_sensors(data):
    with _sub_lock:
        subs = list(sensor_subscribers)
    for sub in subs:
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

        if "distance_series" in payload:
            import numpy as np
            try:
                engine = _get_tcn_engine()
                from model_tcn_attention_v2 import Config
                arr = np.array(payload["distance_series"][-64:], dtype=np.float32)
                detected, conf = engine.predict(arr)
                payload = {
                    "breathing": detected,
                    "status": "detected" if detected else "not_detected",
                    "direction": "center" if detected else "none",
                    "left_detected": detected, "right_detected": False,
                    "left_distance": arr[-1] / 100.0, "right_distance": 0,
                    "left_confidence": conf, "right_confidence": 0,
                    "left_votes": int(conf * Config.VOTING_WINDOW),
                    "right_votes": 0,
                    "left_freq": 0, "right_freq": 0,
                    "left_power": 0, "right_power": 0,
                    "distance": arr[-1] / 100.0, "freq": 0, "power": 0,
                    "entropy": conf, "fft_conf": conf, "dl_conf": conf,
                    "votes": int(conf * Config.VOTING_WINDOW),
                    "voting_window": Config.VOTING_WINDOW,
                    "timestamp": int(time.time() * 1000)
                }
            except Exception as infer_err:
                logger.error(f"Inline inference failed: {infer_err}")
                return jsonify({"error": str(infer_err)}), 500

        LATEST = payload
        notify_sensors(payload)
        socketio.emit("sensor_update", payload)
        
        # Save to DB for history
        try:
            db_path = os.path.join(os.path.dirname(__file__), "predictions.db")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, raw_json TEXT, timestamp INTEGER)"
            )
            cur.execute(
                "INSERT INTO predictions (raw_json, timestamp) VALUES (?, ?)", 
                (json.dumps(payload), payload["timestamp"])
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            logger.error(f"DB Error: {db_err}")
            
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Error in api_predict: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/latest")
def api_latest():
    """
    Return latest prediction dictionary.
    """
    return jsonify(LATEST), 200

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
        cpu_temp = None
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps and "cpu_thermal" in temps:
                cpu_temp = temps["cpu_thermal"][0].current
            elif temps and "coretemp" in temps:
                cpu_temp = temps["coretemp"][0].current
        
        # Fallback for some Raspberry Pi kernels where psutil fails
        if cpu_temp is None and os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    cpu_temp = float(f.read().strip()) / 1000.0
            except:
                pass

        if cpu_temp is None:
            cpu_temp = -1

        return jsonify({
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_temp": cpu_temp,
            "cpu_temp_available": cpu_temp >= 0,
            "s1_connected": os.path.exists("/dev/ttyUSB0"),
            "s2_connected": os.path.exists("/dev/ttyUSB1"),
            "uptime": time.time() - psutil.boot_time()
        }), 200
    except Exception as e:
        logger.error(f"Error in api_system: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/model")
def api_model():
    return jsonify({
        "name": "VitalRadar TCN-Attention v2",
        "window_size": 64,
        "freq_min": 0.15,
        "freq_max": 0.67,
        "confidence_threshold": 0.85,
        "voting_window": 32
    }), 200

@app.route("/api/history")
def api_history():
    try:
        # Assuming predictions.db is in app/
        db_path = os.path.join(os.path.dirname(__file__), "predictions.db")
        if not os.path.exists(db_path):
            return jsonify([]), 200
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT raw_json FROM predictions ORDER BY id DESC LIMIT 500")
        rows = cur.fetchall()
        conn.close()
        
        history_data = []
        for row in reversed(rows):
            if row[0]:
                try:
                    history_data.append(json.loads(row[0]))
                except:
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
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'start.sh')
        if not os.path.exists(script):
            return jsonify({"error": f"start.sh not found: {script}"}), 500
        subprocess.run(["pkill", "-f", "deep_optimized.py"])
        subprocess.Popen(["/bin/bash", script],
                         cwd=os.path.dirname(script),
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
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
    with _sub_lock:
        subscribers_list.append(q)
    try:
        while True:
            try:
                msg = q.get(timeout=25.0)
                yield msg
            except queue.Empty:
                yield ": keepalive\n\n"
    finally:
        with _sub_lock:
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
