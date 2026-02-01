"""
Remaining Useful Life (RUL) Predictor
Uses XGBoost model trained on NASA bearing dataset to predict time until failure
"""
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple


class RULPredictor:
    """Predicts Remaining Useful Life for industrial equipment"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_columns = [
            'engine_no', 'op_setting_1', 'op_setting_2', 'op_setting_3',
            'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5',
            'sensor_6', 'sensor_7', 'sensor_8', 'sensor_9', 'sensor_10',
            'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14', 'sensor_15',
            'sensor_16', 'sensor_17', 'sensor_18', 'sensor_19', 'sensor_20',
            'sensor_21'
        ]
        
        if model_path is None:
            model_path = Path(__file__).parent / "models" / "xgb.pkl"
        
        self.load_model(model_path)
    
    def load_model(self, model_path):
        """Load pre-trained XGBoost model"""
        try:
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            print(f"✓ RUL model loaded from {model_path}")
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            self.model = None
    
    def _map_sensors_to_features(self, sensor_data: Dict, machine_id: str) -> pd.DataFrame:
        """
        Map real sensor data to NASA dataset features
        This is an approximation since our simulated sensors differ from NASA features
        """
        # Extract sensor values
        vib_x = sensor_data.get("vibration_x", 0.5)
        vib_y = sensor_data.get("vibration_y", 0.5)
        temp = sensor_data.get("temperature", 70)
        pressure = sensor_data.get("pressure", 100)
        rpm = sensor_data.get("rpm", 1500)
        
        # Create synthetic feature mapping
        # In a real system, these would be actual sensor readings
        engine_no = int(machine_id.split("-")[1]) if "-" in machine_id else 1
        
        features = {
            'engine_no': engine_no,
            'op_setting_1': rpm / 1500,  # Normalized RPM
            'op_setting_2': pressure / 100,  # Normalized pressure
            'op_setting_3': temp / 70,  # Normalized temp
            'sensor_1': vib_x,
            'sensor_2': vib_y,
            'sensor_3': temp / 50,
            'sensor_4': pressure / 80,
            'sensor_5': vib_x * 1.1,
            'sensor_6': vib_y * 1.1,
            'sensor_7': temp / 100,
            'sensor_8': pressure / 120,
            'sensor_9': rpm / 2000,
            'sensor_10': vib_x * vib_y,
            'sensor_11': temp / 90,
            'sensor_12': pressure / 110,
            'sensor_13': vib_x * 1.2,
            'sensor_14': vib_y * 1.2,
            'sensor_15': temp / 85,
            'sensor_16': pressure / 95,
            'sensor_17': rpm / 1800,
            'sensor_18': vib_x * 0.9,
            'sensor_19': vib_y * 0.9,
            'sensor_20': temp / 75,
            'sensor_21': pressure / 105
        }
        
        return pd.DataFrame([features], columns=self.feature_columns)
    
    def predict_rul(self, sensor_data: Dict, machine_id: str) -> Tuple[float, float]:
        """
        Predict Remaining Useful Life
        Returns: (rul_hours, health_score_percentage)
        """
        # Use heuristic method directly for now (XGBoost model has compatibility issues)
        # In production, retrain model with current XGBoost version
        return self._heuristic_rul(sensor_data)
    
    def _heuristic_rul(self, sensor_data: Dict) -> Tuple[float, float]:
        """
        Equipment-agnostic health heuristic for thermal power plant.
        OPTIMIZED: Thresholds synchronized with config.py warning/critical values
        """
        vib_x = sensor_data.get("vibration_x", 0.5)
        vib_y = sensor_data.get("vibration_y", 0.5)
        temp = sensor_data.get("temperature", 70)
        pressure = sensor_data.get("pressure", 100)
        
        # Vibration score: Calibrated to config.py thresholds
        # Baseline: 0.35-0.60 (healthy), Warning: 1.2-1.5, Critical: 2.5-3.0
        avg_vib = (vib_x + vib_y) / 2
        if avg_vib <= 0.65:  # Healthy baseline range
            vib_score = 100
        elif avg_vib <= 1.2:  # Approaching warning (EARLY DETECTION)
            vib_score = 100 - ((avg_vib - 0.65) / 0.55) * 20  # Linear drop to 80
        elif avg_vib <= 2.5:  # Warning to critical range
            vib_score = 80 - ((avg_vib - 1.2) / 1.3) * 50  # Drop to 30
        else:  # Critical and beyond
            vib_score = max(0, 30 - ((avg_vib - 2.5) / 1.0) * 30)  # Drop to 0
        
        # Temperature score: context-aware per equipment type
        # HVAC chiller: baseline ~7.5°C, warning >10°C, critical >15°C
        # Motors: baseline ~72-82°C, warning >85°C, critical >95°C
        # Pumps: baseline ~52°C, warning >70°C, critical >85°C
        if temp < 20:  # Likely HVAC/chiller
            if temp <= 7.5:
                temp_score = 100
            elif temp <= 10.0:  # Warning zone
                temp_score = 100 - ((temp - 7.5) / 2.5) * 30
            elif temp <= 15.0:  # Critical zone
                temp_score = 70 - ((temp - 10.0) / 5.0) * 50
            else:
                temp_score = max(0, 20 - ((temp - 15.0) / 5.0) * 20)
        elif temp > 60:  # Likely motor
            if temp <= 72:
                temp_score = 100
            elif temp <= 85:  # Warning zone
                temp_score = 100 - ((temp - 72) / 13) * 25
            elif temp <= 95:  # Critical zone
                temp_score = 75 - ((temp - 85) / 10) * 45
            else:
                temp_score = max(0, 30 - ((temp - 95) / 10) * 30)
        else:  # Pump range
            if temp <= 52:
                temp_score = 100
            elif temp <= 70:  # Warning zone
                temp_score = 100 - ((temp - 52) / 18) * 25
            elif temp <= 85:  # Critical zone
                temp_score = 75 - ((temp - 70) / 15) * 45
            else:
                temp_score = max(0, 30 - ((temp - 85) / 15) * 30)
        
        # Combined health score (vibration weighted more heavily for industrial equipment)
        health_score = (vib_score * 0.6) + (temp_score * 0.4)
        health_score = min(100, max(0, health_score))  # Clamp to 0-100
        
        # RUL based on health (non-linear for better lead time prediction)
        # Health 100-70: RUL 144-72h (HEALTHY)
        # Health 70-40: RUL 72-24h (DEGRADING - WARNING)
        # Health 40-0: RUL 24-0h (PRE_FAILURE/FAILURE - CRITICAL)
        if health_score >= 70:
            rul_hours = 72 + ((health_score - 70) / 30) * 72  # 72-144h
        elif health_score >= 40:
            rul_hours = 24 + ((health_score - 40) / 30) * 48  # 24-72h
        else:
            rul_hours = (health_score / 40) * 24  # 0-24h
        
        return round(rul_hours, 1), round(health_score, 2)
    
    def get_failure_probability(self, rul_hours: float) -> str:
        """Classify failure risk based on RUL"""
        if rul_hours > 72:
            return "low"
        elif rul_hours > 24:
            return "medium"
        else:
            return "high"


# Global predictor instance
predictor = None


def get_predictor() -> RULPredictor:
    """Get or create RUL predictor singleton"""
    global predictor
    if predictor is None:
        predictor = RULPredictor()
    return predictor


if __name__ == "__main__":
    # Test the predictor
    print("Testing RUL Predictor...")
    pred = RULPredictor()
    
    # Test with healthy sensor data
    healthy_data = {
        "vibration_x": 0.5,
        "vibration_y": 0.5,
        "temperature": 70,
        "pressure": 100,
        "rpm": 1500
    }
    rul, health = pred.predict_rul(healthy_data, "M-001")
    print(f"Healthy Machine: RUL={rul}h, Health={health}%, Risk={pred.get_failure_probability(rul)}")
    
    # Test with degraded sensor data
    degraded_data = {
        "vibration_x": 1.2,
        "vibration_y": 1.1,
        "temperature": 85,
        "pressure": 95,
        "rpm": 1400
    }
    rul, health = pred.predict_rul(degraded_data, "M-002")
    print(f"Degraded Machine: RUL={rul}h, Health={health}%, Risk={pred.get_failure_probability(rul)}")
    
    # Test with critical sensor data
    critical_data = {
        "vibration_x": 1.8,
        "vibration_y": 1.7,
        "temperature": 95,
        "pressure": 90,
        "rpm": 1300
    }
    rul, health = pred.predict_rul(critical_data, "M-003")
    print(f"Critical Machine: RUL={rul}h, Health={health}%, Risk={pred.get_failure_probability(rul)}")
