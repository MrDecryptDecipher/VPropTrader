"""Drift Detection using Statistical Tests"""

import numpy as np
from scipy import stats
from typing import Optional, Dict
from loguru import logger
from app.core import settings


class DriftDetector:
    """Detect distribution drift in features"""
    
    def __init__(self):
        self.threshold = settings.drift_threshold
        self.reference_data = None
        self.drift_detected = False
    
    def set_reference(self, data: np.ndarray):
        """Set reference distribution"""
        self.reference_data = data
        logger.info(f"Reference distribution set: {len(data)} samples")
    
    def detect_drift(self, recent_data: np.ndarray) -> Dict:
        """
        Detect drift using Kolmogorov-Smirnov test
        
        Args:
            recent_data: Recent feature samples
        
        Returns:
            Dict with drift detection results
        """
        if self.reference_data is None:
            logger.warning("No reference data set for drift detection")
            return {"drift_detected": False, "reason": "no_reference"}
        
        try:
            # Perform KS test for each feature
            n_features = min(self.reference_data.shape[1], recent_data.shape[1])
            
            ks_statistics = []
            p_values = []
            
            for i in range(n_features):
                ref_feature = self.reference_data[:, i]
                recent_feature = recent_data[:, i]
                
                # KS test
                ks_stat, p_value = stats.ks_2samp(ref_feature, recent_feature)
                
                ks_statistics.append(ks_stat)
                p_values.append(p_value)
            
            # Average KS statistic
            avg_ks = np.mean(ks_statistics)
            min_p_value = np.min(p_values)
            
            # Drift detected if p-value < 0.01 (significant difference)
            drift_detected = min_p_value < 0.01 or avg_ks > self.threshold
            
            self.drift_detected = drift_detected
            
            result = {
                "drift_detected": drift_detected,
                "avg_ks_statistic": float(avg_ks),
                "min_p_value": float(min_p_value),
                "threshold": self.threshold,
                "n_features_tested": n_features,
            }
            
            if drift_detected:
                logger.warning(f"⚠ Drift detected! KS: {avg_ks:.4f}, p-value: {min_p_value:.6f}")
            else:
                logger.debug(f"No drift detected. KS: {avg_ks:.4f}, p-value: {min_p_value:.6f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return {"drift_detected": False, "error": str(e)}
    
    def should_retrain(self) -> bool:
        """Check if retraining should be triggered"""
        return self.drift_detected


# Global drift detector instance
drift_detector = DriftDetector()
