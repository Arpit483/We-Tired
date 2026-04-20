from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Database config
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "predictions.db")
    
    # SQLite configuration for Raspberry Pi
    # Add timeout to handle locking issues, check_same_thread=False for Flask
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'timeout': 20,
            'check_same_thread': False
        }
    }
    app.config['JSON_SORT_KEYS'] = False
    
    # Ensure database directory exists and has proper permissions
    os.makedirs(basedir, exist_ok=True)
    
    db.init_app(app)
    
    with app.app_context():
        from . import routes
        from . import models
        try:
            db.create_all()
            # Ensure database file has proper permissions
            if os.path.exists(db_path):
                os.chmod(db_path, 0o664)
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise
    
    return app