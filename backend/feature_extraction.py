"""
Feature Extraction Module for Industrial Predictive Maintenance

Extracts vibration health indicators aligned with NASA IMS research.
These features are used as input to XGBoost models for failure prediction.
"""

import numpy as np
from typing import Dict, List, Optional
from scipy import stats as scipy_stats


def extract_features(sensor_data: np.ndarray) -> Dict[str, float]:
    """
    Extract vibration health features from sensor data.
    
    NASA-aligned features:
    - RMS: Overall vibration energy
    - Kurtosis: Peak indicator (increases with damage)
    - Crest Factor: Peak-to-RMS ratio
    - Spectral Energy: Frequency domain energy
    
    Args:
        sensor_data: 1D array of vibration samples
        
    Returns:
        Dictionary of feature values
    """
    data = np.asarray(sensor_data).flatten()
    
    if len(data) == 0:
        return _empty_features()
    
    # ==================== TIME DOMAIN FEATURES ====================
    
    # RMS (Root Mean Square) - overall vibration level
    rms = np.sqrt(np.mean(data**2))
    
    # Peak value
    peak = np.max(np.abs(data))
    
    # Peak-to-Peak
    peak_to_peak = np.max(data) - np.min(data)
    
    # Crest Factor - ratio of peak to RMS (increases with damage)
    crest_factor = peak / rms if rms > 0 else 0
    
    # Standard Deviation
    std_dev = np.std(data)
    
    # Kurtosis - measure of peakedness (>3 indicates damage)
    kurtosis = float(scipy_stats.kurtosis(data, fisher=True))  # Fisher = excess kurtosis
    
    # Skewness - asymmetry indicator
    skewness = float(scipy_stats.skew(data))
    
    # ==================== FREQUENCY DOMAIN FEATURES ====================
    
    # FFT
    fft_vals = np.fft.fft(data)
    fft_magnitude = np.abs(fft_vals[:len(data)//2])
    
    # Spectral Energy
    spectral_energy = np.sum(fft_magnitude**2) / len(data)
    
    # Mean Frequency
    freqs = np.fft.fftfreq(len(data))[:len(data)//2]
    if np.sum(fft_magnitude) > 0:
        mean_freq = np.sum(freqs * fft_magnitude) / np.sum(fft_magnitude)
    else:
        mean_freq = 0
    
    return {
        "rms": float(rms),
        "peak": float(peak),
        "peak_to_peak": float(peak_to_peak),
        "crest_factor": float(crest_factor),
        "std_dev": float(std_dev),
        "kurtosis": float(kurtosis),
        "skewness": float(skewness),
        "spectral_energy": float(spectral_energy),
        "mean_freq": float(mean_freq)
    }


def _empty_features() -> Dict[str, float]:
    """Return empty feature set for missing data."""
    return {
        "rms": 0.0,
        "peak": 0.0,
        "peak_to_peak": 0.0,
        "crest_factor": 0.0,
        "std_dev": 0.0,
        "kurtosis": 0.0,
        "skewness": 0.0,
        "spectral_energy": 0.0,
        "mean_freq": 0.0
    }


def features_to_array(features: Dict[str, float]) -> np.ndarray:
    """
    Convert feature dictionary to array for ML model input.
    
    Order matches XGBoost model training.
    """
    return np.array([
        features.get("rms", 0),
        features.get("kurtosis", 0),
        features.get("crest_factor", 0),
        features.get("spectral_energy", 0),
        features.get("peak_to_peak", 0),
        features.get("std_dev", 0)
    ])


def calculate_health_index(features: Dict[str, float], 
                          baselines: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate health index (0-100) from features.
    
    100 = Perfectly healthy
    0 = Imminent failure
    
    Args:
        features: Current feature values
        baselines: Healthy baseline values (optional)
    """
    if baselines is None:
        # Default healthy baselines (from NASA IMS healthy state)
        baselines = {
            "rms": 0.08,
            "kurtosis": 3.0,
            "crest_factor": 3.5,
            "spectral_energy": 100
        }
    
    # Calculate deviation from baseline
    deviations = []
    
    # RMS deviation (higher = worse)
    if features.get("rms", 0) > 0 and baselines.get("rms", 0) > 0:
        rms_ratio = features["rms"] / baselines["rms"]
        rms_penalty = max(0, min(1, (rms_ratio - 1) / 5))  # 0-1 scale
        deviations.append(rms_penalty)
    
    # Kurtosis deviation (higher = worse, >6 is bad)
    kurtosis = features.get("kurtosis", 3.0)
    kurtosis_penalty = max(0, min(1, (kurtosis - 3) / 10))
    deviations.append(kurtosis_penalty)
    
    # Crest factor deviation
    crest = features.get("crest_factor", 3.5)
    crest_penalty = max(0, min(1, (crest - 3.5) / 10))
    deviations.append(crest_penalty)
    
    if not deviations:
        return 100.0
    
    # Average penalty
    avg_penalty = np.mean(deviations)
    
    # Convert to health (0-100)
    health = (1 - avg_penalty) * 100
    
    return max(0, min(100, health))


def calculate_failure_risk(features: Dict[str, float]) -> float:
    """
    Calculate failure risk (0-1) from features.
    
    0 = No risk
    1 = Imminent failure
    """
    health = calculate_health_index(features)
    return (100 - health) / 100


# ==================== FEATURE THRESHOLDS ====================

# Based on ISO 10816 vibration severity standards
VIBRATION_THRESHOLDS = {
    "rms": {
        "good": 0.1,
        "satisfactory": 0.2,
        "unsatisfactory": 0.4,
        "unacceptable": 0.7
    },
    "kurtosis": {
        "normal": 4.0,
        "warning": 6.0,
        "critical": 10.0
    },
    "crest_factor": {
        "normal": 4.0,
        "warning": 6.0,
        "critical": 8.0
    }
}


def get_feature_status(features: Dict[str, float]) -> Dict[str, str]:
    """
    Get status labels for each feature based on thresholds.
    """
    status = {}
    
    # RMS status
    rms = features.get("rms", 0)
    if rms < VIBRATION_THRESHOLDS["rms"]["good"]:
        status["rms"] = "GOOD"
    elif rms < VIBRATION_THRESHOLDS["rms"]["satisfactory"]:
        status["rms"] = "SATISFACTORY"
    elif rms < VIBRATION_THRESHOLDS["rms"]["unsatisfactory"]:
        status["rms"] = "UNSATISFACTORY"
    else:
        status["rms"] = "UNACCEPTABLE"
    
    # Kurtosis status
    kurtosis = features.get("kurtosis", 3)
    if kurtosis < VIBRATION_THRESHOLDS["kurtosis"]["normal"]:
        status["kurtosis"] = "NORMAL"
    elif kurtosis < VIBRATION_THRESHOLDS["kurtosis"]["warning"]:
        status["kurtosis"] = "WARNING"
    else:
        status["kurtosis"] = "CRITICAL"
    
    # Crest factor status
    crest = features.get("crest_factor", 3)
    if crest < VIBRATION_THRESHOLDS["crest_factor"]["normal"]:
        status["crest_factor"] = "NORMAL"
    elif crest < VIBRATION_THRESHOLDS["crest_factor"]["warning"]:
        status["crest_factor"] = "WARNING"
    else:
        status["crest_factor"] = "CRITICAL"
    
    return status


# ==================== SELF TEST ====================
if __name__ == "__main__":
    print("=" * 60)
    print("FEATURE EXTRACTION MODULE TEST")
    print("=" * 60)
    
    # Generate synthetic healthy data
    np.random.seed(42)
    healthy_data = np.random.normal(0, 0.05, 1000)
    
    # Generate synthetic degraded data
    degraded_data = np.random.normal(0, 0.15, 1000)
    degraded_data += np.sin(np.linspace(0, 10, 1000)) * 0.2  # Add impulse
    
    print("\n--- Healthy Signal ---")
    healthy_features = extract_features(healthy_data)
    for k, v in healthy_features.items():
        print(f"  {k}: {v:.4f}")
    print(f"  Health Index: {calculate_health_index(healthy_features):.1f}%")
    print(f"  Failure Risk: {calculate_failure_risk(healthy_features):.2f}")
    
    print("\n--- Degraded Signal ---")
    degraded_features = extract_features(degraded_data)
    for k, v in degraded_features.items():
        print(f"  {k}: {v:.4f}")
    print(f"  Health Index: {calculate_health_index(degraded_features):.1f}%")
    print(f"  Failure Risk: {calculate_failure_risk(degraded_features):.2f}")
    
    print("\n--- Status Labels ---")
    status = get_feature_status(degraded_features)
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
