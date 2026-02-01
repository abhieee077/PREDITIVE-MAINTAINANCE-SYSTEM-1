"""
Time-to-Failure (TTF) Forecaster
Uses Facebook Prophet to predict when machine health will reach critical threshold
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List


class TTFForecaster:
    """Forecasts time until critical failure threshold"""
    
    def __init__(self):
        self.prophet = None
        self.health_history = {}  # machine_id -> list of (timestamp, health_score)
        self.critical_threshold = 30  # Health score below which is critical
        self._initialize_prophet()
    
    def _initialize_prophet(self):
        """Lazy import and initialize Prophet"""
        try:
            from prophet import Prophet
            self.prophet = Prophet
            print("✓ Prophet forecaster initialized")
        except ImportError:
            print("✗ Prophet not installed, using linear fallback")
            self.prophet = None
    
    def add_health_reading(self, machine_id: str, health_score: float):
        """Add health score data point for forecasting"""
        if machine_id not in self.health_history:
            self.health_history[machine_id] = []
        
        timestamp = datetime.now()
        self.health_history[machine_id].append({
            "timestamp": timestamp,
            "health_score": health_score
        })
        
        # Keep only last 100 readings per machine
        if len(self.health_history[machine_id]) > 100:
            self.health_history[machine_id].pop(0)
    
    def forecast_ttf(self, machine_id: str, horizon_hours: int = 48) -> Dict:
        """
        Forecast time to failure
        Returns: dict with forecast timeline and estimated TTF
        """
        if machine_id not in self.health_history or len(self.health_history[machine_id]) < 10:
            return {
                "status": "insufficient_data",
                "ttf_hours": None,
                "forecast": []
            }
        
        history = self.health_history[machine_id]
        
        # Use Prophet if available, otherwise linear regression
        if self.prophet is not None:
            return self._prophet_forecast(history, horizon_hours)
        else:
            return self._linear_forecast(history, horizon_hours)
    
    def _prophet_forecast(self, history: List[Dict], horizon_hours: int) -> Dict:
        """Forecast using Facebook Prophet"""
        try:
            # Prepare data for Prophet
            df = pd.DataFrame([
                {
                    "ds": record["timestamp"],
                    "y": record["health_score"]
                }
                for record in history
            ])
            
            # Create and fit model
            model = self.prophet(
                daily_seasonality=False,
                weekly_seasonality=False,
                yearly_seasonality=False
            )
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=horizon_hours, freq='H')
            forecast = model.predict(future)
            
            # Extract predictions
            predictions = []
            ttf_hours = None
            
            for _, row in forecast.iterrows():
                pred_time = row['ds']
                pred_health = max(0, min(100, row['yhat']))
                
                predictions.append({
                    "timestamp": pred_time.isoformat(),
                    "health_score": round(pred_health, 2),
                    "lower_bound": round(max(0, row['yhat_lower']), 2),
                    "upper_bound": round(min(100, row['yhat_upper']), 2)
                })
                
                # Find when it crosses critical threshold
                if ttf_hours is None and pred_health < self.critical_threshold:
                    ttf_hours = (pred_time - datetime.now()).total_seconds() / 3600
            
            return {
                "status": "success",
                "method": "prophet",
                "ttf_hours": round(ttf_hours, 1) if ttf_hours else None,
                "forecast": predictions[-horizon_hours:]  # Return only future predictions
            }
        
        except Exception as e:
            print(f"Prophet forecast error: {e}")
            return self._linear_forecast(history, horizon_hours)
    
    def _linear_forecast(self, history: List[Dict], horizon_hours: int) -> Dict:
        """Fallback: Linear regression forecast"""
        # Calculate degradation rate
        health_values = [r["health_score"] for r in history]
        current_health = health_values[-1]
        
        # Simple linear trend
        if len(health_values) >= 2:
            recent_values = health_values[-10:]  # Last 10 readings
            degradation_rate = (recent_values[-1] - recent_values[0]) / len(recent_values)
        else:
            degradation_rate = -0.5  # Default assumption
        
        # Project forward
        predictions = []
        ttf_hours = None
        
        for hour in range(horizon_hours):
            future_health = current_health + (degradation_rate * hour)
            future_health = max(0, min(100, future_health))
            
            future_time = datetime.now() + timedelta(hours=hour)
            predictions.append({
                "timestamp": future_time.isoformat(),
                "health_score": round(future_health, 2),
                "lower_bound": round(max(0, future_health - 10), 2),
                "upper_bound": round(min(100, future_health + 10), 2)
            })
            
            if ttf_hours is None and future_health < self.critical_threshold:
                ttf_hours = hour
        
        return {
            "status": "success",
            "method": "linear",
            "ttf_hours": round(ttf_hours, 1) if ttf_hours else None,
            "forecast": predictions
        }


# Global forecaster instance
forecasters = {}


def get_forecaster(machine_id: str) -> TTFForecaster:
    """Get or create forecaster for a machine"""
    if machine_id not in forecasters:
        forecasters[machine_id] = TTFForecaster()
    return forecasters[machine_id]


if __name__ == "__main__":
    # Test the forecaster
    print("Testing TTF Forecaster...")
    forecaster = TTFForecaster()
    
    # Simulate degrading health over time
    print("Simulating degrading machine health...")
    for i in range(30):
        health = 95 - (i * 1.5)  # Degrades 1.5% per reading
        forecaster.add_health_reading("M-001", health)
    
    # Forecast
    result = forecaster.forecast_ttf("M-001", horizon_hours=48)
    print(f"\nForecast Status: {result['status']}")
    print(f"Method: {result.get('method', 'N/A')}")
    print(f"Estimated Time to Failure: {result['ttf_hours']} hours")
    print(f"Forecast points: {len(result['forecast'])}")
    
    if result['forecast']:
        print("\nFirst 5 predictions:")
        for pred in result['forecast'][:5]:
            print(f"  {pred['timestamp']}: Health={pred['health_score']}% "
                  f"({pred['lower_bound']}-{pred['upper_bound']})")
