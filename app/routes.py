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

# HIGH-04: protect LATEST with a lock so concurrent green-threads see a consistent snapshot
_latest_lock = threading.Lock()
LATEST = {}

terminal_subscribers = []
sensor_subscribers = []
_sub_lock = threading.Lock()

# ---------------------------------------------------------------------------
# CRIT-02 / HIGH-03: TCN engine singleton
#   - Config.VOTING_WINDOW is cached on the engine object after first load so
#     api_predict never needs its own 'from model_tcn_attention_v2 import Config'
#   - A missing model file raises a clear RuntimeError at load time, not silently
# ---------------------------------------------------------------------------
_tcn_engine = None
_tcn_engine_lock = threading.Lock()
_tcn_voting_window = 32   # default; overwritten when engine loads
_tcn_load_failed = False  # set True after a definitive load failure to avoid retrying

def _get_tcn_engine():
    """
    Load TCNInferenceEngine once and cache it.
    Raises RuntimeError if the model file is missing or corrupt.
    Subsequent calls after a failure return None immediately (no retry storm).
    """
    global _tcn_engine, _tcn_voting_window, _tcn_load_failed
    with _tcn_engine_lock:
        if _tcn_load_failed:
            raise RuntimeError(
                "TCN engine previously failed to load. "
                "Restart the server after placing the model file."
            )
        if _tcn_engine is None:
            import sys
            model_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', 'model'))
            model_pt  = os.path.join(model_dir, 'tcn_attention_vitalradar_v2.pt')

            # CRIT-02: fail fast with a descriptive message instead of HTTP 500
            if not os.path.isfile(model_pt):
                _tcn_load_failed = True
                raise RuntimeError(
                    f"[CRIT-02] Model weights not found at: {model_pt}\n"
                    "Run 'python model/download_weights.py' or copy the file manually."
                )

            try:
                if model_dir not in sys.path:
                    sys.path.insert(0, model_dir)

                from model_tcn_attention_v2 import TCNInferenceEngine, Config as TCNConfig
                _tcn_engine = TCNInferenceEngine(model_pt)
                # HIGH-03: store VOTING_WINDOW on the engine so callers never re-import Config
                _tcn_engine._voting_window = TCNConfig.VOTING_WINDOW
                _tcn_voting_window = TCNConfig.VOTING_WINDOW
                logger.info("[CRIT-02] TCNInferenceEngine loaded from %s", model_pt)
            except Exception as load_err:
                _tcn_load_failed = True
                raise RuntimeError(f"TCN engine load failed: {load_err}") from load_err

    return _tcn_engine


# ---------------------------------------------------------------------------
# Subscriber helpers
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Static / SPA serving
# ---------------------------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return app.send_static_file("index.html")
    return render_template("index.html")


# ---------------------------------------------------------------------------
# /api/predict
# ---------------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Accept JSON payload from deep_optimized.py and broadcast to UI.
    Two accepted shapes:
      1. {"distance_series": [...]}  →  run inline TCN inference
      2. Any payload with "breathing" / "left_detected" etc.  →  store & broadcast
    """
    global LATEST
    try:
        payload = request.get_json(force=True, silent=False)
        if not isinstance(payload, dict):
            return jsonify({"error": "Payload must be a JSON object"}), 400
        if "timestamp" not in payload:
            payload["timestamp"] = int(time.time() * 1000)

        # ── Inline TCN path ──────────────────────────────────────────────────
        if "distance_series" in payload:
            import numpy as np
            ds = payload["distance_series"]

            # LOW-01: validate input before touching numpy
            if not isinstance(ds, list) or len(ds) < 64:
                return jsonify({
                    "error": f"distance_series must be a list of >=64 numbers, got {len(ds) if isinstance(ds, list) else type(ds).__name__}"
                }), 400
            if not all(isinstance(v, (int, float)) for v in ds):
                return jsonify({"error": "distance_series must contain only numbers"}), 400

            try:
                engine = _get_tcn_engine()
                vw = getattr(engine, '_voting_window', _tcn_voting_window)
                arr = np.array(ds[-64:], dtype=np.float32)
                detected, conf = engine.predict(arr)
                # distance kept in cm to match deep_optimized.py convention;
                # SensorPanel divides by 100 to display in metres.
                raw_cm = float(arr[-1])
                payload = {
                    "breathing": bool(detected),
                    "status": "detected" if detected else "not_detected",
                    "direction": "center" if detected else "none",
                    "left_detected": bool(detected), "right_detected": False,
                    "left_distance": raw_cm, "right_distance": 0.0,
                    "left_confidence": float(conf), "right_confidence": 0.0,
                    "left_votes": int(conf * vw), "right_votes": 0,
                    "left_freq": 0.0, "right_freq": 0.0,
                    "left_power": 0.0, "right_power": 0.0,
                    "distance": raw_cm, "freq": 0.0, "power": 0.0,
                    "entropy": float(conf), "fft_conf": float(conf), "dl_conf": float(conf),
                    "votes": int(conf * vw), "voting_window": vw,
                    "timestamp": int(time.time() * 1000),
                }
            except RuntimeError as model_err:
                # CRIT-02: model file missing — return 503 with clear message
                logger.critical("Model unavailable: %s", model_err)
                return jsonify({"error": str(model_err)}), 503
            except Exception as infer_err:
                logger.error("Inline inference failed: %s", infer_err)
                return jsonify({"error": str(infer_err)}), 500

        # ── Store & broadcast ─────────────────────────────────────────────────
        with _latest_lock:            # HIGH-04: thread-safe LATEST update
            LATEST = payload
        notify_sensors(payload)
        socketio.emit("sensor_update", payload)

        # HIGH-02: use context-manager so connection is always released
        db_path = os.path.join(os.path.dirname(__file__), "predictions.db")
        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS predictions "
                    "(id INTEGER PRIMARY KEY AUTOINCREMENT, raw_json TEXT, timestamp INTEGER)"
                )
                cur.execute(
                    "INSERT INTO predictions (raw_json, timestamp) VALUES (?, ?)",
                    (json.dumps(payload), payload["timestamp"])
                )
        except sqlite3.Error as db_err:
            logger.error("DB Error: %s", db_err)

        return jsonify({"ok": True}), 200

    except Exception as e:
        logger.error("Error in api_predict: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# /api/latest
# ---------------------------------------------------------------------------
@app.route("/api/latest")
def api_latest():
    with _latest_lock:              # HIGH-04: consistent read
        snapshot = dict(LATEST)
    return jsonify(snapshot), 200


# ---------------------------------------------------------------------------
# /api/terminal
# ---------------------------------------------------------------------------
@app.route("/api/terminal", methods=["POST"])
def api_terminal():
    try:
        payload = request.get_json(force=True, silent=False)
        # Guard: payload may be None or a non-dict JSON value
        if not isinstance(payload, dict):
            return jsonify({"error": "Payload must be a JSON object"}), 400
        line = payload.get("line", "")
        if line:
            notify_terminal(line)
            socketio.emit("terminal_update", {"line": line})
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error("Error in api_terminal: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# /api/system
# ---------------------------------------------------------------------------
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

        if cpu_temp is None and os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    cpu_temp = float(f.read().strip()) / 1000.0
            except OSError:
                pass

        # MED-02: return null (None -> JSON null) instead of -1 sentinel
        return jsonify({
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_temp": cpu_temp,           # None -> null in JSON
            "cpu_temp_available": cpu_temp is not None,
            "s1_connected": os.path.exists("/dev/ttyUSB0"),
            "s2_connected": os.path.exists("/dev/ttyUSB1"),
            "uptime": time.time() - psutil.boot_time(),
        }), 200
    except Exception as e:
        logger.error("Error in api_system: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# /api/model  (static metadata -- no model file needed)
# ---------------------------------------------------------------------------
@app.route("/api/model")
def api_model():
    return jsonify({
        "name": "VitalRadar TCN-Attention v2",
        "window_size": 64,
        "freq_min": 0.15,
        "freq_max": 0.67,
        "confidence_threshold": 0.85,
        "voting_window": 32,
    }), 200


# ---------------------------------------------------------------------------
# /api/history
# ---------------------------------------------------------------------------
@app.route("/api/history")
def api_history():
    try:
        db_path = os.path.join(os.path.dirname(__file__), "predictions.db")
        if not os.path.exists(db_path):
            return jsonify([]), 200

        # HIGH-02: context-manager guarantees connection is closed
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
    except sqlite3.Error as e:
        logger.error("DB Error in api_history: %s", e)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error("Error in api_history: %s", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# /api/scan/*
# ---------------------------------------------------------------------------
SCAN_RESULT = None

@app.route("/api/scan/start", methods=["POST"])
def api_scan_start():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        duration = float(payload.get("duration", 10.0))
        
        import sys
        root_dir = os.path.dirname(os.path.dirname(__file__))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        import deep_optimized
        
        deep_optimized.start_scan(duration)
        socketio.emit("scan_started", {"duration": duration})
        return jsonify({"ok": True, "duration": duration}), 200
    except Exception as e:
        logger.error("Error in api_scan_start: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop():
    global SCAN_RESULT
    try:
        import sys
        root_dir = os.path.dirname(os.path.dirname(__file__))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        import deep_optimized
        
        result = deep_optimized.stop_scan()
        SCAN_RESULT = result
        socketio.emit("scan_complete", result)
        return jsonify(result), 200
    except Exception as e:
        logger.error("Error in api_scan_stop: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/result", methods=["GET"])
def api_scan_result():
    if SCAN_RESULT is None:
        return jsonify({"status": "no_scan"}), 200
    return jsonify(SCAN_RESULT), 200


# ---------------------------------------------------------------------------
# /api/restart  &  /api/stop
# ---------------------------------------------------------------------------
@app.route("/api/restart", methods=["POST"])
def api_restart():
    if request.remote_addr != "127.0.0.1" and not request.remote_addr.startswith("192.168."):
        return jsonify({"error": "Unauthorized"}), 403
    try:
        script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'start.sh'))
        if not os.path.isfile(script):
            return jsonify({"error": f"start.sh not found: {script}"}), 500
        subprocess.run(["pkill", "-f", "deep_optimized.py"], check=False)
        subprocess.Popen(
            ["/bin/bash", script],
            cwd=os.path.dirname(script),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def api_stop():
    if request.remote_addr != "127.0.0.1" and not request.remote_addr.startswith("192.168."):
        return jsonify({"error": "Unauthorized"}), 403
    try:
        subprocess.run(["pkill", "-f", "deep_optimized.py"], check=False)
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# SSE streams
# ---------------------------------------------------------------------------
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
