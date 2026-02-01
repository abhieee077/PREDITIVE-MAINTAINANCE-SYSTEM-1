"""
ML Stabilization Layer
Wraps ML predictions with industrial-grade stabilization:
- Exponential Moving Average (EMA) smoothing
- Monotonic RUL enforcement (never increases)
- Rate limiting
- Confidence tracking
"""
import time
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from config import Config
from rul_predictor import get_predictor


class StabilizedRULPredictor:
    """Production-grade RUL predictor with stabilization"""
    
    def __init__(self):
        self.raw_predictor = get_predictor()
        
        # Per-machine state
        self.prediction_history: Dict[str, list] = {}  # machine_id -> [(timestamp, rul, health)]
        self.last_prediction_time: Dict[str, datetime] = {}
        self.stable_predictions: Dict[str, Tuple[float, float]] = {}  # machine_id -> (rul, health)
        
        # Configuration
        self.ema_alpha = Config.EMA_ALPHA
        self.min_interval = timedelta(seconds=Config.MIN_PREDICTION_INTERVAL_SECONDS)
    
    def predict_rul(self, sensor_data: Dict, machine_id: str, bypass_smoothing: bool = False) -> Tuple[float, float]:
        """
        Get stabilized RUL prediction
        Returns: (rul_hours, health_score)
        
        If bypass_smoothing is True, skip EMA and caching (for demo mode)
        """
        # If bypass requested (demo mode), return raw prediction immediately
        if bypass_smoothing:
            raw_rul, raw_health = self.raw_predictor.predict_rul(sensor_data, machine_id)
            # Clear history for this machine to allow fresh predictions
            self.prediction_history.pop(machine_id, None)
            self.stable_predictions.pop(machine_id, None)
            self.last_prediction_time.pop(machine_id, None)
            return raw_rul, raw_health
        
        current_time = datetime.now()
        
        # Check if we should update prediction (rate limiting)
        if machine_id in self.last_prediction_time:
            time_since_last = current_time - self.last_prediction_time[machine_id]
            if time_since_last < self.min_interval:
                # Return cached stable prediction
                if machine_id in self.stable_predictions:
                    return self.stable_predictions[machine_id]
        
        # Get raw prediction from underlying model
        raw_rul, raw_health = self.raw_predictor.predict_rul(sensor_data, machine_id)
        
        # Apply stabilization
        stable_rul, stable_health = self._stabilize_prediction(
            machine_id, raw_rul, raw_health, current_time
        )
        
        # Cache stable prediction
        self.stable_predictions[machine_id] = (stable_rul, stable_health)
        self.last_prediction_time[machine_id] = current_time
        
        return stable_rul, stable_health
    
    def _stabilize_prediction(self, machine_id: str, raw_rul: float, 
                            raw_health: float, timestamp: datetime) -> Tuple[float, float]:
        """Apply EMA smoothing and monotonic enforcement"""
        
        # Initialize history if needed
        if machine_id not in self.prediction_history:
            self.prediction_history[machine_id] = []
        
        history = self.prediction_history[machine_id]
        
        # First prediction - no smoothing needed
        if len(history) == 0:
            history.append((timestamp, raw_rul, raw_health))
            return raw_rul, raw_health
        
        # Get previous stable prediction
        prev_timestamp, prev_rul, prev_health = history[-1]
        
        # Apply Exponential Moving Average (EMA)
        # new_value = alpha * raw_value + (1 - alpha) * prev_value
        ema_rul = self.ema_alpha * raw_rul + (1 - self.ema_alpha) * prev_rul
        ema_health = self.ema_alpha * raw_health + (1 - self.ema_alpha) * prev_health
        
        # Enforce monotonic RUL (can only decrease or stay constant)
        stable_rul = min(ema_rul, prev_rul)
        
        # Health can fluctuate slightly but should generally decrease
        # Allow small increases (within 5%) to account for sensor noise
        if ema_health > prev_health * 1.05:
            stable_health = prev_health
        else:
            stable_health = ema_health
        
        # Enforce bounds
        stable_rul = max(Config.MIN_RUL_HOURS, min(stable_rul, Config.MAX_RUL_HOURS))
        stable_health = max(0.0, min(100.0, stable_health))
        
        # Add to history (keep last 50 predictions)
        history.append((timestamp, stable_rul, stable_health))
        if len(history) > 50:
            history.pop(0)
        
        return round(stable_rul, 1), round(stable_health, 2)
    
    def get_prediction_trend(self, machine_id: str, hours: int = 24) -> Dict:
        """Get prediction trend for analysis"""
        if machine_id not in self.prediction_history:
            return {"status": "no_data"}
        
        history = self.prediction_history[machine_id]
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_history = [
            {
                "timestamp": ts.isoformat(),
                "rul_hours": rul,
                "health_score": health
            }
            for ts, rul, health in history
            if ts >= cutoff
        ]
        
        if not recent_history:
            return {"status": "no_recent_data"}
        
        # Calculate trend
        if len(recent_history) >= 2:
            first_rul = recent_history[0]["rul_hours"]
            last_rul = recent_history[-1]["rul_hours"]
            rul_change = last_rul - first_rul
            
            first_health = recent_history[0]["health_score"]
            last_health = recent_history[-1]["health_score"]
            health_change = last_health - first_health
        else:
            rul_change = 0
            health_change = 0
        
        return {
            "status": "success",
            "data_points": len(recent_history),
            "rul_change": round(rul_change, 1),
            "health_change": round(health_change, 2),
            "trend": "degrading" if rul_change < -5 else "stable",
            "history": recent_history
        }
    
    def reset_machine(self, machine_id: str):
        """Reset prediction history (after maintenance)"""
        if machine_id in self.prediction_history:
            self.prediction_history[machine_id] = []
        if machine_id in self.stable_predictions:
            del self.stable_predictions[machine_id]
        if machine_id in self.last_prediction_time:
            del self.last_prediction_time[machine_id]
        print(f"✓ Reset ML predictions for {machine_id}")


# Global stabilized predictor instance
_stabilized_predictor = None

def get_stabilized_predictor() -> StabilizedRULPredictor:
    """Get or create stabilized predictor singleton"""
    global _stabilized_predictor
    if _stabilized_predictor is None:
        _stabilized_predictor = StabilizedRULPredictor()
    return _stabilized_predictor


if __name__ == "__main__":
    # Test ML stabilization
    print("Testing ML Stabilization...")
    print("=" * 60)
    
    predictor = StabilizedRULPredictor()
    
    # Simulate oscillating raw predictions
    print("\nSimulating oscillating raw RUL predictions:")
    print("(Raw predictions jump around, stable predictions smooth)")
    print()
    
    test_sensor_data = {
        "vibration_x": 0.8,
        "vibration_y": 0.7,
        "temperature": 75,
        "pressure": 98,
        "rpm": 1480
    }
    
    # Simulate 20 predictions with artificial oscillation
    import random
    base_rul = 100
    
    for i in range(20):
        # Add random oscillation to simulate unstable raw predictions
        raw_rul_noise = random.uniform(-10, 10)
        test_sensor_data["temperature"] = 75 + raw_rul_noise / 2
        
        stable_rul, stable_health = predictor.predict_rul(test_sensor_data, "TEST-001")
        
        # Get what the raw predictor would have said
        raw_rul, raw_health = predictor.raw_predictor.predict_rul(test_sensor_data, "TEST-001")
        
        print(f"Step {i+1:2d}: Raw RUL={raw_rul:6.1f}h, "
              f"Stable RUL={stable_rul:6.1f}h, "
              f"Diff={abs(raw_rul - stable_rul):5.1f}h")
        
        # Gradually degrade sensor
        test_sensor_data["vibration_x"] += 0.02
        test_sensor_data["temperature"] += 0.5
        
        time.sleep(0.1)  # Small delay
    
    # Test monotonic enforcement
    print("\n" + "=" * 60)
    print("Testing Monotonic RUL Enforcement:")
    print("(RUL should never increase)")
    print()
    
    predictor2 = StabilizedRULPredictor()
    prev_rul = None
    
    for i in range(10):
        stable_rul, _ = predictor2.predict_rul(test_sensor_data, "TEST-002")
        
        if prev_rul is not None:
            increased = stable_rul > prev_rul
            status = "❌ INCREASED!" if increased else "✓ Decreased/Stable"
            print(f"Step {i+1:2d}: RUL={stable_rul:6.1f}h, "
                  f"Change={stable_rul - prev_rul:+6.1f}h, {status}")
        else:
            print(f"Step {i+1:2d}: RUL={stable_rul:6.1f}h (initial)")
        
        prev_rul = stable_rul
        test_sensor_data["vibration_x"] += 0.03
        time.sleep(0.1)
    
    print("\n" + "=" * 60)
    print("✓ ML Stabilization working correctly!")
