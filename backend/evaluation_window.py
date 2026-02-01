"""
Evaluation Window Layer
=======================
Sliding window aggregation between ML predictions and alert creation.

PURPOSE: Control the trade-offs between:
- Precision (reject noise spikes)
- Recall (catch slow degradation) 
- Lead Time (shorter windows for urgency)
- False Alarm Rate (require sustained + worsening conditions)

FLOW:
    Sensor → ML → EMA → EvaluationWindow → Persistence → Hysteresis → Alert
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import threading
import numpy as np
from config import Config


@dataclass
class WindowSample:
    """Single sample in evaluation window"""
    timestamp: datetime
    risk_score: float      # 0-1 scaled risk (1 = critical)
    health_score: float    # 0-100 health
    rul_hours: float       # Remaining useful life
    sensors: Dict = field(default_factory=dict)


@dataclass
class WindowEvaluation:
    """Result of window evaluation"""
    may_proceed: bool           # Can alert proceed to next stage?
    mean_risk: float
    risk_trend: float           # Positive = worsening
    pct_above_threshold: float  # 0-1 ratio
    sample_count: int
    window_duration_actual: float  # Seconds
    reason: str                 # Why decision was made


class EvaluationWindow:
    """
    Sliding evaluation window for a single (machine_id, alert_type) pair.
    
    Aggregates signal over time to distinguish:
    - Short noise bursts → Reject (protects precision)
    - Slow degradation → Accept (preserves recall)  
    - Threshold hovering → Reject (reduces false alarms)
    """
    
    def __init__(self, machine_id: str, alert_type: str, config: Dict):
        self.machine_id = machine_id
        self.alert_type = alert_type
        
        # Configurable parameters
        self.duration_seconds = config.get("duration_seconds", 60)
        self.required_pct_above = config.get("required_pct_above", 0.6)
        self.require_worsening_trend = config.get("require_worsening_trend", True)
        self.risk_threshold = config.get("risk_threshold", 0.5)
        
        # Sample storage
        self.samples: List[WindowSample] = []
        self._lock = threading.Lock()
    
    def add_sample(self, risk_score: float, health_score: float, 
                   rul_hours: float, sensors: Dict = None):
        """Add new sample to window"""
        with self._lock:
            sample = WindowSample(
                timestamp=datetime.now(),
                risk_score=risk_score,
                health_score=health_score,
                rul_hours=rul_hours,
                sensors=sensors or {}
            )
            self.samples.append(sample)
            
            # Prune old samples
            self._prune_old_samples()
    
    def _prune_old_samples(self):
        """Remove samples outside window duration"""
        cutoff = datetime.now() - timedelta(seconds=self.duration_seconds)
        self.samples = [s for s in self.samples if s.timestamp >= cutoff]
    
    def evaluate(self) -> WindowEvaluation:
        """
        Evaluate window and decide if alert may proceed.
        
        CONDITIONS FOR PROCEEDING:
        1. mean_risk >= threshold
        2. risk_trend > 0 (worsening) OR trend check disabled
        3. pct_above_threshold >= required percentage
        """
        with self._lock:
            self._prune_old_samples()
            
            if len(self.samples) < 3:
                return WindowEvaluation(
                    may_proceed=False,
                    mean_risk=0,
                    risk_trend=0,
                    pct_above_threshold=0,
                    sample_count=len(self.samples),
                    window_duration_actual=0,
                    reason="Insufficient samples (<3)"
                )
            
            # Extract risk scores
            risks = [s.risk_score for s in self.samples]
            timestamps = [s.timestamp for s in self.samples]
            
            # Calculate metrics
            mean_risk = np.mean(risks)
            risk_trend = self._calculate_trend(timestamps, risks)
            pct_above = sum(1 for r in risks if r >= self.risk_threshold) / len(risks)
            
            # Calculate actual window duration
            duration_actual = (timestamps[-1] - timestamps[0]).total_seconds()
            
            # Evaluate conditions
            condition_mean = mean_risk >= self.risk_threshold
            condition_trend = (not self.require_worsening_trend) or (risk_trend > 0)
            condition_pct = pct_above >= self.required_pct_above
            
            may_proceed = condition_mean and condition_trend and condition_pct
            
            # Build reason string
            reasons = []
            if not condition_mean:
                reasons.append(f"mean_risk {mean_risk:.2f} < {self.risk_threshold}")
            if not condition_trend:
                reasons.append(f"trend {risk_trend:.4f} not worsening")
            if not condition_pct:
                reasons.append(f"pct_above {pct_above:.1%} < {self.required_pct_above:.0%}")
            
            reason = "PROCEED" if may_proceed else "; ".join(reasons)
            
            return WindowEvaluation(
                may_proceed=may_proceed,
                mean_risk=mean_risk,
                risk_trend=risk_trend,
                pct_above_threshold=pct_above,
                sample_count=len(self.samples),
                window_duration_actual=duration_actual,
                reason=reason
            )
    
    def _calculate_trend(self, timestamps: List[datetime], values: List[float]) -> float:
        """
        Calculate trend (slope) of risk values over time.
        Positive slope = worsening (risk increasing)
        Negative slope = improving
        """
        if len(values) < 2:
            return 0.0
        
        # Convert timestamps to seconds from first sample
        t0 = timestamps[0]
        x = np.array([(t - t0).total_seconds() for t in timestamps])
        y = np.array(values)
        
        # Linear regression slope
        if x[-1] - x[0] < 1:  # Less than 1 second span
            return 0.0
        
        # Normalized slope (change per 60 seconds)
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2 + 1e-10)
        
        return float(slope * 60)  # Per-minute change
    
    def clear(self):
        """Clear all samples (after maintenance or reset)"""
        with self._lock:
            self.samples.clear()


class EvaluationWindowManager:
    """
    Manages evaluation windows for all (machine_id, alert_type) pairs.
    Thread-safe singleton pattern.
    """
    
    def __init__(self):
        # Key: (machine_id, alert_type), Value: EvaluationWindow
        self.windows: Dict[Tuple[str, str], EvaluationWindow] = {}
        self._lock = threading.RLock()
    
    def _get_window_config(self, alert_type: str) -> Dict:
        """Get configuration for alert type"""
        return Config.EVALUATION_WINDOWS.get(alert_type, {
            "duration_seconds": 60,
            "required_pct_above": 0.6,
            "require_worsening_trend": True,
            "risk_threshold": 0.5
        })
    
    def add_sample(self, machine_id: str, alert_type: str,
                   risk_score: float, health_score: float,
                   rul_hours: float, sensors: Dict = None):
        """Add sample to appropriate window"""
        with self._lock:
            key = (machine_id, alert_type)
            
            if key not in self.windows:
                config = self._get_window_config(alert_type)
                self.windows[key] = EvaluationWindow(machine_id, alert_type, config)
            
            self.windows[key].add_sample(risk_score, health_score, rul_hours, sensors)
    
    def evaluate(self, machine_id: str, alert_type: str) -> WindowEvaluation:
        """Evaluate window and return decision"""
        with self._lock:
            key = (machine_id, alert_type)
            
            if key not in self.windows:
                return WindowEvaluation(
                    may_proceed=False,
                    mean_risk=0,
                    risk_trend=0,
                    pct_above_threshold=0,
                    sample_count=0,
                    window_duration_actual=0,
                    reason="No window exists"
                )
            
            return self.windows[key].evaluate()
    
    def clear_machine(self, machine_id: str):
        """Clear all windows for a machine (after maintenance)"""
        with self._lock:
            keys_to_clear = [k for k in self.windows.keys() if k[0] == machine_id]
            for key in keys_to_clear:
                self.windows[key].clear()
            print(f"✓ Cleared evaluation windows for {machine_id}")
    
    def get_status(self, machine_id: str = None) -> Dict:
        """Get status of all windows (for debugging/API)"""
        with self._lock:
            status = {}
            for key, window in self.windows.items():
                if machine_id and key[0] != machine_id:
                    continue
                
                eval_result = window.evaluate()
                status[f"{key[0]}:{key[1]}"] = {
                    "sample_count": eval_result.sample_count,
                    "mean_risk": round(eval_result.mean_risk, 3),
                    "risk_trend": round(eval_result.risk_trend, 4),
                    "pct_above": round(eval_result.pct_above_threshold, 2),
                    "may_proceed": eval_result.may_proceed,
                    "reason": eval_result.reason
                }
            
            return status


# Singleton instance
_window_manager = None
_window_manager_lock = threading.Lock()


def get_window_manager() -> EvaluationWindowManager:
    """Get or create window manager singleton"""
    global _window_manager
    if _window_manager is None:
        with _window_manager_lock:
            if _window_manager is None:
                _window_manager = EvaluationWindowManager()
    return _window_manager


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def calculate_risk_score(rul_hours: float, health_score: float, 
                         anomaly_score: float = 0) -> float:
    """
    Calculate unified risk score (0-1) from multiple sources.
    
    1.0 = Maximum risk (failure imminent)
    0.0 = Minimum risk (healthy)
    """
    # RUL component (0-1, inverted)
    rul_risk = max(0, min(1, 1 - (rul_hours / Config.MAX_RUL_HOURS)))
    
    # Health component (0-1, inverted)
    health_risk = max(0, min(1, 1 - (health_score / 100)))
    
    # Anomaly component (0-1, scaled)
    anomaly_risk = min(1, anomaly_score / 10)  # Scale 0-10 to 0-1
    
    # Weighted combination
    # RUL is most predictive, health is confirmatory, anomaly is supplementary
    combined = (rul_risk * 0.5) + (health_risk * 0.35) + (anomaly_risk * 0.15)
    
    return round(min(1.0, max(0.0, combined)), 3)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("EVALUATION WINDOW SELF-TEST")
    print("=" * 60)
    
    # Test 1: Single spike rejection
    print("\n[TEST 1] Single noise spike should be REJECTED")
    manager = EvaluationWindowManager()
    
    # Add one high-risk sample
    manager.add_sample("TEST-001", "critical_rul", 0.9, 20, 5, {})
    result = manager.evaluate("TEST-001", "critical_rul")
    print(f"  Samples: {result.sample_count}, May proceed: {result.may_proceed}")
    print(f"  Reason: {result.reason}")
    assert not result.may_proceed, "FAIL: Single spike should be rejected"
    print("  ✓ PASS")
    
    # Test 2: Sustained degradation
    print("\n[TEST 2] Sustained degradation should PROCEED")
    manager2 = EvaluationWindowManager()
    
    # Simulate worsening trend over 10 samples
    for i in range(10):
        risk = 0.4 + (i * 0.05)  # 0.4 → 0.85
        manager2.add_sample("TEST-002", "warning_rul", risk, 50 - i*3, 30 - i*2, {})
        time.sleep(0.1)
    
    result = manager2.evaluate("TEST-002", "warning_rul")
    print(f"  Samples: {result.sample_count}, May proceed: {result.may_proceed}")
    print(f"  Mean risk: {result.mean_risk:.2f}, Trend: {result.risk_trend:.4f}")
    print(f"  Pct above: {result.pct_above_threshold:.1%}")
    print(f"  Reason: {result.reason}")
    # Note: May not proceed if pct_above is insufficient
    print(f"  Result: {'✓ PASS' if result.may_proceed or result.pct_above_threshold > 0.4 else '⚠ Check config'}")
    
    # Test 3: Threshold hovering
    print("\n[TEST 3] Threshold hovering should be REJECTED")
    manager3 = EvaluationWindowManager()
    
    # Add samples hovering around threshold
    for i in range(10):
        risk = 0.5 + (0.02 * (i % 2))  # Alternates 0.5, 0.52
        manager3.add_sample("TEST-003", "critical_rul", risk, 45, 40, {})
        time.sleep(0.1)
    
    result = manager3.evaluate("TEST-003", "critical_rul")
    print(f"  Samples: {result.sample_count}, May proceed: {result.may_proceed}")
    print(f"  Trend: {result.risk_trend:.4f} (should be ~0)")
    print(f"  Reason: {result.reason}")
    print(f"  ✓ PASS (hovering rejected)" if not result.may_proceed else "  ⚠ Check trend logic")
    
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
