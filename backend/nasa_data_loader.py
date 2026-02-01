"""
NASA IMS Bearing Dataset Loader

Loads and processes data from NASA's IMS Bearing Dataset for machine failure simulation.
Dataset contains vibration data from 4 bearings running to failure over 35 days.

Reference: https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/
"""

import os
import glob
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NASADataLoader:
    """
    Loads NASA IMS Bearing Dataset for realistic failure simulation.
    
    Dataset structure:
    - 2156 files over 35 days
    - 8 columns (bearings) per file
    - 20481 samples per channel at 20 kHz
    - Bearing 3 (column 2, 0-indexed) failed on Nov 25, 2003
    """
    
    def __init__(self, dataset_path: str):
        """Initialize loader with path to 1st_test folder."""
        self.dataset_path = dataset_path
        self.files: List[str] = []
        self.failed_bearing = 2  # Column index (0-based) of failed bearing
        self.total_files = 0
        self._load_file_list()
        
    def _load_file_list(self):
        """Load and sort all data files chronologically."""
        if not os.path.exists(self.dataset_path):
            logger.warning(f"NASA dataset path not found: {self.dataset_path}")
            return
            
        # Get all files (no extension, just timestamps)
        all_files = glob.glob(os.path.join(self.dataset_path, "*"))
        
        # Filter out directories, keep only files
        self.files = sorted([f for f in all_files if os.path.isfile(f)])
        self.total_files = len(self.files)
        
        if self.total_files > 0:
            logger.info(f"✓ NASA IMS dataset loaded: {self.total_files} files")
        else:
            logger.warning(f"No files found in {self.dataset_path}")
    
    def load_file(self, file_index: int) -> Optional[np.ndarray]:
        """
        Load a single data file.
        
        Returns:
            np.ndarray: Shape (20481, 8) - vibration samples for 8 bearings
        """
        if not self.files or file_index >= len(self.files):
            return None
            
        try:
            filepath = self.files[file_index]
            data = np.loadtxt(filepath, delimiter='\t')
            return data
        except Exception as e:
            logger.error(f"Error loading NASA file: {e}")
            return None
    
    def get_file_at_progress(self, progress: float) -> Optional[np.ndarray]:
        """
        Get data file at specified progress through the dataset.
        
        Args:
            progress: 0.0 (healthy) to 1.0 (failure)
            
        Returns:
            Vibration data array or None
        """
        if not self.files:
            return None
            
        # Map progress to file index
        file_index = int(progress * (self.total_files - 1))
        file_index = max(0, min(file_index, self.total_files - 1))
        
        return self.load_file(file_index)
    
    def get_bearing_data(self, file_index: int, bearing: int = None) -> Optional[np.ndarray]:
        """
        Get vibration data for specific bearing.
        
        Args:
            file_index: Index of file to load
            bearing: Bearing index (0-7), or None for failed bearing
            
        Returns:
            1D array of vibration samples
        """
        data = self.load_file(file_index)
        if data is None:
            return None
            
        if bearing is None:
            bearing = self.failed_bearing
            
        if bearing < 0 or bearing >= data.shape[1]:
            return None
            
        return data[:, bearing]
    
    def get_degradation_features(self, progress: float) -> Dict[str, float]:
        """
        Extract features from data at given degradation progress.
        
        Args:
            progress: 0.0 = healthy, 1.0 = failure
            
        Returns:
            Dictionary of extracted features
        """
        data = self.get_file_at_progress(progress)
        
        if data is None:
            # Return synthetic degraded features if no data
            return self._synthetic_degradation(progress)
            
        # Get failed bearing data
        bearing_data = data[:, self.failed_bearing]
        
        # Extract features
        return self._extract_features(bearing_data)
    
    def _extract_features(self, data: np.ndarray) -> Dict[str, float]:
        """Extract vibration health features from raw data."""
        from scipy import stats as scipy_stats
        
        # RMS (Root Mean Square)
        rms = np.sqrt(np.mean(data**2))
        
        # Kurtosis (peakedness - increases with damage)
        kurtosis = float(scipy_stats.kurtosis(data))
        
        # Crest Factor (peak-to-RMS ratio)
        peak = np.max(np.abs(data))
        crest_factor = peak / rms if rms > 0 else 0
        
        # Spectral Energy (via FFT)
        fft_vals = np.fft.fft(data)
        spectral_energy = np.sum(np.abs(fft_vals)**2) / len(data)
        
        # Peak-to-Peak
        peak_to_peak = np.max(data) - np.min(data)
        
        # Standard deviation
        std_dev = np.std(data)
        
        return {
            "rms": float(rms),
            "kurtosis": float(kurtosis),
            "crest_factor": float(crest_factor),
            "spectral_energy": float(spectral_energy),
            "peak_to_peak": float(peak_to_peak),
            "std_dev": float(std_dev)
        }
    
    def _synthetic_degradation(self, progress: float) -> Dict[str, float]:
        """
        Generate synthetic degradation features when real data unavailable.
        Based on typical bearing degradation curves.
        """
        # Baseline healthy values
        base_rms = 0.08
        base_kurtosis = 3.0  # Normal distribution
        base_crest = 3.5
        base_energy = 100
        
        # Exponential degradation curve (accelerates near failure)
        degradation = np.exp(progress * 3) - 1  # 0 at start, ~20 at failure
        degradation_factor = 1 + degradation * 0.5
        
        return {
            "rms": base_rms * degradation_factor,
            "kurtosis": base_kurtosis + (progress * 10),  # Kurtosis increases
            "crest_factor": base_crest * (1 + progress * 2),
            "spectral_energy": base_energy * degradation_factor,
            "peak_to_peak": 0.2 * degradation_factor,
            "std_dev": 0.05 * degradation_factor
        }
    
    def get_healthy_baseline(self) -> Dict[str, float]:
        """Get baseline features from early (healthy) dataset."""
        return self.get_degradation_features(0.0)
    
    def get_failure_state(self) -> Dict[str, float]:
        """Get features from end (failure) of dataset."""
        return self.get_degradation_features(1.0)


# Global instance
_nasa_loader: Optional[NASADataLoader] = None


def get_nasa_loader() -> NASADataLoader:
    """Get or create global NASA data loader."""
    global _nasa_loader
    
    if _nasa_loader is None:
        # Try to find the dataset
        possible_paths = [
            r"C:\Users\abhij\Downloads\IMS\IMS\1st_test\1st_test",
            os.path.join(os.path.dirname(__file__), "data", "nasa_ims"),
            "./data/nasa_ims"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                _nasa_loader = NASADataLoader(path)
                break
        else:
            # Create with first path, will use synthetic data
            _nasa_loader = NASADataLoader(possible_paths[0])
            
    return _nasa_loader


# ==================== SELF TEST ====================
if __name__ == "__main__":
    print("=" * 60)
    print("NASA IMS DATASET LOADER TEST")
    print("=" * 60)
    
    loader = get_nasa_loader()
    
    print(f"\nDataset path: {loader.dataset_path}")
    print(f"Total files: {loader.total_files}")
    
    if loader.total_files > 0:
        print("\n--- Healthy Baseline (0%) ---")
        healthy = loader.get_degradation_features(0.0)
        for k, v in healthy.items():
            print(f"  {k}: {v:.4f}")
        
        print("\n--- Mid Degradation (50%) ---")
        mid = loader.get_degradation_features(0.5)
        for k, v in mid.items():
            print(f"  {k}: {v:.4f}")
        
        print("\n--- Failure State (100%) ---")
        failure = loader.get_degradation_features(1.0)
        for k, v in failure.items():
            print(f"  {k}: {v:.4f}")
        
        print("\n--- Feature Change Ratios ---")
        for k in healthy:
            if healthy[k] > 0:
                ratio = failure[k] / healthy[k]
                print(f"  {k}: {ratio:.2f}x increase")
    else:
        print("\nNo data files found - using synthetic features")
        synthetic = loader._synthetic_degradation(0.5)
        for k, v in synthetic.items():
            print(f"  {k}: {v:.4f}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
