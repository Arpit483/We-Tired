"""
VitalRadar Flask + Socket.IO entry point.
=========================================
IMPORTANT — LOW-02:
  This application MUST be started with:
      python app.py
  Do NOT use plain gunicorn/uWSGI without the eventlet worker class,
  as socketio.run() is never reached in that case and WebSocket transport
  will not function.

  If you must use gunicorn, run:
      gunicorn --worker-class eventlet -w 1 app:app
"""
from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    print("[VITALRADAR] Starting Flask server with SocketIO (eventlet)...")
    print("[VITALRADAR] Access at http://0.0.0.0:5050")
    socketio.run(app, host="0.0.0.0", port=5050, debug=False)
