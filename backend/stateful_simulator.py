"""
Stateful Sensor Simulation with Physics-Based Degradation
Integrates NASA IMS Bearing Dataset for realistic failure simulation

4-MACHINE ARCHITECTURE:
- M-001: NORMAL (stable baseline)
- M-002: NORMAL (slight noise)
- M-003: FAILING (NASA degradation data)
- M-004: MANUAL (operator control)
"""
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)


class StatefulSensor:
    """Individual sensor with memory and degradation"""
    
    def __init__(self, name: str, baseline: float, limits: tuple):
        self.name = name
        self.baseline = baseline
        self.min_limit, self.max_limit = limits
        
        # Current state
        self.current_value = baseline
        self.drift_accumulator = 0.0
        self.noise_level = 0.02  # 2% noise
        
    def update(self, degradation_factor: float, dt: float = 1.0):
        """Update sensor value with physics-based degradation"""
        # Brownian motion (time-correlated noise)
        noise = np.random.normal(0, self.noise_level * self.baseline)
        
        # Drift towards degraded state
        drift_rate = (degradation_factor - 1.0) * 0.001  # Slow drift
        self.drift_accumulator += drift_rate * dt
        
        # Calculate new value
        degraded_baseline = self.baseline * degradation_factor
        self.current_value = degraded_baseline + self.drift_accumulator + noise
        
        # Enforce physical limits
        self.current_value = np.clip(self.current_value, self.min_limit, self.max_limit)
        
        return self.current_value
    
    def reset(self):
        """Reset sensor to healthy baseline (after maintenance)"""
        self.current_value = self.baseline
        self.drift_accumulator = 0.0


class MachineSimulator:
    """Stateful machine simulator with realistic degradation"""
    
    def __init__(self, machine_id: str, machine_type: str = None, initial_runtime_hours: float = 0.0):
        self.machine_id = machine_id
        self.runtime_hours = initial_runtime_hours
        self.last_update = datetime.now()
        
        # Get machine type from config or use provided
        if machine_type is None:
            machine_type = Config.MACHINE_ASSIGNMENTS.get(machine_id, "FEEDWATER_PUMP")
        self.machine_type = machine_type
        
        # Get type-specific configuration
        type_config = Config.MACHINE_TYPES.get(machine_type, Config.MACHINE_TYPES["FEEDWATER_PUMP"])
        baselines = type_config["baselines"]
        variance = type_config.get("variance", {})
        
        self.machine_name = type_config["name"]
        self.machine_description = type_config["description"]
        
        # Initialize sensors with type-specific baselines
        self.sensors = {
            'vibration_x': StatefulSensor(
                'vibration_x',
                baselines.get('vibration_x', 0.5),
                Config.SENSOR_LIMITS['vibration_x']
            ),
            'vibration_y': StatefulSensor(
                'vibration_y',
                baselines.get('vibration_y', 0.5),
                Config.SENSOR_LIMITS['vibration_y']
            ),
            'temperature': StatefulSensor(
                'temperature',
                baselines.get('temperature', 70.0),
                Config.SENSOR_LIMITS['temperature']
            ),
            'pressure': StatefulSensor(
                'pressure',
                baselines.get('pressure', 100.0),
                Config.SENSOR_LIMITS['pressure']
            ),
            'rpm': StatefulSensor(
                'rpm',
                baselines.get('rpm', 1500.0),
                Config.SENSOR_LIMITS['rpm']
            )
        }
        
        # Set type-specific noise levels based on variance
        if variance:
            self.sensors['vibration_x'].noise_level = variance.get('vibration', 0.08) / baselines.get('vibration_x', 0.5) * 0.5
            self.sensors['vibration_y'].noise_level = variance.get('vibration', 0.08) / baselines.get('vibration_y', 0.5) * 0.5
            self.sensors['temperature'].noise_level = variance.get('temperature', 3.0) / baselines.get('temperature', 70.0)
            if baselines.get('pressure', 0) > 0:
                self.sensors['pressure'].noise_level = variance.get('pressure', 5.0) / baselines.get('pressure', 100.0)
            self.sensors['rpm'].noise_level = variance.get('rpm', 15.0) / baselines.get('rpm', 1500.0)
    
    def advance_time(self, hours: float = 0.0333):  # Default: ~2 minutes
        """Advance machine runtime and update sensors"""
        self.runtime_hours += hours
        
        # Get current degradation phase and factor
        phase = Config.get_degradation_phase(self.runtime_hours)
        degradation_factor = Config.get_degradation_factor(phase)
        
        # Update all sensors
        sensor_readings = {}
        for name, sensor in self.sensors.items():
            value = sensor.update(degradation_factor, dt=hours)
            sensor_readings[name] = round(value, 3)
        
        self.last_update = datetime.now()
        
        return {
            'machine_id': self.machine_id,
            'timestamp': self.last_update.isoformat(),
            'runtime_hours': round(self.runtime_hours, 2),
            'sensors': sensor_readings,
            'health_state': phase.lower(),
            'degradation_factor': degradation_factor
        }
    
    def get_current_reading(self):
        """Get current sensor reading without advancing time"""
        sensor_readings = {
            name: round(sensor.current_value, 3)
            for name, sensor in self.sensors.items()
        }
        
        phase = Config.get_degradation_phase(self.runtime_hours)
        
        return {
            'machine_id': self.machine_id,
            'timestamp': datetime.now().isoformat(),
            'runtime_hours': round(self.runtime_hours, 2),
            'sensors': sensor_readings,
            'health_state': phase.lower(),
            'degradation_factor': Config.get_degradation_factor(phase)
        }
    
    def perform_maintenance(self):
        """Simulate maintenance - reset sensors and runtime"""
        for sensor in self.sensors.values():
            sensor.reset()
        self.runtime_hours = 0.0
        print(f"✓ Maintenance performed on {self.machine_id}")


class FleetSimulator:
    """Manages multiple stateful machine simulators for thermal power plant
    
    4-MACHINE ARCHITECTURE (NASA IMS Integration):
    - M-001: NORMAL (stable baseline - no alerts)
    - M-002: NORMAL (slight noise - auto-cleared warnings)
    - M-003: FAILING (NASA IMS degradation - failure progression)
    - M-004: MANUAL (operator control)
    """
    
    def __init__(self):
        # Initialize fleet with 4-machine architecture
        self.machines = {
            # M-001: NORMAL - Stable baseline
            'M-001': MachineSimulator('M-001', 'FEEDWATER_PUMP', initial_runtime_hours=50),
            # M-002: NORMAL - With slight noise
            'M-002': MachineSimulator('M-002', 'FEEDWATER_PUMP', initial_runtime_hours=0),
            # M-003: FAILING - Uses NASA degradation data
            'M-003': MachineSimulator('M-003', 'HVAC_CHILLER', initial_runtime_hours=80),
            # M-004: MANUAL - Operator control
            'M-004': MachineSimulator('M-004', 'BOILER_FEED_MOTOR', initial_runtime_hours=50),
        }
        
        # Manual override for MANUAL mode machines
        self.manual_override: Dict[str, Dict] = {}
        
        # Demo mode flag (legacy compatibility)
        self.demo_mode_active: Dict[str, bool] = {}
        
        # ==================== NASA FAILING MODE STATE ====================
        # Degradation progress for FAILING mode machines (0.0 = healthy, 1.0 = failure)
        self.degradation_progress: Dict[str, float] = {'M-003': 0.0}
        self.degradation_start_time: Dict[str, Optional[datetime]] = {'M-003': None}
        
        # NASA Data Loader (lazy init)
        self._nasa_loader = None
        
        # Noise level for NORMAL mode machines
        self.noise_levels = {
            'M-001': 0.02,  # 2% noise - very stable
            'M-002': 0.10,  # 10% noise - occasional spikes
        }
        
        print(f"✓ {Config.PLANT_NAME} fleet initialized with {len(self.machines)} equipment:")
        for mid, machine in self.machines.items():
            mode = Config.MACHINE_MODES.get(mid, 'NORMAL')
            print(f"  - {mid}: {machine.machine_name} [{mode}]")
            
        # ==================== STRESS SCENARIO ENGINE ====================
        from stress_scenarios import get_stress_engine
        self.stress_engine = get_stress_engine()

    
    @property
    def nasa_loader(self):
        """Lazy-load NASA data loader."""
        if self._nasa_loader is None:
            try:
                from nasa_data_loader import get_nasa_loader
                self._nasa_loader = get_nasa_loader()
                logger.info(f"✓ NASA loader: {self._nasa_loader.total_files} files")
            except Exception as e:
                logger.warning(f"NASA loader failed: {e}")
                self._nasa_loader = None
        return self._nasa_loader

    
    def set_manual_override(self, machine_id: str, sensor_values: Dict) -> bool:
        """Set manual sensor values for a machine (for demo)"""
        if machine_id not in self.machines:
            return False
        self.manual_override[machine_id] = sensor_values
        print(f"✓ Manual override set for {machine_id}: {sensor_values}")
        return True
    
    def clear_manual_override(self, machine_id: str) -> bool:
        """Clear manual override and return to automatic simulation"""
        if machine_id in self.manual_override:
            del self.manual_override[machine_id]
            print(f"✓ Manual override cleared for {machine_id}")
            return True
        return False
    
    def advance_all(self, hours: float = 0.0333):
        """Advance time for all machines"""
        readings = []
        for machine in self.machines.values():
            reading = machine.advance_time(hours)
            readings.append(reading)
        return readings
    
    def get_all_readings(self):
        """Get current readings from all machines (using mode-aware logic)"""
        readings = []
        for machine_id in self.machines:
            # Use get_machine_reading to ensure all modes/stress/overrides are applied
            reading = self.get_machine_reading(machine_id)
            if reading:
                readings.append(reading)
        return readings
    
    def get_machine_reading(self, machine_id: str):
        """
        Get reading from specific machine - MODE AWARE
        
        Modes:
        - NORMAL: Stable baseline with low noise
        - FAILING: Progressive degradation using NASA IMS data
        - MANUAL: Operator-controlled values
        """
        if machine_id not in self.machines:
            return None
        
        from config import Config
        mode = Config.MACHINE_MODES.get(machine_id, 'NORMAL')
        
        # Get base reading from simulation
        reading = self.machines[machine_id].get_current_reading()
        reading['mode'] = mode
        reading['manual_override'] = False
        
        # ==================== NORMAL MODE ====================
        if mode == 'NORMAL':
            # Stable baseline with configurable noise
            noise_level = self.noise_levels.get(machine_id, 0.02)
            
            # Apply slight noise to sensors (but keep them stable)
            for sensor_name in reading['sensors']:
                base_value = reading['sensors'][sensor_name]
                noise = np.random.normal(0, noise_level * abs(base_value))
                reading['sensors'][sensor_name] = round(base_value + noise, 3)
            
            # Force healthy state for NORMAL mode
            reading['health_state'] = 'healthy'
            reading['degradation_factor'] = 1.0
            return reading
        
        # ==================== FAILING MODE (NASA DATA) ====================
        elif mode == 'FAILING':
            # Initialize start time if not set
            if self.degradation_start_time.get(machine_id) is None:
                self.degradation_start_time[machine_id] = datetime.now()
            
            # Calculate degradation progress based on elapsed time
            elapsed = (datetime.now() - self.degradation_start_time[machine_id]).total_seconds()
            
            # Get degradation rate (custom if set, otherwise from config)
            if hasattr(self, 'custom_degradation_rates') and machine_id in self.custom_degradation_rates:
                degradation_rate = self.custom_degradation_rates[machine_id]
            else:
                mode_config = Config.MACHINE_MODE_CONFIG.get('FAILING', {})
                degradation_rate = mode_config.get('degradation_rate', 0.001)
            
            # Update progress (capped at 1.0)
            self.degradation_progress[machine_id] = min(1.0, elapsed * degradation_rate)
            progress = self.degradation_progress[machine_id]
            
            # Get NASA features for current progress
            if self.nasa_loader:
                nasa_features = self.nasa_loader.get_degradation_features(progress)
            else:
                nasa_features = None
            
            # Apply NASA degradation to sensors
            if nasa_features:
                # Map NASA features to sensor readings
                # RMS → vibration (normalized to baseline)
                baseline_vib = self.machines[machine_id].sensors['vibration_x'].baseline
                rms_ratio = nasa_features['rms'] / 0.13  # Normalize to healthy baseline
                reading['sensors']['vibration_x'] = round(baseline_vib * rms_ratio, 3)
                reading['sensors']['vibration_y'] = round(baseline_vib * rms_ratio * 1.1, 3)
                
                # Temperature increases with degradation
                baseline_temp = self.machines[machine_id].sensors['temperature'].baseline
                temp_increase = progress * 20  # Up to 20°C increase at failure
                reading['sensors']['temperature'] = round(baseline_temp + temp_increase, 1)
                
                # Pressure decreases with degradation (for pumps)
                baseline_pressure = self.machines[machine_id].sensors['pressure'].baseline
                if baseline_pressure > 0:
                    pressure_drop = progress * 30  # Up to 30 PSI drop at failure
                    reading['sensors']['pressure'] = round(baseline_pressure - pressure_drop, 1)
            else:
                # Synthetic degradation fallback
                degradation_factor = 1 + progress * 1.5
                for sensor_name in ['vibration_x', 'vibration_y']:
                    reading['sensors'][sensor_name] = round(
                        reading['sensors'][sensor_name] * degradation_factor, 3
                    )
            
            # Update health state based on progress
            if progress < 0.3:
                reading['health_state'] = 'healthy'
            elif progress < 0.6:
                reading['health_state'] = 'degrading'
            elif progress < 0.85:
                reading['health_state'] = 'pre_failure'
            else:
                reading['health_state'] = 'failure'
            
            reading['degradation_factor'] = 1 + progress * 1.5
            reading['degradation_progress'] = round(progress, 3)
            return reading
        
        # ==================== MANUAL MODE ====================
        elif mode == 'MANUAL':
            # Apply manual override if set
            if machine_id in self.manual_override:
                override = self.manual_override[machine_id]
                reading['sensors'].update(override)
                reading['manual_override'] = True
            return reading
        
        # ==================== LEGACY DEMO MODE ====================
        # Check for active scenario (backward compatibility)
        if self.demo_mode_active.get(machine_id, False):
            from demo_scenarios import get_scenario_player
            player = get_scenario_player()
            scenario_reading = player.get_current_reading(machine_id)
            if scenario_reading:
                scenario_reading['mode'] = 'DEMO'
                scenario_reading['manual_override'] = False
                return scenario_reading
        
        # ==================== APPLY STRESS SCENARIOS ====================
        # Inject stress BEFORE returning readings (affects ML & Alerts)
        if hasattr(self, 'stress_engine'):
            # Apply stress to sensor readings
            stressed_sensors = self.stress_engine.apply_stress(machine_id, reading['sensors'])
            reading['sensors'] = stressed_sensors
            
            # Check if active scenario exists
            scenario = self.stress_engine.get_scenario(machine_id)
            if scenario:
                reading['active_scenario'] = scenario.to_dict()
        
        return reading

    def start_stress_scenario(self, machine_id: str, scenario_type: str, severity: float = 0.5, duration_sec: int = 120):
        """Start a stress scenario on a machine."""
        if hasattr(self, 'stress_engine'):
            return self.stress_engine.start_scenario(machine_id, scenario_type, severity, duration_sec)
        return {"error": "Stress engine not initialized"}

    def stop_stress_scenario(self, machine_id: str):
        """Stop any active stress scenario on a machine."""
        if hasattr(self, 'stress_engine'):
            return self.stress_engine.stop_scenario(machine_id)
        return {"error": "Stress engine not initialized"}

    def reset_failing_mode(self, machine_id: str) -> bool:
        """Reset FAILING mode machine to start degradation from beginning."""
        if machine_id in self.degradation_progress:
            self.degradation_progress[machine_id] = 0.0
            self.degradation_start_time[machine_id] = datetime.now()
            
            # Reset the machine's internal state too
            if machine_id in self.machines:
                self.machines[machine_id].perform_maintenance()
            
            logger.info(f"✓ Reset FAILING mode for {machine_id}")
            return True
        return False
    
    def set_degradation_rate(self, machine_id: str, rate: float) -> bool:
        """Set degradation rate for a machine (for testing/demo)."""
        if machine_id in self.machines:
            # Store custom rate (used by get_machine_reading)
            if not hasattr(self, 'custom_degradation_rates'):
                self.custom_degradation_rates = {}
            self.custom_degradation_rates[machine_id] = rate
            logger.info(f"✓ Set degradation rate for {machine_id}: {rate}")
            return True
        return False
    
    def start_demo_scenario(self, machine_id: str, scenario_id: str = 'BFP-A1-FAILURE', speed: float = 1.0):
        """Start a failure scenario for demo machine (usually M-002)"""
        from demo_scenarios import get_scenario_player
        player = get_scenario_player()
        self.demo_mode_active[machine_id] = True
        result = player.start_scenario(machine_id, scenario_id, speed)
        return result
    
    def stop_demo_scenario(self, machine_id: str):
        """Stop demo scenario and return to simulation mode"""
        from demo_scenarios import get_scenario_player
        player = get_scenario_player()
        result = player.stop_scenario(machine_id)
        self.demo_mode_active[machine_id] = False
        
        # Reset machine to healthy state after scenario ends
        if machine_id in self.machines:
            self.machines[machine_id].perform_maintenance()
            print(f"✓ {machine_id} reset to healthy state after scenario stop")
        
        return result
    
    def is_demo_active(self, machine_id: str) -> bool:
        """Check if demo scenario is active for machine"""
        return self.demo_mode_active.get(machine_id, False)
    
    def perform_maintenance(self, machine_id: str):
        """Perform maintenance on a specific machine"""
        if machine_id in self.machines:
            # Stop any active scenario first
            self.stop_demo_scenario(machine_id)
            
            # Perform maintenance
            self.machines[machine_id].perform_maintenance()
            
            # Clear any manual override
            self.clear_manual_override(machine_id)
            return True
        return False


# Global fleet instance
fleet = FleetSimulator()


if __name__ == "__main__":
    # Test stateful sensors
    print("Testing Stateful Sensor Simulation...")
    print("=" * 60)
    
    # Test single machine
    machine = MachineSimulator('TEST-001', initial_runtime_hours=0)
    
    print("\nSimulating 10 time steps (healthy phase):")
    for i in range(10):
        reading = machine.advance_time(hours=10)  # Advance 10 hours each step
        print(f"Step {i+1}: Runtime={reading['runtime_hours']}h, "
              f"Phase={reading['health_state']}, "
              f"Temp={reading['sensors']['temperature']:.1f}°C, "
              f"Vib={reading['sensors']['vibration_x']:.3f}")
    
    # Jump to degrading phase
    print("\nJumping to degrading phase (600 hours)...")
    machine.runtime_hours = 600
    
    print("\nSimulating 10 time steps (degrading phase):")
    for i in range(10):
        reading = machine.advance_time(hours=10)
        print(f"Step {i+1}: Runtime={reading['runtime_hours']}h, "
              f"Phase={reading['health_state']}, "
              f"Temp={reading['sensors']['temperature']:.1f}°C, "
              f"Vib={reading['sensors']['vibration_x']:.3f}")
    
    # Test maintenance
    print("\nPerforming maintenance...")
    machine.perform_maintenance()
    reading = machine.get_current_reading()
    print(f"After maintenance: Runtime={reading['runtime_hours']}h, "
          f"Temp={reading['sensors']['temperature']:.1f}°C")
    
    print("\n" + "=" * 60)
    print("✓ Stateful sensor simulation working correctly!")
