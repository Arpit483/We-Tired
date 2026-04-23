from .svmmodel import predict as ml_predict
from .models import db, Prediction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def call_predict(payload):
    """Interface between routes and the model / deep-learning script."""
    try:
        if not payload:
            return {"error": "Empty payload"}

        # OPTION 1: RAW DISTANCE SERIES (if ever used from ld2410_runner.py)
        if "distance_series" in payload:
            result = ml_predict(payload)
            if "error" in result:
                return result

        # OPTION 2: DEEP-LEARNING OUTPUT PROVIDED DIRECTLY
        elif any(k in payload for k in ("breathing", "freq", "power")):
            # Data coming directly from deep-learning script
            result = {
                "breathing": bool(payload.get("breathing", False)),
                "freq": float(payload.get("freq", 0.0)),
                "power": float(payload.get("power", 0.0)),
                "entropy": float(payload.get("entropy", 0.0)),
                "distance": float(payload.get("distance", 0.0)),
                "fft_conf": float(payload.get("fft_conf", 0.0)),
                "dl_conf": float(payload.get("dl_conf", 0.0)),
                "votes": int(payload.get("votes", 0)),
                "voting_window": int(payload.get("voting_window", 0)),
                "ok": True,
            }

        else:
            return {"error": "No valid data in payload"}

        # DO NOT override result["breathing"] here.
        # It must remain whatever the deep-learning script decided.

        # Map deep-learning votes to 0?100 for UI
        votes = calculate_votes(result)
        result["votes"] = votes

        # Save to database
        try:
            pred = Prediction(
                breathing=result.get("breathing", False),
                freq=result.get("freq", 0.0),
                power=result.get("power", 0.0),
                entropy=result.get("entropy", 0.0),
                distance=result.get("distance", 0.0),
                votes=votes,
                fft_conf=result.get("fft_conf", 0.0),  # FFT confidence
                dl_conf=result.get("dl_conf", 0.0),  # Deep learning confidence
                
                # Dual sensor data
                status=payload.get("status", "not_detected"),
                direction=payload.get("direction", "none"),
                left_detected=payload.get("left_detected", False),
                left_distance=payload.get("left_distance", 0.0),
                left_confidence=payload.get("left_confidence", 0.0),
                left_votes=payload.get("left_votes", 0),
                left_freq=payload.get("left_freq", 0.0),
                left_power=payload.get("left_power", 0.0),
                right_detected=payload.get("right_detected", False),
                right_distance=payload.get("right_distance", 0.0),
                right_confidence=payload.get("right_confidence", 0.0),
                right_votes=payload.get("right_votes", 0),
                right_freq=payload.get("right_freq", 0.0),
                right_power=payload.get("right_power", 0.0),
                
                timestamp=datetime.utcnow(),
            )

            db.session.add(pred)
            db.session.commit()
        except Exception as db_error:
            logger.error(f"Database error in call_predict: {db_error}")
            db.session.rollback()
            # Still return the result even if database save fails
            result["db_error"] = str(db_error)
            return result

        return result

    except Exception as e:
        logger.error(f"Error in call_predict: {e}")
        return {"error": str(e)}


def calculate_votes(svm_output):
    """
    Use deep-learning votes if provided. Do NOT change breathing.
    """
    raw_votes = svm_output.get("votes")
    win = svm_output.get("voting_window", 0)

    if raw_votes is not None and win:
        ratio = max(0.0, min(1.0, float(raw_votes) / float(win)))
        return int(ratio * 100)

    # Fallback if no votes were sent
    return 100 if svm_output.get("breathing", False) else 0
