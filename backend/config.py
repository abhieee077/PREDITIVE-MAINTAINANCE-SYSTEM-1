"""
Production Configuration Management
Centralized configuration for industrial predictive maintenance system
"""
from pathlib import Path
from typing import Dict, Tuple
import os

class Config:
    """Production-grade configuration with environment-specific settings"""
    
    # ==================== ALERT THRESHOLDS (WITH HYSTERESIS) ====================
    # HYSTERESIS: Separate trigger/clear thresholds to prevent alert flapping
    # Trigger threshold is stricter; clear threshold has 5-10% buffer
    
    # RUL (Remaining Useful Life) thresholds in hours  
    RUL_CRITICAL_TRIGGER = 24     # Critical alert triggers when RUL < 24 hours
    RUL_CRITICAL_CLEAR = 28       # Critical alert clears when RUL > 28 hours (17% buffer)
    RUL_WARNING_TRIGGER = 48      # Warning alert triggers when RUL < 48 hours
    RUL_WARNING_CLEAR = 52        # Warning alert clears when RUL > 52 hours (8% buffer)
    
    # Legacy compat (used by some components)
    RUL_CRITICAL_HOURS = 24
    RUL_WARNING_HOURS = 48
    
    # Health score thresholds with hysteresis (0-100)
    HEALTH_CRITICAL_TRIGGER = 30   # Trigger when health < 30%
    HEALTH_CRITICAL_CLEAR = 35     # Clear when health > 35%
    HEALTH_WARNING_TRIGGER = 50    # Trigger when health < 50%
    HEALTH_WARNING_CLEAR = 55      # Clear when health > 55%
    
    # Legacy compat
    HEALTH_CRITICAL_THRESHOLD = 30
    HEALTH_WARNING_THRESHOLD = 50
    
    # ==================== ALERT PERSISTENCE WINDOWS ====================
    # Condition must persist for X seconds before alert is raised
    # Prevents false alarms from transient sensor spikes
    PERSISTENCE_WINDOWS = {
        "critical_rul": 30,       # 30 seconds sustained for critical RUL
        "warning_rul": 60,        # 60 seconds for warning RUL
        "low_health_critical": 30, # 30 seconds for critical health
        "low_health_warning": 60,  # 60 seconds for warning health  
        "anomaly_detected": 45    # 45 seconds for anomaly confirmation
    }
    
    # ==================== ALERT RATE LIMITING ====================
    MAX_ALERTS_PER_MACHINE_PER_MINUTE = 3   # Prevent alert flooding
    MAX_TOTAL_ALERTS_PER_MINUTE = 10        # System-wide limit
    
    # ==================== MULTI-SENSOR CONFIRMATION ====================
    # For critical alerts, require multiple sensors to confirm
    MULTI_SENSOR_REQUIRED_FOR_CRITICAL = True
    MIN_DEGRADED_SENSORS_FOR_CRITICAL = 2   # At least 2 sensors must be degraded
    
    # Sensor degradation thresholds (for multi-sensor check)
    SENSOR_DEGRADATION_THRESHOLDS = {
        "vibration_x": 1.5,    # mm/s - above this = degraded
        "vibration_y": 1.5,    # mm/s
        "temperature": 85.0,   # °C - context-dependent, use motor baseline
        "pressure_low": 90.0,  # PSI - below this = degraded
        "rpm_low": 1350        # RPM - below this = degraded
    }
    
    # ==================== EVALUATION WINDOWS ====================
    # Sliding window aggregation before alert creation
    # PURPOSE: Control trade-offs between precision, lead time, false alarms
    #
    # METRIC PROTECTION:
    # - Precision: Reject if pct_above < required (filters noise spikes)
    # - Recall: Accumulate slow degradation over window duration
    # - Lead Time: Shorter windows for critical (faster response)
    # - False Alarms: Require positive trend + ratio gating
    
    EVALUATION_WINDOWS = {
        "warning_rul": {
            "duration_seconds": 60,       # Aggregate over 60 seconds
            "required_pct_above": 0.55,   # 55% of samples must exceed threshold
            "require_worsening_trend": True,
            "risk_threshold": 0.4         # Risk score threshold (0-1)
        },
        "critical_rul": {
            "duration_seconds": 45,       # Shorter for urgency
            "required_pct_above": 0.65,   # 65% for higher precision
            "require_worsening_trend": True,
            "risk_threshold": 0.6
        },
        "low_health_warning": {
            "duration_seconds": 60,
            "required_pct_above": 0.55,
            "require_worsening_trend": True,
            "risk_threshold": 0.4
        },
        "low_health_critical": {
            "duration_seconds": 45,
            "required_pct_above": 0.65,
            "require_worsening_trend": True,
            "risk_threshold": 0.6
        },
        "anomaly_detected": {
            "duration_seconds": 90,       # Longer for anomalies (transients common)
            "required_pct_above": 0.50,   # 50% (anomalies can be sporadic)
            "require_worsening_trend": False,  # Anomalies may plateau
            "risk_threshold": 0.3
        }
    }
    
    # Anomaly detection
    ANOMALY_CONTAMINATION = 0.1   # Expected % of anomalies in data
    ANOMALY_CRITICAL_SCORE = 5.0  # Score above which anomaly is critical
    
    # ==================== ML STABILIZATION ====================
    # Exponential Moving Average (EMA) smoothing
    EMA_ALPHA = 0.1  # Lower = more smoothing, higher = more responsive
    
    # Minimum interval between RUL predictions (seconds)
    MIN_PREDICTION_INTERVAL_SECONDS = 300  # 5 minutes
    
    # RUL constraints
    MAX_RUL_HOURS = 144  # 6 days maximum RUL
    MIN_RUL_HOURS = 0    # Minimum RUL
    
    # ==================== DATA RETENTION ====================
    # Sensor history
    MAX_SENSOR_HISTORY_SAMPLES = 200  # Per machine
    
    # Health history for forecasting
    MAX_HEALTH_HISTORY_SAMPLES = 100  # Per machine
    
    # Alert retention
    ALERT_RETENTION_DAYS = 90  # Keep active/resolved alerts for 90 days
    
    # Log retention
    LOG_RETENTION_DAYS = 730  # Keep logs for 2 years (compliance)
    
    # ==================== DATABASE ====================
    # Database path
    DB_PATH = str(Path(__file__).parent / "data" / "maintenance.db")
    
    # Connection pool settings
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    
    # ==================== SENSOR SIMULATION ====================
    # Degradation phase thresholds (runtime hours)
    DEGRADATION_PHASES: Dict[str, Tuple[int, int]] = {
        "HEALTHY": (0, 500),        # 0-500 hours: Normal operation
        "DEGRADING": (500, 800),    # 500-800 hours: Gradual degradation
        "PRE_FAILURE": (800, 950),  # 800-950 hours: Accelerated degradation
        "FAILURE": (950, 1000)      # 950-1000 hours: Critical failure imminent
    }
    
    # Sensor baseline values (healthy state)
    SENSOR_BASELINES = {
        "vibration_x": 0.5,      # mm/s
        "vibration_y": 0.5,      # mm/s
        "temperature": 70.0,     # Celsius
        "pressure": 100.0,       # PSI
        "rpm": 1500.0            # Revolutions per minute
    }
    
    # Sensor physical limits (for validation)
    SENSOR_LIMITS = {
        "vibration_x": (0.0, 10.0),
        "vibration_y": (0.0, 10.0),
        "temperature": (-50.0, 200.0),
        "pressure": (0.0, 200.0),
        "rpm": (0.0, 3000.0)
    }
    
    # Degradation factors per phase
    DEGRADATION_FACTORS = {
        "HEALTHY": 1.0,
        "DEGRADING": 1.3,
        "PRE_FAILURE": 1.8,
        "FAILURE": 2.5
    }
    
    # ==================== THERMAL POWER PLANT CONFIG ====================
    # Plant identification
    PLANT_NAME = "Main Power Block"
    PLANT_TYPE = "Thermal Power Plant"
    
    # Machine type definitions with realistic thermal power plant profiles
    # OPTIMIZED: Added warning thresholds for earlier detection (improved lead time)
    MACHINE_TYPES = {
        "FEEDWATER_PUMP": {
            "name": "Feedwater Pump",
            "description": "High-pressure pump feeding water to boiler",
            "baselines": {
                "vibration_x": 0.55,      # mm/s - centrifugal pump typical
                "vibration_y": 0.60,      # mm/s - slightly higher due to fluid
                "temperature": 52.0,      # °C - synchronized with professional_datasets
                "pressure": 145.0,        # PSI - high discharge pressure
                "rpm": 1480.0             # 4-pole motor at 50Hz
            },
            "variance": {
                "vibration": 0.10,        # Reduced for lower false alarms
                "temperature": 3.0,
                "pressure": 5.0,
                "rpm": 10.0
            },
            "warning_thresholds": {       # NEW: Earlier detection for lead time
                "vibration": 1.2,         # mm/s - early warning
                "temperature": 70.0,      # °C - early warning
                "pressure_low": 120.0,    # PSI - early warning
                "pressure_high": 165.0    # PSI - early warning
            },
            "critical_thresholds": {
                "vibration": 2.5,         # mm/s - bearing damage
                "temperature": 85.0,      # °C - seal failure risk
                "pressure_low": 100.0,    # PSI - cavitation
                "pressure_high": 180.0    # PSI - overpressure
            }
        },
        "ID_FAN_MOTOR": {
            "name": "ID Fan Motor",
            "description": "Induced draft fan motor for flue gas extraction",
            "baselines": {
                "vibration_x": 0.45,      # mm/s - large motor, well-balanced
                "vibration_y": 0.45,      # mm/s
                "temperature": 72.0,      # °C - hot motor windings
                "pressure": 0.0,          # N/A for fan motor
                "rpm": 1485.0             # Slight slip from synchronous
            },
            "variance": {
                "vibration": 0.06,        # Reduced for lower false alarms
                "temperature": 4.0,
                "pressure": 0.0,
                "rpm": 8.0
            },
            "warning_thresholds": {       # NEW: Earlier detection for lead time
                "vibration": 1.5,         # mm/s - early warning
                "temperature": 85.0,      # °C - early warning
                "rpm_low": 1450.0         # Early warning
            },
            "critical_thresholds": {
                "vibration": 3.0,         # mm/s
                "temperature": 95.0,      # °C - winding insulation limit
                "rpm_low": 1400.0         # Below this = problem
            }
        },
        "HVAC_CHILLER": {
            "name": "HVAC Chiller",
            "description": "Central cooling chiller for control room HVAC",
            "baselines": {
                "vibration_x": 0.35,      # mm/s - precision equipment
                "vibration_y": 0.38,      # mm/s
                "temperature": 7.5,       # °C - synchronized with professional_datasets
                "pressure": 85.0,         # PSI - refrigerant pressure
                "rpm": 1750.0             # Compressor speed
            },
            "variance": {
                "vibration": 0.04,        # Reduced for precision equipment
                "temperature": 1.0,
                "pressure": 3.0,
                "rpm": 15.0
            },
            "warning_thresholds": {       # NEW: Earlier detection for lead time
                "vibration": 0.8,         # mm/s - early warning
                "temperature_high": 10.0, # °C - early warning
                "pressure_low": 70.0,     # PSI - early warning
                "pressure_high": 100.0    # PSI - early warning
            },
            "critical_thresholds": {
                "vibration": 1.5,         # mm/s - precision system
                "temperature_high": 15.0, # °C - cooling capacity loss
                "pressure_low": 60.0,     # PSI - refrigerant leak
                "pressure_high": 120.0    # PSI - overcharge
            }
        },
        "BOILER_FEED_MOTOR": {
            "name": "Boiler Feed Motor",
            "description": "Main boiler feedwater pump motor",
            "baselines": {
                "vibration_x": 0.50,      # mm/s
                "vibration_y": 0.52,      # mm/s
                "temperature": 82.0,      # °C - high load motor
                "pressure": 0.0,          # N/A - motor only
                "rpm": 2970.0             # 2-pole motor, high speed
            },
            "variance": {
                "vibration": 0.08,        # Reduced for lower false alarms
                "temperature": 5.0,
                "pressure": 0.0,
                "rpm": 15.0
            },
            "warning_thresholds": {       # NEW: Earlier detection for lead time
                "vibration": 1.3,         # mm/s - early warning
                "temperature": 95.0,      # °C - early warning
                "rpm_low": 2950.0         # Early warning
            },
            "critical_thresholds": {
                "vibration": 2.8,         # mm/s
                "temperature": 105.0,     # °C - Class F insulation
                "rpm_low": 2900.0
            }
        }
    }
    
    # Machine ID to type mapping - 4-MACHINE ARCHITECTURE
    # M-001: NORMAL (Stable baseline - no alerts expected)
    # M-002: NORMAL (Slight noise - occasional auto-cleared warnings)
    # M-003: FAILING (NASA IMS degradation - demonstrates failure progression)
    # M-004: MANUAL (Operator-controlled - responds to commands)
    MACHINE_ASSIGNMENTS = {
        "M-001": "FEEDWATER_PUMP",   # NORMAL - stable baseline
        "M-002": "FEEDWATER_PUMP",   # NORMAL - with slight noise
        "M-003": "HVAC_CHILLER",     # FAILING - uses NASA degradation data
        "M-004": "BOILER_FEED_MOTOR" # MANUAL - operator control
    }
    
    # Machine modes for 4-machine architecture
    # NORMAL: Stable operation with baseline values
    # FAILING: Progressive degradation using NASA IMS data
    # MANUAL: Accepts operator input/overrides
    MACHINE_MODES = {
        "M-001": "NORMAL",           # Stable baseline (judges see healthy)
        "M-002": "NORMAL",           # Slight noise (auto-cleared warnings)
        "M-003": "FAILING",          # NASA degradation curve
        "M-004": "MANUAL"            # Operator control
    }
    
    # NASA IMS Dataset Configuration
    NASA_DATASET_PATH = r"C:\Users\abhij\Downloads\IMS\IMS\1st_test\1st_test"
    
    # Machine mode behavior parameters
    MACHINE_MODE_CONFIG = {
        "NORMAL": {
            "degradation_progress": 0.0,   # No degradation
            "noise_level": 0.05,           # 5% sensor noise
            "add_occasional_spike": False  # No transient spikes
        },
        "NORMAL_NOISY": {
            "degradation_progress": 0.0,
            "noise_level": 0.15,           # 15% noise
            "add_occasional_spike": True   # Occasional spikes (auto-clear)
        },
        "FAILING": {
            "degradation_start": 0.0,      # Start at healthy
            "degradation_rate": 0.001,     # Progress per second
            "use_nasa_data": True          # Use real NASA data
        },
        "MANUAL": {
            "default_to_healthy": True,    # Start healthy
            "accept_overrides": True       # Accept API overrides
        }
    }

    
    # ==================== API SETTINGS ====================
    # Rate limiting
    API_RATE_LIMIT_PER_MINUTE = 100
    
    # CORS settings
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
    
    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
    
    # ==================== LOGGING ====================
    # Log file settings
    LOG_DIR = str(Path(__file__).parent / "logs")
    LOG_FILE = "maintenance.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # ==================== OPERATOR SETTINGS ====================
    # Default operator ID for system actions
    SYSTEM_OPERATOR_ID = "SYSTEM"
    
    # Require operator notes minimum length
    MIN_RESOLUTION_NOTES_LENGTH = 10
    MIN_ROOT_CAUSE_LENGTH = 5
    
    # ==================== ALERT LIFECYCLE ====================
    # Valid alert state transitions
    VALID_ALERT_TRANSITIONS = {
        "ACTIVE": ["ACKNOWLEDGED"],
        "ACKNOWLEDGED": ["IN_PROGRESS", "RESOLVED"],
        "IN_PROGRESS": ["RESOLVED"],
        "RESOLVED": ["LOGGED"],
        "LOGGED": []  # Terminal state
    }
    
    # Alert types
    ALERT_TYPES = {
        "critical_rul": "Critical RUL",
        "warning_rul": "Warning RUL",
        "anomaly_detected": "Anomaly Detected",
        "low_health": "Low Health Score",
        "sensor_failure": "Sensor Failure"
    }
    
    # Severity levels
    SEVERITY_LEVELS = ["info", "warning", "critical"]
    
    # ==================== ENVIRONMENT-SPECIFIC ====================
    @classmethod
    def get_env(cls) -> str:
        """Get current environment"""
        return os.getenv("MAINTENANCE_ENV", "development")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.get_env() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.get_env() == "development"
    
    # ==================== HELPER METHODS ====================
    @classmethod
    def get_degradation_phase(cls, runtime_hours: float) -> str:
        """Determine degradation phase based on runtime hours"""
        for phase, (min_hours, max_hours) in cls.DEGRADATION_PHASES.items():
            if min_hours <= runtime_hours < max_hours:
                return phase
        return "FAILURE"  # Beyond max hours
    
    @classmethod
    def get_degradation_factor(cls, phase: str) -> float:
        """Get degradation multiplier for a phase"""
        return cls.DEGRADATION_FACTORS.get(phase, 1.0)
    
    @classmethod
    def validate_sensor_value(cls, sensor_name: str, value: float) -> bool:
        """Validate sensor value is within physical limits"""
        if sensor_name not in cls.SENSOR_LIMITS:
            return True  # Unknown sensor, assume valid
        
        min_val, max_val = cls.SENSOR_LIMITS[sensor_name]
        return min_val <= value <= max_val
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        # Create logs directory
        Path(cls.LOG_DIR).mkdir(parents=True, exist_ok=True)
        
        # Create data directory for database
        Path(cls.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)"""
        print("=" * 60)
        print("PRODUCTION CONFIGURATION")
        print("=" * 60)
        print(f"Environment: {cls.get_env()}")
        print(f"Database: {cls.DB_PATH}")
        print(f"Log Directory: {cls.LOG_DIR}")
        print(f"\nAlert Thresholds:")
        print(f"  RUL Critical: < {cls.RUL_CRITICAL_HOURS} hours")
        print(f"  RUL Warning: < {cls.RUL_WARNING_HOURS} hours")
        print(f"  Health Critical: < {cls.HEALTH_CRITICAL_THRESHOLD}%")
        print(f"\nML Stabilization:")
        print(f"  EMA Alpha: {cls.EMA_ALPHA}")
        print(f"  Prediction Interval: {cls.MIN_PREDICTION_INTERVAL_SECONDS}s")
        print(f"\nData Retention:")
        print(f"  Alerts: {cls.ALERT_RETENTION_DAYS} days")
        print(f"  Logs: {cls.LOG_RETENTION_DAYS} days")
        print("=" * 60)


# Initialize directories on import
Config.ensure_directories()


if __name__ == "__main__":
    # Test configuration
    Config.print_config()
    
    # Test helper methods
    print("\nTesting helper methods:")
    print(f"Phase at 100 hours: {Config.get_degradation_phase(100)}")
    print(f"Phase at 600 hours: {Config.get_degradation_phase(600)}")
    print(f"Phase at 900 hours: {Config.get_degradation_phase(900)}")
    
    print(f"\nDegradation factor for HEALTHY: {Config.get_degradation_factor('HEALTHY')}")
    print(f"Degradation factor for CRITICAL: {Config.get_degradation_factor('PRE_FAILURE')}")
    
    print(f"\nValidate temperature 75°C: {Config.validate_sensor_value('temperature', 75)}")
    print(f"Validate temperature 250°C: {Config.validate_sensor_value('temperature', 250)}")
