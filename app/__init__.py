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

    # CRIT-01 fix: restrict HTTP CORS to /api/* and the known origin list
    CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

    # CRIT-01 fix: restrict Socket.IO CORS to same origin list
    socketio.init_app(
        app,
        cors_allowed_origins=ALLOWED_ORIGINS,
        async_mode="eventlet",
    )

    with app.app_context():
        from . import routes

    return app