from flask import current_app as app, request, jsonify, render_template
from .models import db, Prediction, GPSData
from .svminterface import call_predict
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# MAIN DASHBOARD PAGE
# ---------------------------------------------------------------------
@app.route("/")
def index():
    # Make sure this filename matches your template in app/templates/
    # Save your HTML as: app/templates/vitalradar_dashboard.html
    return render_template("index.html")


# ---------------------------------------------------------------------
# API: LATEST PREDICTIONS FOR FRONTEND
# ---------------------------------------------------------------------
@app.route("/api/latest")
def api_latest():
    """
    Return latest predictions in the structure expected by the frontend:
    {
      "total_detections": ...,
      "breathing_count": ...,
      "avg_votes": ...,
      "max_distance": ...,
      "records": [ {...}, ... ]
    }
    """
    try:
        # Check if database is accessible
        try:
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Database connection failed",
                "details": str(db_error),
                "total_detections": 0,
                "breathing_count": 0,
                "avg_votes": 0,
                "max_distance": 0.0,
                "records": []
            }), 500

        # Get last 100 predictions, newest first
        try:
            rows = (
                Prediction.query
                .order_by(Prediction.timestamp.desc())
                .limit(100)
                .all()
            )
        except Exception as query_error:
            logger.error(f"Query error: {query_error}")
            logger.error(traceback.format_exc())
            # Return empty result instead of failing
            rows = []

        # Convert to list of dicts, oldest first for timeline
        try:
            records = [r.as_dict() for r in reversed(rows)]
        except Exception as dict_error:
            logger.error(f"Error converting records to dict: {dict_error}")
            logger.error(traceback.format_exc())
            records = []

        total = len(records)
        breathing_count = sum(1 for r in records if r.get("breathing", False)) if records else 0
        avg_votes = int(sum(r.get("votes", 0) for r in records) / total) if total > 0 else 0
        max_distance = max((r.get("distance", 0.0) for r in records), default=0.0) if records else 0.0

        return jsonify({
            "total_detections": total,
            "breathing_count": breathing_count,
            "avg_votes": avg_votes,
            "max_distance": max_distance,
            "records": records,
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error in api_latest: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "total_detections": 0,
            "breathing_count": 0,
            "avg_votes": 0,
            "max_distance": 0.0,
            "records": []
        }), 500


# ---------------------------------------------------------------------
# API: PREDICT (USED BY SENSOR / DL SCRIPT)
# ---------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Accept JSON payload from ld2410_runner or deep-learning script
    and store prediction in the database.
    """
    try:
        payload = request.get_json(force=True, silent=False)
        result = call_predict(payload)
        status = 200 if "error" not in result else 400
        return jsonify(result), status
    except Exception as e:
        logger.error(f"Error in api_predict: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# API: GPS DATA ENDPOINTS
# ---------------------------------------------------------------------
@app.route("/api/gps", methods=["POST"])
def api_gps():
    """
    Accept GPS data from neo6m_runner.py and store in database.
    Expected JSON payload:
    {
        "latitude": float,
        "longitude": float,
        "altitude": float (optional),
        "speed": float (optional),
        "satellites": int (optional),
        "fix_quality": int (optional),
        "raw_nmea": string (optional)
    }
    """
    try:
        payload = request.get_json(force=True, silent=False)
        
        # Validate required fields
        if "latitude" not in payload or "longitude" not in payload:
            return jsonify({"ok": False, "error": "latitude and longitude are required"}), 400
        
        # Create GPS data record
        gps_record = GPSData(
            latitude=float(payload["latitude"]),
            longitude=float(payload["longitude"]),
            altitude=float(payload.get("altitude", 0.0)),
            speed=float(payload.get("speed", 0.0)),
            satellites=int(payload.get("satellites", 0)),
            fix_quality=int(payload.get("fix_quality", 0)),
            raw_nmea=payload.get("raw_nmea", "")
        )
        
        db.session.add(gps_record)
        db.session.commit()
        
        return jsonify({
            "ok": True,
            "id": gps_record.id,
            "message": "GPS data stored successfully"
        }), 200
        
    except ValueError as e:
        logger.error(f"ValueError in api_gps: {e}")
        return jsonify({"ok": False, "error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in api_gps: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/gps/latest")
def api_gps_latest():
    """
    Return latest GPS data for frontend.
    Returns:
    {
        "total_records": int,
        "latest": {...},
        "records": [...]
    }
    """
    try:
        # Get last 100 GPS records, newest first
        rows = (
            GPSData.query
            .order_by(GPSData.timestamp.desc())
            .limit(100)
            .all()
        )
        
        records = [r.as_dict() for r in reversed(rows)]
        latest = records[-1] if records else None
        
        return jsonify({
            "total_records": len(records),
            "latest": latest,
            "records": records,
        }), 200
        
    except Exception as e:
        logger.error(f"Error in api_gps_latest: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "total_records": 0,
            "latest": None,
            "records": []
        }), 500


@app.route("/api/gps/current")
def api_gps_current():
    """
    Return only the most recent GPS fix.
    """
    try:
        latest = (
            GPSData.query
            .order_by(GPSData.timestamp.desc())
            .first()
        )
        
        if latest:
            return jsonify({
                "ok": True,
                "data": latest.as_dict()
            }), 200
        else:
            return jsonify({
                "ok": False,
                "error": "No GPS data available"
            }), 404
        
    except Exception as e:
        logger.error(f"Error in api_gps_current: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
