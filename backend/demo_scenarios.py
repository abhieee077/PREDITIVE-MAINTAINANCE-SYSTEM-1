"""
Demo Scenario System for Hackathon Presentation
Provides:
1. Virtual Preset Machine - Static healthy values (no changing)
2. Failure Scenario Player - Pre-scripted 3-4 minute degradation to failure
3. Professional sensor datasets based on real industrial profiles
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import threading
import time


class ScenarioState(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


@dataclass
class SensorSnapshot:
    """Single point in time sensor reading"""
    timestamp_offset_seconds: float  # Offset from scenario start
    vibration_x: float
    vibration_y: float
    temperature: float
    pressure: float
    rpm: float
    health_score: float
    anomaly_score: float
    phase: str  # HEALTHY, DEGRADING, PRE_FAILURE, FAILURE


# ==================== PRESET VIRTUAL MACHINES ====================
# These are STATIC - values never change (synchronized with config.py baselines)
PRESET_MACHINES = {
    "VIRTUAL-HEALTHY": {
        "name": "Virtual Healthy Reference",
        "description": "Static healthy machine - baseline for comparison",
        "sensors": {
            "vibration_x": 0.55,       # Synced with FEEDWATER_PUMP baseline
            "vibration_y": 0.60,
            "temperature": 52.0,       # Synced with FEEDWATER_PUMP baseline
            "pressure": 145.0,
            "rpm": 1480.0
        },
        "health_score": 98.5,
        "anomaly_score": 0.02,
        "rul_hours": 120.0,            # NEW: RUL prediction for lead time demo
        "phase": "HEALTHY",
        "status": "OPERATIONAL",
        "last_maintenance": "2026-01-15T09:00:00",
        "runtime_hours": 50.0
    },
    "VIRTUAL-DEGRADING": {
        "name": "Virtual Degrading Reference",
        "description": "Static degrading machine - shows warning state",
        "sensors": {
            "vibration_x": 1.25,       # Above warning threshold (1.2)
            "vibration_y": 1.18,
            "temperature": 72.0,       # Approaching warning (70.0)
            "pressure": 138.0,
            "rpm": 1465.0
        },
        "health_score": 62.0,
        "anomaly_score": 0.45,
        "rul_hours": 48.0,             # NEW: Warning level RUL
        "phase": "DEGRADING",
        "status": "WARNING",
        "last_maintenance": "2025-12-20T14:00:00",
        "runtime_hours": 600.0
    },
    "VIRTUAL-CRITICAL": {
        "name": "Virtual Critical Reference",
        "description": "Static critical machine - shows failure imminent",
        "sensors": {
            "vibration_x": 2.60,       # Above critical threshold (2.5)
            "vibration_y": 2.55,
            "temperature": 92.0,       # Above critical (85.0)
            "pressure": 95.0,          # Below critical low (100.0)
            "rpm": 1420.0
        },
        "health_score": 18.0,
        "anomaly_score": 0.95,
        "rul_hours": 8.0,              # NEW: Critical level RUL
        "phase": "PRE_FAILURE",
        "status": "CRITICAL",
        "last_maintenance": "2025-11-10T08:00:00",
        "runtime_hours": 920.0
    }
}


# ==================== FAILURE SCENARIO TIMELINE ====================
# Professional 4-minute failure scenario (240 seconds)
# Based on real industrial pump failure patterns

FAILURE_SCENARIO_BFP_A1: List[SensorSnapshot] = [
    # ============================================================
    # 60-SECOND DRAMATIC FAILURE SCENARIO
    # Perfect for 1-minute demo to judges
    # Visible degradation every 5 seconds
    # ============================================================
    
    # Phase 1: HEALTHY (0-10 seconds) - Stable baseline
    SensorSnapshot(0,  0.50, 0.52,  50.0, 145.0, 1480, 95.0, 0.05, "HEALTHY"),
    SensorSnapshot(5,  0.52, 0.54,  51.0, 145.0, 1480, 94.0, 0.06, "HEALTHY"),
    SensorSnapshot(10, 0.55, 0.58,  52.0, 144.8, 1479, 92.0, 0.08, "HEALTHY"),
    
    # Phase 2: DEGRADING (15-30 seconds) - VISIBLE CHANGE! 
    # Vibration: 0.5 → 1.5 mm/s, Temp: 52 → 75°C
    SensorSnapshot(15, 0.72, 0.75,  58.0, 143.0, 1475, 82.0, 0.25, "DEGRADING"),
    SensorSnapshot(20, 0.95, 1.00,  65.0, 140.0, 1468, 70.0, 0.40, "DEGRADING"),
    SensorSnapshot(25, 1.20, 1.28,  72.0, 136.0, 1458, 58.0, 0.55, "DEGRADING"),
    SensorSnapshot(30, 1.50, 1.60,  80.0, 132.0, 1445, 48.0, 0.65, "DEGRADING"),
    
    # Phase 3: PRE_FAILURE (35-45 seconds) - ALARM BELLS!
    # Vibration: 1.5 → 3.0 mm/s, Temp: 80 → 100°C
    SensorSnapshot(35, 1.85, 1.95,  88.0, 125.0, 1428, 38.0, 0.78, "PRE_FAILURE"),
    SensorSnapshot(40, 2.30, 2.45,  95.0, 118.0, 1405, 28.0, 0.88, "PRE_FAILURE"),
    SensorSnapshot(45, 2.80, 3.00, 102.0, 110.0, 1375, 18.0, 0.95, "PRE_FAILURE"),
    
    # Phase 4: FAILURE (50-60 seconds) - CRITICAL! TRIP IMMINENT!
    # Vibration: 3.0 → 7.0 mm/s, Temp: 100 → 150°C
    SensorSnapshot(50, 3.50, 3.75, 115.0,  95.0, 1320, 10.0, 0.98, "FAILURE"),
    SensorSnapshot(55, 5.00, 5.30, 135.0,  70.0, 1180,  3.0, 1.00, "FAILURE"),
    SensorSnapshot(60, 7.00, 7.50, 155.0,  35.0,  750,  0.0, 1.00, "FAILURE"),  # TRIP!
]


# Alternative: Slow degradation scenario (also 4 minutes but different pattern)
SLOW_FAILURE_SCENARIO: List[SensorSnapshot] = [
    # Gradual bearing wear pattern - temperature leads
    SensorSnapshot(0, 0.48, 0.50, 55.0, 143.0, 1478, 96.0, 0.03, "HEALTHY"),
    SensorSnapshot(15, 0.50, 0.52, 57.0, 142.8, 1477, 94.5, 0.05, "HEALTHY"),
    SensorSnapshot(30, 0.52, 0.55, 60.0, 142.5, 1476, 92.0, 0.08, "HEALTHY"),
    SensorSnapshot(45, 0.58, 0.60, 64.0, 142.0, 1474, 88.0, 0.15, "DEGRADING"),
    SensorSnapshot(60, 0.65, 0.68, 68.0, 141.0, 1472, 84.0, 0.22, "DEGRADING"),
    SensorSnapshot(75, 0.75, 0.78, 72.0, 140.0, 1468, 78.0, 0.32, "DEGRADING"),
    SensorSnapshot(90, 0.88, 0.92, 77.0, 138.5, 1464, 72.0, 0.42, "DEGRADING"),
    SensorSnapshot(105, 1.05, 1.10, 82.0, 136.5, 1458, 65.0, 0.52, "DEGRADING"),
    SensorSnapshot(120, 1.28, 1.35, 87.0, 134.0, 1450, 56.0, 0.62, "PRE_FAILURE"),
    SensorSnapshot(135, 1.55, 1.62, 92.0, 130.0, 1440, 47.0, 0.72, "PRE_FAILURE"),
    SensorSnapshot(150, 1.88, 1.98, 97.0, 125.0, 1428, 38.0, 0.82, "PRE_FAILURE"),
    SensorSnapshot(165, 2.25, 2.38, 102.0, 118.0, 1412, 29.0, 0.90, "PRE_FAILURE"),
    SensorSnapshot(180, 2.72, 2.88, 108.0, 109.0, 1390, 20.0, 0.95, "FAILURE"),
    SensorSnapshot(195, 3.35, 3.55, 116.0, 98.0, 1358, 12.0, 0.98, "FAILURE"),
    SensorSnapshot(210, 4.18, 4.42, 126.0, 82.0, 1305, 5.0, 1.00, "FAILURE"),
    SensorSnapshot(225, 5.25, 5.55, 138.0, 60.0, 1220, 1.0, 1.00, "FAILURE"),
    SensorSnapshot(240, 6.80, 7.15, 155.0, 30.0, 1050, 0.0, 1.00, "FAILURE"),
]


class ScenarioPlayer:
    """
    Plays pre-recorded failure scenarios in real-time.
    For hackathon demo - shows realistic 3-4 minute failure progression.
    """
    
    def __init__(self):
        self.scenarios = {
            "BFP-A1-FAILURE": FAILURE_SCENARIO_BFP_A1,
            "SLOW-BEARING-WEAR": SLOW_FAILURE_SCENARIO,
        }
        
        # Current playback state per machine
        self.active_scenarios: Dict[str, dict] = {}
        self._lock = threading.Lock()
        
    def get_available_scenarios(self) -> List[dict]:
        """List all available demo scenarios"""
        return [
            {
                "id": "BFP-A1-FAILURE",
                "name": "Feedwater Pump Catastrophic Failure",
                "duration_seconds": 240,
                "description": "Rapid bearing failure with vibration spike - 4 minutes",
                "phases": ["HEALTHY", "DEGRADING", "PRE_FAILURE", "FAILURE"],
                "datapoints": len(FAILURE_SCENARIO_BFP_A1)
            },
            {
                "id": "SLOW-BEARING-WEAR",
                "name": "Gradual Bearing Wear",
                "duration_seconds": 240,
                "description": "Slow temperature-led degradation - 4 minutes",
                "phases": ["HEALTHY", "DEGRADING", "PRE_FAILURE", "FAILURE"],
                "datapoints": len(SLOW_FAILURE_SCENARIO)
            }
        ]
    
    def start_scenario(self, machine_id: str, scenario_id: str, speed_multiplier: float = 1.0) -> dict:
        """
        Start playing a scenario for a machine.
        speed_multiplier: 1.0 = real-time, 2.0 = 2x speed, 0.5 = half speed
        """
        if scenario_id not in self.scenarios:
            return {"success": False, "error": f"Unknown scenario: {scenario_id}"}
        
        with self._lock:
            self.active_scenarios[machine_id] = {
                "scenario_id": scenario_id,
                "started_at": datetime.now(),
                "speed_multiplier": speed_multiplier,
                "state": ScenarioState.RUNNING,
                "current_index": 0,
                "paused_at": None
            }
        
        print(f"▶ Started scenario '{scenario_id}' for {machine_id} at {speed_multiplier}x speed")
        
        return {
            "success": True,
            "machine_id": machine_id,
            "scenario_id": scenario_id,
            "duration_seconds": 240 / speed_multiplier,
            "state": "RUNNING"
        }
    
    def pause_scenario(self, machine_id: str) -> dict:
        """Pause active scenario"""
        with self._lock:
            if machine_id not in self.active_scenarios:
                return {"success": False, "error": "No active scenario"}
            
            scenario = self.active_scenarios[machine_id]
            scenario["state"] = ScenarioState.PAUSED
            scenario["paused_at"] = datetime.now()
            
        return {"success": True, "state": "PAUSED"}
    
    def resume_scenario(self, machine_id: str) -> dict:
        """Resume paused scenario"""
        with self._lock:
            if machine_id not in self.active_scenarios:
                return {"success": False, "error": "No active scenario"}
            
            scenario = self.active_scenarios[machine_id]
            if scenario["state"] != ScenarioState.PAUSED:
                return {"success": False, "error": "Scenario not paused"}
            
            # Adjust start time to account for pause
            pause_duration = datetime.now() - scenario["paused_at"]
            scenario["started_at"] += pause_duration
            scenario["state"] = ScenarioState.RUNNING
            scenario["paused_at"] = None
            
        return {"success": True, "state": "RUNNING"}
    
    def stop_scenario(self, machine_id: str) -> dict:
        """Stop and remove scenario"""
        with self._lock:
            if machine_id in self.active_scenarios:
                del self.active_scenarios[machine_id]
                print(f"⏹ Stopped scenario for {machine_id}")
                return {"success": True, "message": "Scenario stopped"}
        return {"success": False, "error": "No active scenario"}
    
    def get_current_reading(self, machine_id: str) -> Optional[dict]:
        """
        Get current sensor reading based on scenario timeline.
        Returns None if no active scenario.
        """
        with self._lock:
            if machine_id not in self.active_scenarios:
                return None
            
            scenario_data = self.active_scenarios[machine_id]
            
            # If paused, return last reading
            if scenario_data["state"] == ScenarioState.PAUSED:
                snapshots = self.scenarios[scenario_data["scenario_id"]]
                idx = min(scenario_data["current_index"], len(snapshots) - 1)
                return self._snapshot_to_reading(machine_id, snapshots[idx], scenario_data)
            
            # Calculate elapsed time with speed multiplier
            elapsed = (datetime.now() - scenario_data["started_at"]).total_seconds()
            elapsed *= scenario_data["speed_multiplier"]
            
            # Find the right snapshot
            snapshots = self.scenarios[scenario_data["scenario_id"]]
            current_snapshot = None
            
            for i, snapshot in enumerate(snapshots):
                if snapshot.timestamp_offset_seconds <= elapsed:
                    current_snapshot = snapshot
                    scenario_data["current_index"] = i
                else:
                    break
            
            # Check if scenario completed
            if elapsed >= snapshots[-1].timestamp_offset_seconds:
                scenario_data["state"] = ScenarioState.COMPLETED
                current_snapshot = snapshots[-1]
            
            if current_snapshot is None:
                current_snapshot = snapshots[0]
            
            return self._snapshot_to_reading(machine_id, current_snapshot, scenario_data)
    
    def _snapshot_to_reading(self, machine_id: str, snapshot: SensorSnapshot, scenario_data: dict) -> dict:
        """Convert snapshot to standard reading format matching MachineSimulator output"""
        # Calculate runtime_hours from scenario elapsed time (scaled appropriately)
        elapsed_scenario_seconds = snapshot.timestamp_offset_seconds
        simulated_runtime_hours = elapsed_scenario_seconds / 3600 * 100  # Scale: 1 second = ~100 hours simulated
        
        return {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
            "sensors": {
                "vibration_x": snapshot.vibration_x,
                "vibration_y": snapshot.vibration_y,
                "temperature": snapshot.temperature,
                "pressure": snapshot.pressure,
                "rpm": snapshot.rpm
            },
            "health_score": snapshot.health_score,
            "anomaly_score": snapshot.anomaly_score,
            "health_state": snapshot.phase.lower(),
            "runtime_hours": round(simulated_runtime_hours, 2),  # Required by machines endpoint
            "degradation_factor": 1.0 + (1.0 - snapshot.health_score / 100),  # Derive from health
            "scenario": {
                "id": scenario_data["scenario_id"],
                "state": scenario_data["state"].value,
                "progress_percent": round(
                    (scenario_data["current_index"] / 
                     len(self.scenarios[scenario_data["scenario_id"]])) * 100, 1
                ),
                "current_phase": snapshot.phase
            }
        }
    
    def get_scenario_status(self, machine_id: str) -> Optional[dict]:
        """Get status of active scenario for a machine"""
        with self._lock:
            if machine_id not in self.active_scenarios:
                return None
            
            scenario_data = self.active_scenarios[machine_id]
            snapshots = self.scenarios[scenario_data["scenario_id"]]
            
            elapsed = (datetime.now() - scenario_data["started_at"]).total_seconds()
            elapsed *= scenario_data["speed_multiplier"]
            
            return {
                "machine_id": machine_id,
                "scenario_id": scenario_data["scenario_id"],
                "state": scenario_data["state"].value,
                "elapsed_seconds": round(elapsed, 1),
                "total_seconds": snapshots[-1].timestamp_offset_seconds,
                "progress_percent": round(min(100, (elapsed / snapshots[-1].timestamp_offset_seconds) * 100), 1),
                "current_index": scenario_data["current_index"],
                "total_datapoints": len(snapshots),
                "speed_multiplier": scenario_data["speed_multiplier"]
            }
    
    def get_all_active_scenarios(self) -> List[dict]:
        """Get status of all active scenarios"""
        statuses = []
        for machine_id in list(self.active_scenarios.keys()):
            status = self.get_scenario_status(machine_id)
            if status:
                statuses.append(status)
        return statuses


def get_preset_machine(preset_id: str) -> Optional[dict]:
    """Get static preset machine data - values never change"""
    if preset_id in PRESET_MACHINES:
        machine = PRESET_MACHINES[preset_id].copy()
        machine["preset_id"] = preset_id
        machine["timestamp"] = datetime.now().isoformat()
        return machine
    return None


def get_all_preset_machines() -> List[dict]:
    """Get all available preset machines"""
    machines = []
    for preset_id in PRESET_MACHINES:
        machine = get_preset_machine(preset_id)
        if machine:
            machines.append(machine)
    return machines


# Global scenario player instance
_scenario_player = None


def get_scenario_player() -> ScenarioPlayer:
    """Get or create global scenario player"""
    global _scenario_player
    if _scenario_player is None:
        _scenario_player = ScenarioPlayer()
    return _scenario_player


# ==================== TEST ====================
if __name__ == "__main__":
    print("=" * 60)
    print("DEMO SCENARIO SYSTEM TEST")
    print("=" * 60)
    
    # Test preset machines
    print("\n📋 PRESET MACHINES (Static Values):")
    for preset_id in PRESET_MACHINES:
        machine = get_preset_machine(preset_id)
        print(f"\n  {preset_id}:")
        print(f"    Name: {machine['name']}")
        print(f"    Health: {machine['health_score']}%")
        print(f"    Status: {machine['status']}")
        print(f"    Sensors: T={machine['sensors']['temperature']}°C, "
              f"V={machine['sensors']['vibration_x']}mm/s")
    
    # Test scenario player
    print("\n\n🎬 SCENARIO PLAYER:")
    player = get_scenario_player()
    
    print("\n  Available Scenarios:")
    for scenario in player.get_available_scenarios():
        print(f"    - {scenario['id']}: {scenario['name']}")
        print(f"      Duration: {scenario['duration_seconds']}s, Points: {scenario['datapoints']}")
    
    # Start a scenario
    print("\n  Starting BFP-A1-FAILURE scenario at 10x speed...")
    result = player.start_scenario("M-001", "BFP-A1-FAILURE", speed_multiplier=10.0)
    print(f"  Result: {result}")
    
    # Read a few points
    print("\n  Reading scenario data (10 samples at 0.5s intervals):")
    for i in range(10):
        reading = player.get_current_reading("M-001")
        if reading:
            print(f"    t={i*0.5:.1f}s: Health={reading['health_score']}%, "
                  f"Phase={reading['scenario']['current_phase']}, "
                  f"Progress={reading['scenario']['progress_percent']}%")
        time.sleep(0.5)
    
    # Stop scenario
    player.stop_scenario("M-001")
    print("\n  Scenario stopped.")
    
    print("\n" + "=" * 60)
    print("✓ Demo scenario system ready for hackathon!")
