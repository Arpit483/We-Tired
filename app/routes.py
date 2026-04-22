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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Serve React App for all paths
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    return app.send_static_file("index.html")

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
    if request.remote_addr != "127.0.0.1":
        return jsonify({"error": "Unauthorized"}), 403
    try:
        subprocess.run(["pkill", "-f", "deep_optimized.py"])
        subprocess.Popen(["./start.sh"]) # Or specific runner script
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stop", methods=["POST"])
def api_stop():
    if request.remote_addr != "127.0.0.1":
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
