from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import logging

socketio = SocketIO()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS for standard HTTP requests
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")
    
    with app.app_context():
        from . import routes
    
    return app