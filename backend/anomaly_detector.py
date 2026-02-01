"""
Anomaly Detection Module
Uses PyOD's IsolationForest and statistical methods to detect sensor anomalies
"""
import numpy as np
from typing import Dict, List, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """Detects anomalies in sensor data streams using Isolation Forest"""
    
    def __init__(self, contamination=0.05):
        # Use native Sklearn IsolationForest instead of PyOD (which was crashing)
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.sensor_history = []
        self.min_samples = 20
        
    def _extract_features(self, sensor_data: Dict) -> np.ndarray:
        """Extract numeric features from sensor dict"""
        return np.array([
            sensor_data.get("vibration_x", 0),
            sensor_data.get("vibration_y", 0),
            sensor_data.get("temperature", 0),
            sensor_data.get("pressure", 0),
            sensor_data.get("rpm", 0)
        ])
    
    def add_sample(self, sensor_data: Dict):
        """Add sensor reading to history for training"""
        features = self._extract_features(sensor_data)
        self.sensor_history.append(features)
        
        # Keep only last 200 samples
        if len(self.sensor_history) > 200:
            self.sensor_history.pop(0)
        
        # Refit model if we have enough samples
        if len(self.sensor_history) >= self.min_samples:
            self._fit_model()
    
    def _fit_model(self):
        """Fit the anomaly detection model on historical data"""
        X = np.array(self.sensor_history)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
    
    def detect_anomaly(self, sensor_data: Dict) -> Tuple[bool, float, Dict]:
        """
        Detect if sensor reading is anomalous
        Returns: (is_anomaly, anomaly_score, details)
        """
        features = self._extract_features(sensor_data)
        
        # Add to history
        self.add_sample(sensor_data)
        
        # Use statistical method if model not fitted yet
        if not self.is_fitted:
            return self._detect_statistical(sensor_data, features)
        
        # ML-based detection
        X = features.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get anomaly score 
        # Sklearn: Lower = More Anomalous (negative values)
        # We invert it so Higher = More Anomalous
        raw_score = self.model.decision_function(X_scaled)[0]
        anomaly_score = -raw_score
        
        # Sklearn predict: -1 is anomaly, 1 is normal
        prediction = self.model.predict(X_scaled)[0]
        is_anomaly = bool(prediction == -1)
        
        details = {
            "method": "IsolationForest",
            "score": float(anomaly_score),
            "threshold": "auto"
        }
        
        return is_anomaly, float(anomaly_score), details
    
    def _detect_statistical(self, sensor_data: Dict, features: np.ndarray) -> Tuple[bool, float, Dict]:
        """Fallback: Simple z-score based anomaly detection"""
        if len(self.sensor_history) < 10:
            # Not enough data yet
            return False, 0.0, {"method": "insufficient_data"}
        
        X = np.array(self.sensor_history)
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0) + 1e-6  # Avoid division by zero
        
        # Calculate z-scores
        z_scores = np.abs((features - mean) / std)
        max_z = np.max(z_scores)
        
        # Anomaly if any sensor exceeds 3.5 sigma (OPTIMIZED: raised from 3.0 for fewer false alarms)
        is_anomaly = bool(max_z > 3.5)  # Convert numpy bool to Python bool
        
        details = {
            "method": "z_score",
            "max_z_score": float(max_z),
            "threshold": 3.0,
            "sensor_z_scores": {
                "vibration_x": float(z_scores[0]),
                "vibration_y": float(z_scores[1]),
                "temperature": float(z_scores[2]),
                "pressure": float(z_scores[3]),
                "rpm": float(z_scores[4])
            }
        }
        
        return is_anomaly, float(max_z), details
    
    def get_health_score(self, sensor_data: Dict) -> float:
        """Calculate health score (0-100) based on anomaly probability"""
        is_anomaly, score, details = self.detect_anomaly(sensor_data)
        
        # Convert anomaly score to health score
        # Lower anomaly score = higher health
        if details["method"] == "z_score":
            # Z-score based: 0-3 is healthy, >3 is unhealthy
            health = max(0, min(100, 100 - (score / 3.0) * 100))
        else:
            # IForest based: normalize score
            health = max(0, min(100, 100 - abs(score) * 10))
        
        return round(health, 2)


# Global detector instances for each machine
detectors = {}


def get_detector(machine_id: str) -> AnomalyDetector:
    """Get or create anomaly detector for a machine"""
    if machine_id not in detectors:
        detectors[machine_id] = AnomalyDetector()
    return detectors[machine_id]


if __name__ == "__main__":
    # Test the detector
    print("Testing Anomaly Detector...")
    detector = AnomalyDetector()
    
    # Simulate normal readings
    for i in range(50):
        normal_data = {
            "vibration_x": 0.5 + np.random.normal(0, 0.05),
            "vibration_y": 0.5 + np.random.normal(0, 0.05),
            "temperature": 70 + np.random.normal(0, 2),
            "pressure": 100 + np.random.normal(0, 5),
            "rpm": 1500 + np.random.normal(0, 50)
        }
        is_anom, score, details = detector.detect_anomaly(normal_data)
        print(f"Sample {i+1}: Anomaly={is_anom}, Score={score:.3f}, Health={detector.get_health_score(normal_data)}%")
    
    # Inject anomaly
    print("\n--- Injecting Anomaly ---")
    anomaly_data = {
        "vibration_x": 2.5,  # Spike!
        "vibration_y": 2.3,  # Spike!
        "temperature": 95,
        "pressure": 100,
        "rpm": 1500
    }
    is_anom, score, details = detector.detect_anomaly(anomaly_data)
    print(f"Anomaly Detection: {is_anom}, Score: {score:.3f}, Health: {detector.get_health_score(anomaly_data)}%")
    print(f"Details: {details}")
