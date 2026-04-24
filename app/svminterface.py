from .svmmodel import predict as ml_predict
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)

class _FakeDB:
    def session(self): pass

db = _FakeDB()

class Prediction:
    pass


def call_predict(payload):
    """Interface between routes and the model / deep-learning script."""
    try:
        if not payload:
            return {"error": "Empty payload"}

        # OPTION 1: RAW DISTANCE SERIES
        # BUG-10 fix: the SVM path is disabled. Log a warning instead of silently
        # routing into ml_predict() which always returns {"error": "SVM disabled"}.
        if "distance_series" in payload:
            logger.warning(
                "BUG-10: distance_series payload received but SVM is disabled. "
                "Route this payload to the TCNInferenceEngine via /api/predict "
                "with a distance_series key instead."
            )
            return {"error": "SVM disabled — use /api/predict with distance_series for TCN inference", "ok": False}


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

        logger.info(json.dumps(result))

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
