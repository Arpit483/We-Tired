from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import logging

socketio = SocketIO()

# CRIT-01: Restrict CORS to known origins only (not wildcard).
# Add your production hostname to ALLOWED_ORIGINS to permit the Pi's own domain.
ALLOWED_ORIGINS = [
    "http://localhost:5050",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://raspberrypi.local",
    "http://raspberrypi.local:5050",
]

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config['JSON_SORT_KEYS'] = False

    # Reverted CRIT-01 strict restrictions to allow access via dynamic local network IPs
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Reverted Socket.IO CORS to allow wildcard origin access from local IP addresses
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
    )

    with app.app_context():
        from . import routes

    return app