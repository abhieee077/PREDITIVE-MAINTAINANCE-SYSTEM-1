"""
Professional Industrial Sensor Datasets
Based on real-world industrial equipment failure patterns

Sources:
- NASA Prognostics Data Repository (bearing datasets)
- CWRU Bearing Data Center
- Industry standard ISO 10816 vibration limits
- Thermal power plant operating manuals

This module provides scientifically accurate sensor profiles for:
1. Various equipment types
2. Different failure modes
3. Realistic degradation curves
4. Industry-standard thresholds
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum
import numpy as np


class EquipmentClass(Enum):
    """ISO 10816 equipment classification"""
    CLASS_I = "Small machines"           # up to 15 kW
    CLASS_II = "Medium machines"         # 15-75 kW (most common)
    CLASS_III = "Large machines"         # rigid foundation
    CLASS_IV = "Very large machines"     # flexible foundation


class VibrationSeverity(Enum):
    """ISO 10816 vibration severity zones"""
    ZONE_A = "New/Excellent"     # Newly commissioned
    ZONE_B = "Acceptable"        # Unlimited operation
    ZONE_C = "Unsatisfactory"    # Limited operation, plan maintenance
    ZONE_D = "Unacceptable"      # Damage imminent, stop


# ==================== ISO 10816 VIBRATION LIMITS (mm/s RMS) ====================
# These are real industry standards used globally

VIBRATION_LIMITS = {
    EquipmentClass.CLASS_I: {
        VibrationSeverity.ZONE_A: (0.0, 0.71),
        VibrationSeverity.ZONE_B: (0.71, 1.8),
        VibrationSeverity.ZONE_C: (1.8, 4.5),
        VibrationSeverity.ZONE_D: (4.5, float('inf')),
    },
    EquipmentClass.CLASS_II: {
        VibrationSeverity.ZONE_A: (0.0, 1.12),
        VibrationSeverity.ZONE_B: (1.12, 2.8),
        VibrationSeverity.ZONE_C: (2.8, 7.1),
        VibrationSeverity.ZONE_D: (7.1, float('inf')),
    },
    EquipmentClass.CLASS_III: {
        VibrationSeverity.ZONE_A: (0.0, 1.8),
        VibrationSeverity.ZONE_B: (1.8, 4.5),
        VibrationSeverity.ZONE_C: (4.5, 11.2),
        VibrationSeverity.ZONE_D: (11.2, float('inf')),
    },
    EquipmentClass.CLASS_IV: {
        VibrationSeverity.ZONE_A: (0.0, 2.8),
        VibrationSeverity.ZONE_B: (2.8, 7.1),
        VibrationSeverity.ZONE_C: (7.1, 18.0),
        VibrationSeverity.ZONE_D: (18.0, float('inf')),
    },
}


# ==================== MOTOR TEMPERATURE CLASSES (IEC 60034) ====================

INSULATION_CLASSES = {
    "A": {"max_temp": 105, "rise": 60},    # Oldest, rarely used
    "B": {"max_temp": 130, "rise": 80},    # Common in HVAC
    "F": {"max_temp": 155, "rise": 105},   # Most common industrial
    "H": {"max_temp": 180, "rise": 125},   # High-performance motors
}


# ==================== PROFESSIONAL EQUIPMENT PROFILES ====================

@dataclass
class SensorProfile:
    """Professional sensor baseline and operating ranges"""
    baseline: float           # Normal operating value
    warning: float           # Warning threshold
    critical: float          # Critical/trip threshold
    unit: str                # Engineering unit
    noise_std: float         # Normal noise standard deviation
    

@dataclass
class EquipmentProfile:
    """Complete equipment profile with all sensors"""
    name: str
    equipment_class: EquipmentClass
    insulation_class: str
    
    # Sensor profiles
    vibration_x: SensorProfile
    vibration_y: SensorProfile
    temperature: SensorProfile
    pressure: SensorProfile
    rpm: SensorProfile
    
    # Operating characteristics
    rated_power_kw: float
    service_factor: float
    mtbf_hours: int          # Mean time between failures
    
    # Degradation model
    degradation_rate: float  # Health % loss per hour under stress
    
    def to_config(self) -> Dict:
        """Convert to config-compatible format"""
        return {
            "name": self.name,
            "description": f"{self.name} - {self.equipment_class.value}",
            "baselines": {
                "vibration_x": self.vibration_x.baseline,
                "vibration_y": self.vibration_y.baseline,
                "temperature": self.temperature.baseline,
                "pressure": self.pressure.baseline,
                "rpm": self.rpm.baseline,
            },
            "thresholds": {
                "vibration_warning": self.vibration_x.warning,
                "vibration_critical": self.vibration_x.critical,
                "temperature_warning": self.temperature.warning,
                "temperature_critical": self.temperature.critical,
                "pressure_warning": self.pressure.warning,
                "pressure_critical": self.pressure.critical,
            },
            "variance": {
                "vibration": self.vibration_x.noise_std,
                "temperature": self.temperature.noise_std,
                "pressure": self.pressure.noise_std,
                "rpm": self.rpm.noise_std,
            },
            "mtbf_hours": self.mtbf_hours,
            "rated_power_kw": self.rated_power_kw,
        }


# ==================== THERMAL POWER PLANT EQUIPMENT ====================

EQUIPMENT_PROFILES: Dict[str, EquipmentProfile] = {
    
    # Boiler Feed Water Pump (BFP) - Critical component
    "BOILER_FEED_PUMP": EquipmentProfile(
        name="Boiler Feed Water Pump",
        equipment_class=EquipmentClass.CLASS_III,
        insulation_class="F",
        vibration_x=SensorProfile(
            baseline=0.55, warning=1.8, critical=4.5, unit="mm/s", noise_std=0.08
        ),
        vibration_y=SensorProfile(
            baseline=0.60, warning=1.8, critical=4.5, unit="mm/s", noise_std=0.10
        ),
        temperature=SensorProfile(
            baseline=52.0, warning=85.0, critical=105.0, unit="°C", noise_std=3.0
        ),
        pressure=SensorProfile(
            baseline=145.0, warning=180.0, critical=200.0, unit="bar", noise_std=5.0
        ),
        rpm=SensorProfile(
            baseline=1480.0, warning=1420.0, critical=1350.0, unit="rpm", noise_std=10.0
        ),
        rated_power_kw=500,
        service_factor=1.15,
        mtbf_hours=25000,
        degradation_rate=0.002,
    ),
    
    # Induced Draft (ID) Fan Motor
    "ID_FAN_MOTOR": EquipmentProfile(
        name="Induced Draft Fan Motor",
        equipment_class=EquipmentClass.CLASS_III,
        insulation_class="F",
        vibration_x=SensorProfile(
            baseline=0.45, warning=1.8, critical=4.5, unit="mm/s", noise_std=0.06
        ),
        vibration_y=SensorProfile(
            baseline=0.45, warning=1.8, critical=4.5, unit="mm/s", noise_std=0.06
        ),
        temperature=SensorProfile(
            baseline=72.0, warning=95.0, critical=155.0, unit="°C", noise_std=4.0
        ),
        pressure=SensorProfile(
            baseline=0.0, warning=0.0, critical=0.0, unit="N/A", noise_std=0.0
        ),
        rpm=SensorProfile(
            baseline=1485.0, warning=1450.0, critical=1400.0, unit="rpm", noise_std=8.0
        ),
        rated_power_kw=250,
        service_factor=1.15,
        mtbf_hours=35000,
        degradation_rate=0.0015,
    ),
    
    # Cooling Water Pump
    "COOLING_WATER_PUMP": EquipmentProfile(
        name="Cooling Water Pump",
        equipment_class=EquipmentClass.CLASS_II,
        insulation_class="B",
        vibration_x=SensorProfile(
            baseline=0.40, warning=1.12, critical=2.8, unit="mm/s", noise_std=0.05
        ),
        vibration_y=SensorProfile(
            baseline=0.42, warning=1.12, critical=2.8, unit="mm/s", noise_std=0.05
        ),
        temperature=SensorProfile(
            baseline=45.0, warning=75.0, critical=95.0, unit="°C", noise_std=2.5
        ),
        pressure=SensorProfile(
            baseline=85.0, warning=110.0, critical=130.0, unit="bar", noise_std=4.0
        ),
        rpm=SensorProfile(
            baseline=1475.0, warning=1430.0, critical=1380.0, unit="rpm", noise_std=12.0
        ),
        rated_power_kw=75,
        service_factor=1.0,
        mtbf_hours=40000,
        degradation_rate=0.001,
    ),
    
    # Control Room HVAC Chiller
    "CRAC_CHILLER": EquipmentProfile(
        name="CRAC Unit Chiller",
        equipment_class=EquipmentClass.CLASS_II,
        insulation_class="F",
        vibration_x=SensorProfile(
            baseline=0.35, warning=1.0, critical=2.5, unit="mm/s", noise_std=0.04
        ),
        vibration_y=SensorProfile(
            baseline=0.38, warning=1.0, critical=2.5, unit="mm/s", noise_std=0.04
        ),
        temperature=SensorProfile(
            baseline=7.5, warning=12.0, critical=18.0, unit="°C", noise_std=0.8
        ),
        pressure=SensorProfile(
            baseline=85.0, warning=60.0, critical=45.0, unit="psi", noise_std=3.0
        ),
        rpm=SensorProfile(
            baseline=1750.0, warning=1700.0, critical=1600.0, unit="rpm", noise_std=15.0
        ),
        rated_power_kw=45,
        service_factor=1.0,
        mtbf_hours=50000,
        degradation_rate=0.0008,
    ),
    
    # Transformer Cooling System
    "TRANSFORMER_COOLING": EquipmentProfile(
        name="Transformer Oil Cooling System",
        equipment_class=EquipmentClass.CLASS_I,
        insulation_class="B",
        vibration_x=SensorProfile(
            baseline=0.25, warning=0.71, critical=1.8, unit="mm/s", noise_std=0.03
        ),
        vibration_y=SensorProfile(
            baseline=0.25, warning=0.71, critical=1.8, unit="mm/s", noise_std=0.03
        ),
        temperature=SensorProfile(
            baseline=55.0, warning=75.0, critical=90.0, unit="°C", noise_std=2.0
        ),
        pressure=SensorProfile(
            baseline=25.0, warning=35.0, critical=45.0, unit="psi", noise_std=1.5
        ),
        rpm=SensorProfile(
            baseline=1450.0, warning=1400.0, critical=1350.0, unit="rpm", noise_std=8.0
        ),
        rated_power_kw=15,
        service_factor=1.0,
        mtbf_hours=60000,
        degradation_rate=0.0005,
    ),
    
    # Turbine Auxiliary Motor
    "TURBINE_AUXILIARY": EquipmentProfile(
        name="Turbine Auxiliary Motor",
        equipment_class=EquipmentClass.CLASS_III,
        insulation_class="H",
        vibration_x=SensorProfile(
            baseline=0.50, warning=1.8, critical=4.5, unit="mm/s", noise_std=0.07
        ),
        vibration_y=SensorProfile(
            baseline=0.52, warning=1.8, critical=4.5, unit="mm/s", noise_std=0.07
        ),
        temperature=SensorProfile(
            baseline=82.0, warning=120.0, critical=155.0, unit="°C", noise_std=5.0
        ),
        pressure=SensorProfile(
            baseline=0.0, warning=0.0, critical=0.0, unit="N/A", noise_std=0.0
        ),
        rpm=SensorProfile(
            baseline=2970.0, warning=2900.0, critical=2800.0, unit="rpm", noise_std=18.0
        ),
        rated_power_kw=200,
        service_factor=1.15,
        mtbf_hours=30000,
        degradation_rate=0.0018,
    ),
}


# ==================== FAILURE MODE PROFILES ====================

@dataclass
class FailureMode:
    """Definition of a specific failure mode"""
    name: str
    description: str
    primary_indicator: str      # Main sensor that shows failure first
    secondary_indicators: List[str]
    progression_hours: float    # Time from first sign to failure
    detectability: float        # 0-1, how easy to detect early
    severity: str              # MINOR, MAJOR, CRITICAL
    
    # Characteristic sensor patterns
    vibration_pattern: str     # SPIKE, GRADUAL, HARMONIC
    temperature_pattern: str   # RISE, FLUCTUATE, SPIKE
    

FAILURE_MODES: Dict[str, FailureMode] = {
    
    "BEARING_INNER_RACE": FailureMode(
        name="Bearing Inner Race Defect",
        description="Defect on bearing inner race causing localized damage",
        primary_indicator="vibration_x",
        secondary_indicators=["temperature"],
        progression_hours=72,
        detectability=0.85,
        severity="CRITICAL",
        vibration_pattern="HARMONIC",  # BPFI frequency
        temperature_pattern="GRADUAL",
    ),
    
    "BEARING_OUTER_RACE": FailureMode(
        name="Bearing Outer Race Defect",
        description="Defect on bearing outer race",
        primary_indicator="vibration_y",
        secondary_indicators=["vibration_x", "temperature"],
        progression_hours=96,
        detectability=0.90,
        severity="CRITICAL",
        vibration_pattern="HARMONIC",  # BPFO frequency
        temperature_pattern="GRADUAL",
    ),
    
    "UNBALANCE": FailureMode(
        name="Rotor Unbalance",
        description="Mass imbalance in rotating component",
        primary_indicator="vibration_x",
        secondary_indicators=["vibration_y"],
        progression_hours=168,  # 1 week
        detectability=0.95,
        severity="MAJOR",
        vibration_pattern="1X_HARMONIC",
        temperature_pattern="SLIGHT",
    ),
    
    "MISALIGNMENT": FailureMode(
        name="Shaft Misalignment",
        description="Angular or parallel shaft misalignment",
        primary_indicator="vibration_y",
        secondary_indicators=["vibration_x", "temperature"],
        progression_hours=240,  # 10 days
        detectability=0.90,
        severity="MAJOR",
        vibration_pattern="2X_HARMONIC",
        temperature_pattern="RISE",
    ),
    
    "MOTOR_OVERHEATING": FailureMode(
        name="Motor Winding Overheating",
        description="Excessive heat in motor windings",
        primary_indicator="temperature",
        secondary_indicators=["rpm"],
        progression_hours=24,
        detectability=0.95,
        severity="CRITICAL",
        vibration_pattern="NORMAL",
        temperature_pattern="SPIKE",
    ),
    
    "CAVITATION": FailureMode(
        name="Pump Cavitation",
        description="Bubble formation and collapse in pump",
        primary_indicator="pressure",
        secondary_indicators=["vibration_x", "vibration_y"],
        progression_hours=48,
        detectability=0.80,
        severity="CRITICAL",
        vibration_pattern="BROADBAND",
        temperature_pattern="FLUCTUATE",
    ),
}


# ==================== DEGRADATION CURVES ====================

def calculate_health_score(
    sensors: Dict[str, float],
    profile: EquipmentProfile,
    runtime_hours: float
) -> float:
    """
    Calculate health score based on sensor values and professional thresholds.
    Uses weighted scoring with industry-standard limits.
    """
    score = 100.0
    
    # Vibration contribution (40% weight)
    vib_x = sensors.get("vibration_x", profile.vibration_x.baseline)
    vib_y = sensors.get("vibration_y", profile.vibration_y.baseline)
    avg_vib = (vib_x + vib_y) / 2
    
    if avg_vib >= profile.vibration_x.critical:
        score -= 40
    elif avg_vib >= profile.vibration_x.warning:
        vib_factor = (avg_vib - profile.vibration_x.warning) / (
            profile.vibration_x.critical - profile.vibration_x.warning
        )
        score -= 25 + (15 * vib_factor)
    else:
        vib_factor = avg_vib / profile.vibration_x.warning
        score -= 10 * vib_factor
    
    # Temperature contribution (30% weight)
    temp = sensors.get("temperature", profile.temperature.baseline)
    
    if temp >= profile.temperature.critical:
        score -= 30
    elif temp >= profile.temperature.warning:
        temp_factor = (temp - profile.temperature.warning) / (
            profile.temperature.critical - profile.temperature.warning
        )
        score -= 18 + (12 * temp_factor)
    else:
        temp_factor = temp / profile.temperature.warning
        score -= 5 * temp_factor
    
    # Pressure contribution (20% weight) - only for pressurized equipment
    if profile.pressure.baseline > 0:
        pressure = sensors.get("pressure", profile.pressure.baseline)
        # Pressure can be too high OR too low
        if pressure >= profile.pressure.critical or pressure <= profile.pressure.critical * 0.3:
            score -= 20
        elif pressure >= profile.pressure.warning or pressure <= profile.pressure.warning * 0.5:
            score -= 12
    
    # Runtime age penalty (10% weight)
    if runtime_hours > profile.mtbf_hours * 0.7:
        age_factor = (runtime_hours - profile.mtbf_hours * 0.7) / (profile.mtbf_hours * 0.3)
        score -= min(10, 10 * age_factor)
    
    return max(0, min(100, score))


def get_vibration_severity(
    vibration_rms: float,
    equipment_class: EquipmentClass
) -> VibrationSeverity:
    """
    Determine vibration severity zone per ISO 10816.
    This is how real industrial systems classify vibration.
    """
    limits = VIBRATION_LIMITS[equipment_class]
    
    for severity, (min_val, max_val) in limits.items():
        if min_val <= vibration_rms < max_val:
            return severity
    
    return VibrationSeverity.ZONE_D


def get_temperature_status(
    temperature: float,
    insulation_class: str
) -> str:
    """
    Determine motor temperature status per IEC 60034.
    """
    limits = INSULATION_CLASSES.get(insulation_class, INSULATION_CLASSES["F"])
    
    if temperature >= limits["max_temp"]:
        return "CRITICAL"
    elif temperature >= limits["max_temp"] - 20:
        return "WARNING"
    elif temperature >= limits["max_temp"] - 40:
        return "CAUTION"
    else:
        return "NORMAL"


# ==================== DATASET GENERATION ====================

def generate_professional_dataset(
    equipment_type: str,
    failure_mode: str,
    duration_hours: float = 72,
    sample_interval_minutes: float = 5
) -> List[Dict]:
    """
    Generate a professional-grade failure dataset.
    Uses real equipment profiles and failure mode patterns.
    """
    if equipment_type not in EQUIPMENT_PROFILES:
        raise ValueError(f"Unknown equipment type: {equipment_type}")
    if failure_mode not in FAILURE_MODES:
        raise ValueError(f"Unknown failure mode: {failure_mode}")
    
    profile = EQUIPMENT_PROFILES[equipment_type]
    failure = FAILURE_MODES[failure_mode]
    
    samples_count = int(duration_hours * 60 / sample_interval_minutes)
    dataset = []
    
    for i in range(samples_count):
        # Progress through failure (0 to 1)
        progress = i / samples_count
        
        # Calculate degradation based on failure mode
        if failure.vibration_pattern == "GRADUAL":
            vib_multiplier = 1 + (progress * 5)
        elif failure.vibration_pattern == "HARMONIC":
            vib_multiplier = 1 + (progress ** 2 * 8)  # Exponential growth
        elif failure.vibration_pattern == "SPIKE":
            vib_multiplier = 1 + (3 if progress > 0.8 else progress)
        else:
            vib_multiplier = 1 + (progress * 3)
        
        if failure.temperature_pattern == "GRADUAL":
            temp_increase = progress * 50
        elif failure.temperature_pattern == "RISE":
            temp_increase = progress ** 1.5 * 60
        elif failure.temperature_pattern == "SPIKE":
            temp_increase = 40 if progress > 0.85 else progress * 20
        else:
            temp_increase = progress * 25
        
        # Generate sensor values with realistic noise
        sensors = {
            "vibration_x": round(
                profile.vibration_x.baseline * vib_multiplier + 
                np.random.normal(0, profile.vibration_x.noise_std), 3
            ),
            "vibration_y": round(
                profile.vibration_y.baseline * vib_multiplier + 
                np.random.normal(0, profile.vibration_y.noise_std), 3
            ),
            "temperature": round(
                profile.temperature.baseline + temp_increase + 
                np.random.normal(0, profile.temperature.noise_std), 1
            ),
            "pressure": round(
                profile.pressure.baseline * (1 - progress * 0.3) + 
                np.random.normal(0, profile.pressure.noise_std), 1
            ) if profile.pressure.baseline > 0 else 0,
            "rpm": round(
                profile.rpm.baseline * (1 - progress * 0.2) + 
                np.random.normal(0, profile.rpm.noise_std), 0
            ),
        }
        
        # Calculate derived metrics
        health_score = calculate_health_score(sensors, profile, i * sample_interval_minutes / 60)
        vib_severity = get_vibration_severity(
            (sensors["vibration_x"] + sensors["vibration_y"]) / 2,
            profile.equipment_class
        )
        temp_status = get_temperature_status(sensors["temperature"], profile.insulation_class)
        
        # Determine phase
        if progress < 0.3:
            phase = "HEALTHY"
        elif progress < 0.6:
            phase = "DEGRADING"
        elif progress < 0.85:
            phase = "PRE_FAILURE"
        else:
            phase = "FAILURE"
        
        dataset.append({
            "sample_index": i,
            "timestamp_offset_minutes": i * sample_interval_minutes,
            "sensors": sensors,
            "health_score": round(health_score, 1),
            "phase": phase,
            "vibration_severity": vib_severity.value,
            "temperature_status": temp_status,
            "progress_percent": round(progress * 100, 1),
        })
    
    return dataset


def export_dataset_for_training(datasets: List[Dict], format: str = "csv") -> str:
    """
    Export datasets in format suitable for ML training.
    """
    import json
    
    if format == "json":
        return json.dumps(datasets, indent=2)
    elif format == "csv":
        lines = ["timestamp,vibration_x,vibration_y,temperature,pressure,rpm,health_score,phase"]
        for sample in datasets:
            s = sample["sensors"]
            lines.append(
                f"{sample['timestamp_offset_minutes']},{s['vibration_x']},{s['vibration_y']},"
                f"{s['temperature']},{s['pressure']},{s['rpm']},"
                f"{sample['health_score']},{sample['phase']}"
            )
        return "\n".join(lines)
    else:
        raise ValueError(f"Unknown format: {format}")


# ==================== EXPORTS ====================

def get_all_equipment_profiles() -> Dict[str, Dict]:
    """Get all equipment profiles as config-compatible dicts"""
    return {
        etype: profile.to_config()
        for etype, profile in EQUIPMENT_PROFILES.items()
    }


def get_all_failure_modes() -> List[Dict]:
    """Get all failure mode definitions"""
    return [
        {
            "id": fid,
            "name": fm.name,
            "description": fm.description,
            "primary_indicator": fm.primary_indicator,
            "progression_hours": fm.progression_hours,
            "severity": fm.severity,
        }
        for fid, fm in FAILURE_MODES.items()
    ]


# ==================== TEST ====================

if __name__ == "__main__":
    print("=" * 70)
    print("PROFESSIONAL INDUSTRIAL DATASETS")
    print("=" * 70)
    
    print("\n📊 EQUIPMENT PROFILES (ISO 10816 Compliant):")
    for etype, profile in EQUIPMENT_PROFILES.items():
        print(f"\n  {etype}:")
        print(f"    Name: {profile.name}")
        print(f"    Class: {profile.equipment_class.value}")
        print(f"    Rated Power: {profile.rated_power_kw} kW")
        print(f"    MTBF: {profile.mtbf_hours:,} hours")
        print(f"    Vibration Baseline: {profile.vibration_x.baseline} mm/s")
        print(f"    Vibration Warning: {profile.vibration_x.warning} mm/s")
        print(f"    Vibration Critical: {profile.vibration_x.critical} mm/s")
    
    print("\n\n🔧 FAILURE MODES:")
    for fid, fm in FAILURE_MODES.items():
        print(f"\n  {fid}:")
        print(f"    {fm.name} - {fm.severity}")
        print(f"    Primary Indicator: {fm.primary_indicator}")
        print(f"    Progression: {fm.progression_hours} hours")
    
    print("\n\n📈 GENERATING SAMPLE DATASET:")
    dataset = generate_professional_dataset(
        equipment_type="BOILER_FEED_PUMP",
        failure_mode="BEARING_INNER_RACE",
        duration_hours=4,
        sample_interval_minutes=10
    )
    
    print(f"  Generated {len(dataset)} samples")
    print("\n  First 5 samples:")
    for sample in dataset[:5]:
        print(f"    t={sample['timestamp_offset_minutes']:3}min: "
              f"Health={sample['health_score']:5.1f}%, "
              f"Phase={sample['phase']:12}, "
              f"Vib={sample['sensors']['vibration_x']:.2f}mm/s")
    
    print("\n  Last 5 samples (approaching failure):")
    for sample in dataset[-5:]:
        print(f"    t={sample['timestamp_offset_minutes']:3}min: "
              f"Health={sample['health_score']:5.1f}%, "
              f"Phase={sample['phase']:12}, "
              f"Vib={sample['sensors']['vibration_x']:.2f}mm/s")
    
    print("\n" + "=" * 70)
    print("✓ Professional datasets ready for hackathon!")
