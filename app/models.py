from . import db
from datetime import datetime


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )
    breathing = db.Column(db.Boolean, default=False)
    freq = db.Column(db.Float, default=0.0)
    power = db.Column(db.Float, default=0.0)
    entropy = db.Column(db.Float, default=0.0)
    distance = db.Column(db.Float, default=0.0)
    votes = db.Column(db.Integer, default=0)
    fft_conf = db.Column(db.Float, default=0.0)  # FFT confidence score
    dl_conf = db.Column(db.Float, default=0.0)  # Deep learning confidence score
    latitude = db.Column(db.Float, default=None, nullable=True)  # GPS latitude
    longitude = db.Column(db.Float, default=None, nullable=True)  # GPS longitude
    
    # Dual sensor fields
    status = db.Column(db.String(20), default="not_detected")  # detected, not_detected, high_chance
    direction = db.Column(db.String(20), default="none")  # center, move_left, move_right, none
    left_detected = db.Column(db.Boolean, default=False)
    left_distance = db.Column(db.Float, default=0.0)
    left_confidence = db.Column(db.Float, default=0.0)
    left_votes = db.Column(db.Integer, default=0)
    left_freq = db.Column(db.Float, default=0.0)
    left_power = db.Column(db.Float, default=0.0)
    right_detected = db.Column(db.Boolean, default=False)
    right_distance = db.Column(db.Float, default=0.0)
    right_confidence = db.Column(db.Float, default=0.0)
    right_votes = db.Column(db.Integer, default=0)
    right_freq = db.Column(db.Float, default=0.0)
    right_power = db.Column(db.Float, default=0.0)
    
    raw_json = db.Column(db.Text)

    def as_dict(self):
        result = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "breathing": self.breathing,
            "freq": round(self.freq, 3),
            "power": round(self.power, 2),
            "entropy": round(self.entropy, 3),
            "distance": round(self.distance, 2),
            "votes": self.votes,
            "fft_conf": round(self.fft_conf, 3) if self.fft_conf else 0.0,
            "dl_conf": round(self.dl_conf, 3) if self.dl_conf else 0.0,
            
            # Dual sensor data
            "status": self.status or "not_detected",
            "direction": self.direction or "none",
            "left_detected": self.left_detected,
            "left_distance": round(self.left_distance, 2) if self.left_distance else 0.0,
            "left_confidence": round(self.left_confidence, 3) if self.left_confidence else 0.0,
            "left_votes": self.left_votes or 0,
            "left_freq": round(self.left_freq, 3) if self.left_freq else 0.0,
            "left_power": round(self.left_power, 2) if self.left_power else 0.0,
            "right_detected": self.right_detected,
            "right_distance": round(self.right_distance, 2) if self.right_distance else 0.0,
            "right_confidence": round(self.right_confidence, 3) if self.right_confidence else 0.0,
            "right_votes": self.right_votes or 0,
            "right_freq": round(self.right_freq, 3) if self.right_freq else 0.0,
            "right_power": round(self.right_power, 2) if self.right_power else 0.0,
            
            # Legacy compatibility
            "sensor1_detected": self.left_detected,
            "sensor1_distance": round(self.left_distance, 2) if self.left_distance else 0.0,
            "sensor1_confidence": round(self.left_confidence, 3) if self.left_confidence else 0.0,
            "sensor1_votes": self.left_votes or 0,
            "sensor2_detected": self.right_detected,
            "sensor2_distance": round(self.right_distance, 2) if self.right_distance else 0.0,
            "sensor2_confidence": round(self.right_confidence, 3) if self.right_confidence else 0.0,
            "sensor2_votes": self.right_votes or 0,
        }
        if self.latitude is not None and self.longitude is not None:
            result["latitude"] = round(self.latitude, 6)
            result["longitude"] = round(self.longitude, 6)
        return result

    def __repr__(self):
        return f"<Prediction id={self.id} breathing={self.breathing} votes={self.votes}>"


class GPSData(db.Model):
    __tablename__ = "gps_data"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    altitude = db.Column(db.Float, default=0.0)
    speed = db.Column(db.Float, default=0.0)  # in km/h
    satellites = db.Column(db.Integer, default=0)
    fix_quality = db.Column(db.Integer, default=0)  # 0=no fix, 1=GPS fix, 2=DGPS fix
    raw_nmea = db.Column(db.Text)  # Store raw NMEA sentence

    def as_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "altitude": round(self.altitude, 2),
            "speed": round(self.speed, 2),
            "satellites": self.satellites,
            "fix_quality": self.fix_quality,
        }

    def __repr__(self):
        return f"<GPSData id={self.id} lat={self.latitude} lon={self.longitude}>"
