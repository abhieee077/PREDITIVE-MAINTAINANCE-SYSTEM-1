"""
Stress Scenario Engine for Industrial Predictive Maintenance

Provides industry-realistic stress scenarios that can be injected
BEFORE ML processing to test system response to extreme conditions.

Scenario Types:
- LOAD_SPIKE: Sudden high load
- LUBRICATION_LOSS: Accelerated wear
- COOLING_FAILURE: Temperature rise
- SENSOR_DRIFT: Sensor bias
- RUNAWAY_FAILURE: Rapid degradation (the "wow" moment)

Stress is injected at sensor level to preserve metric validity.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    NONE = "NONE"
    LOAD_SPIKE = "LOAD_SPIKE"
    LUBRICATION_LOSS = "LUBRICATION_LOSS"
    COOLING_FAILURE = "COOLING_FAILURE"
    SENSOR_DRIFT = "SENSOR_DRIFT"
    RUNAWAY_FAILURE = "RUNAWAY_FAILURE"


@dataclass
class StressScenario:
    """Active stress scenario configuration."""
    scenario_type: ScenarioType = ScenarioType.NONE
    severity: float = 0.0  # 0.0 - 1.0 (continuous, not binary)
    duration_sec: int = 0
    start_time: Optional[datetime] = None
    machine_id: str = ""
    is_demo_tagged: bool = True  # Excluded from baseline metrics
    
    @property
    def is_active(self) -> bool:
        """Check if scenario is currently active."""
        if self.scenario_type == ScenarioType.NONE:
            return False
        if self.start_time is None:
            return False
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed < self.duration_sec
    
    @property
    def progress(self) -> float:
        """Progress through scenario (0.0 - 1.0)."""
        if not self.is_active:
            return 0.0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return min(1.0, elapsed / self.duration_sec) if self.duration_sec > 0 else 1.0
    
    @property
    def remaining_sec(self) -> float:
        """Seconds remaining in scenario."""
        if not self.is_active:
            return 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return max(0, self.duration_sec - elapsed)
    
    def to_dict(self) -> Dict:
        """Convert to API-friendly dictionary."""
        return {
            "type": self.scenario_type.value,
            "severity": self.severity,
            "duration_sec": self.duration_sec,
            "remaining_sec": round(self.remaining_sec, 1),
            "progress": round(self.progress, 3),
            "is_active": self.is_active,
            "machine_id": self.machine_id,
            "is_demo_tagged": self.is_demo_tagged
        }


class StressScenarioEngine:
    """
    Manages stress scenarios for machines.
    
    Scenarios are injected BEFORE ML processing:
    Sensor Simulation → Stress Scenario → Feature Extraction → XGBoost → Alerts
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._active_scenarios: Dict[str, StressScenario] = {}
        
        # Drift bias for SENSOR_DRIFT (persists during scenario)
        self._drift_bias: Dict[str, float] = {}
        
        logger.info("✓ Stress Scenario Engine initialized")
    
    def start_scenario(
        self,
        machine_id: str,
        scenario_type: str,
        severity: float = 0.5,
        duration_sec: int = 120
    ) -> Dict:
        """
        Start a stress scenario on a machine.
        
        Args:
            machine_id: Target machine
            scenario_type: One of LOAD_SPIKE, LUBRICATION_LOSS, etc.
            severity: 0.0 - 1.0 (continuous)
            duration_sec: Duration in seconds
        """
        with self._lock:
            # Parse scenario type
            try:
                stype = ScenarioType(scenario_type.upper())
            except ValueError:
                return {"error": f"Unknown scenario type: {scenario_type}"}
            
            # Validate severity
            severity = max(0.0, min(1.0, severity))
            
            # Create scenario
            scenario = StressScenario(
                scenario_type=stype,
                severity=severity,
                duration_sec=duration_sec,
                start_time=datetime.now(),
                machine_id=machine_id,
                is_demo_tagged=True
            )
            
            self._active_scenarios[machine_id] = scenario
            
            # Initialize drift bias for sensor drift
            if stype == ScenarioType.SENSOR_DRIFT:
                import random
                self._drift_bias[machine_id] = random.uniform(-0.1, 0.1)
            
            logger.info(f"✓ Started {stype.value} on {machine_id} (severity={severity}, duration={duration_sec}s)")
            
            return {
                "success": True,
                "scenario": scenario.to_dict()
            }
    
    def stop_scenario(self, machine_id: str) -> Dict:
        """Stop any active scenario on a machine."""
        with self._lock:
            if machine_id in self._active_scenarios:
                scenario = self._active_scenarios[machine_id]
                del self._active_scenarios[machine_id]
                
                # Clear drift bias
                if machine_id in self._drift_bias:
                    del self._drift_bias[machine_id]
                
                logger.info(f"✓ Stopped scenario on {machine_id}")
                return {"success": True, "stopped": scenario.to_dict()}
            
            return {"success": False, "error": "No active scenario"}
    
    def get_scenario(self, machine_id: str) -> Optional[StressScenario]:
        """Get active scenario for a machine (if any)."""
        with self._lock:
            scenario = self._active_scenarios.get(machine_id)
            if scenario and not scenario.is_active:
                # Scenario expired
                del self._active_scenarios[machine_id]
                return None
            return scenario
    
    def get_all_active(self) -> Dict[str, Dict]:
        """Get all active scenarios."""
        with self._lock:
            result = {}
            expired = []
            
            for mid, scenario in self._active_scenarios.items():
                if scenario.is_active:
                    result[mid] = scenario.to_dict()
                else:
                    expired.append(mid)
            
            # Clean up expired
            for mid in expired:
                del self._active_scenarios[mid]
            
            return result
    
    def apply_stress(self, machine_id: str, sensor_state: Dict) -> Dict:
        """
        Apply stress scenario to sensor readings.
        
        This is called BEFORE feature extraction / ML.
        
        Args:
            machine_id: Machine ID
            sensor_state: Dict with sensor values (vibration_x, temperature, etc.)
            
        Returns:
            Modified sensor_state with stress applied
        """
        scenario = self.get_scenario(machine_id)
        if not scenario or not scenario.is_active:
            return sensor_state
        
        # Copy to avoid mutating original
        stressed = sensor_state.copy()
        severity = scenario.severity
        stype = scenario.scenario_type
        
        # ==================== LOAD_SPIKE ====================
        if stype == ScenarioType.LOAD_SPIKE:
            # Sudden high load → increased vibration and RPM
            stressed['vibration_x'] = stressed.get('vibration_x', 0.5) * (1 + 0.5 * severity)
            stressed['vibration_y'] = stressed.get('vibration_y', 0.5) * (1 + 0.5 * severity)
            stressed['rpm'] = stressed.get('rpm', 1500) * (1 + 0.3 * severity)
        
        # ==================== LUBRICATION_LOSS ====================
        elif stype == ScenarioType.LUBRICATION_LOSS:
            # Accelerated wear → vibration increase + temp rise
            stressed['vibration_x'] = stressed.get('vibration_x', 0.5) + 0.3 * severity
            stressed['vibration_y'] = stressed.get('vibration_y', 0.5) + 0.3 * severity
            stressed['temperature'] = stressed.get('temperature', 70) + 10 * severity
        
        # ==================== COOLING_FAILURE ====================
        elif stype == ScenarioType.COOLING_FAILURE:
            # Temperature rise only
            stressed['temperature'] = stressed.get('temperature', 70) + 15 * severity
        
        # ==================== SENSOR_DRIFT ====================
        elif stype == ScenarioType.SENSOR_DRIFT:
            # Gradual sensor bias
            drift = self._drift_bias.get(machine_id, 0.05)
            stressed['vibration_x'] = stressed.get('vibration_x', 0.5) + drift * severity
            stressed['vibration_y'] = stressed.get('vibration_y', 0.5) + drift * severity * 0.8
        
        # ==================== RUNAWAY_FAILURE (WOW MOMENT) ====================
        elif stype == ScenarioType.RUNAWAY_FAILURE:
            # Rapid degradation - all parameters degrade fast
            progress = scenario.progress  # Use progress for acceleration
            accel = 1 + 2 * severity * progress  # Accelerating factor
            
            stressed['vibration_x'] = stressed.get('vibration_x', 0.5) * accel
            stressed['vibration_y'] = stressed.get('vibration_y', 0.5) * accel
            stressed['temperature'] = stressed.get('temperature', 70) + 20 * severity * progress
            
            # Pressure drops
            if stressed.get('pressure', 0) > 0:
                stressed['pressure'] = stressed.get('pressure', 100) * (1 - 0.3 * severity * progress)
        
        # Mark as stressed
        stressed['_stress_scenario'] = stype.value
        stressed['_stress_severity'] = severity
        
        return stressed


# Global singleton
_engine: Optional[StressScenarioEngine] = None


def get_stress_engine() -> StressScenarioEngine:
    """Get or create the global stress scenario engine."""
    global _engine
    if _engine is None:
        _engine = StressScenarioEngine()
    return _engine


# ==================== SELF TEST ====================
if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("STRESS SCENARIO ENGINE TEST")
    print("=" * 60)
    
    engine = get_stress_engine()
    
    # Test LOAD_SPIKE
    print("\n--- Testing LOAD_SPIKE ---")
    result = engine.start_scenario("M-002", "LOAD_SPIKE", severity=0.7, duration_sec=5)
    print(f"Started: {result}")
    
    sensors = {"vibration_x": 0.5, "vibration_y": 0.5, "temperature": 70, "rpm": 1500}
    stressed = engine.apply_stress("M-002", sensors)
    print(f"Before: vib={sensors['vibration_x']:.3f}, rpm={sensors['rpm']:.0f}")
    print(f"After:  vib={stressed['vibration_x']:.3f}, rpm={stressed['rpm']:.0f}")
    
    # Test RUNAWAY_FAILURE
    print("\n--- Testing RUNAWAY_FAILURE (3 seconds) ---")
    engine.start_scenario("M-003", "RUNAWAY_FAILURE", severity=0.9, duration_sec=3)
    
    for i in range(4):
        stressed = engine.apply_stress("M-003", sensors.copy())
        scenario = engine.get_scenario("M-003")
        progress = scenario.progress if scenario else 0
        print(f"T+{i}s: progress={progress:.2f} vib={stressed['vibration_x']:.3f} temp={stressed['temperature']:.1f}")
        time.sleep(1)
    
    # Show all active
    print("\n--- Active Scenarios ---")
    print(engine.get_all_active())
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
