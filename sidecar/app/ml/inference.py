"""ML Inference Engine - Combines all models for predictions"""

import numpy as np
from typing import Dict, Optional, Tuple
from loguru import logger
import time

from app.ml.random_forest import random_forest
from app.ml.lstm_model import lstm_model
from app.ml.onnx_exporter import onnx_exporter
from app.features.feature_engineer import feature_engineer


class MLInference:
    """ML inference engine combining all models"""
    
    def __init__(self):
        self.models_loaded = False
        self.use_onnx = False
        self.model_version = 1
    
    def load_models(self, prefer_onnx: bool = True) -> bool:
        """
        Load all trained models
        
        Args:
            prefer_onnx: If True, try to load ONNX models first
        
        Returns:
            True if models loaded successfully
        """
        try:
            # Try ONNX first if preferred
            if prefer_onnx:
                onnx_loaded = onnx_exporter.load_onnx_models()
                onnx_exporter.load_metadata()
                
                if onnx_loaded:
                    self.use_onnx = True
                    self.models_loaded = True
                    logger.info("✓ Using ONNX models for inference")
                    
                    # Benchmark inference speed
                    benchmark = onnx_exporter.benchmark_inference_speed(n_iterations=100)
                    if benchmark.get('total_avg_ms', 999) < 1.0:
                        logger.info(f"✓ ONNX inference validated: {benchmark['total_avg_ms']:.4f} ms")
                    
                    return True
            
            # Fallback to native models
            logger.info("Loading native Python models...")
            rf_loaded = random_forest.load()
            lstm_loaded = lstm_model.load()
            
            self.models_loaded = rf_loaded and lstm_loaded
            self.use_onnx = False
            
            if self.models_loaded:
                logger.info("✓ All ML models loaded successfully (native)")
            else:
                logger.warning("⚠ Some models failed to load - using defaults")
            
            return self.models_loaded
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def swap_models_atomic(self) -> bool:
        """
        Atomically swap to newly trained models
        
        This is called after retraining to load new ONNX models
        without disrupting inference
        
        Returns:
            True if swap successful
        """
        try:
            logger.info("Performing atomic model swap...")
            
            # Load new ONNX models
            new_onnx_loaded = onnx_exporter.load_onnx_models()
            
            if not new_onnx_loaded:
                logger.error("Failed to load new ONNX models")
                return False
            
            # Validate inference speed
            benchmark = onnx_exporter.benchmark_inference_speed(n_iterations=100)
            
            if benchmark.get('total_avg_ms', 999) > 5.0:
                logger.error(f"New models too slow: {benchmark['total_avg_ms']:.4f} ms")
                return False
            
            # Atomic swap - just update the flag
            self.use_onnx = True
            self.model_version += 1
            
            logger.info(f"✓ Model swap successful - now using version {self.model_version}")
            logger.info(f"  Inference time: {benchmark.get('total_avg_ms', 0):.4f} ms")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during model swap: {e}", exc_info=True)
            return False
    
    def predict_sync(
        self,
        symbol: str,
        features: Dict
    ) -> Dict:
        """
        Synchronous prediction for backtesting
        
        Args:
            symbol: Trading symbol
            features: Pre-computed features dict
        
        Returns:
            Dict with predictions
        """
        try:
            # Simple prediction based on features
            # For backtesting, we use a simplified approach
            
            # Default predictions
            predictions = {
                'rf_pwin': 0.55,  # Default 55% win probability
                'lstm_direction': 0,
                'confidence': 0.6
            }
            
            # Adjust based on trend strength
            ema_slope = features.get('ema_slope', 0)
            if abs(ema_slope) > 0.001:
                predictions['rf_pwin'] = 0.60
                predictions['confidence'] = 0.7
            
            return predictions
            
        except Exception as e:
            logger.debug(f"Prediction error: {e}")
            return {'rf_pwin': 0.5, 'lstm_direction': 0, 'confidence': 0.5}
    
    async def predict(
        self, 
        symbol: str,
        feature_sequence: Optional[np.ndarray] = None
    ) -> Optional[Dict]:
        """
        Run inference on all models
        
        Args:
            symbol: Trading symbol
            feature_sequence: Optional pre-computed feature sequence for LSTM
        
        Returns:
            Dict with predictions from all models
        """
        try:
            start_time = time.perf_counter()
            
            # Extract current features
            features_dict = await feature_engineer.extract_features(symbol)
            if not features_dict:
                logger.warning(f"Could not extract features for {symbol}")
                return None
            
            # Get feature vector
            feature_vector = await feature_engineer.get_feature_vector(symbol)
            if feature_vector is None:
                return None
            
            predictions = {}
            
            # Random Forest prediction
            if self.use_onnx and onnx_exporter.rf_session is not None:
                try:
                    # ONNX inference
                    X = feature_vector.reshape(1, -1).astype(np.float32)
                    rf_pwin = onnx_exporter.predict_rf_onnx(X)[0]
                    predictions['rf_pwin'] = float(rf_pwin)
                    
                    logger.debug(f"RF ONNX P(win) for {symbol}: {rf_pwin:.4f}")
                    
                except Exception as e:
                    logger.error(f"RF ONNX prediction error: {e}")
                    predictions['rf_pwin'] = 0.5
            elif random_forest.model is not None:
                try:
                    # Native sklearn inference
                    X = feature_vector.reshape(1, -1)
                    rf_pwin = random_forest.predict_proba(X)[0]
                    predictions['rf_pwin'] = float(rf_pwin)
                    
                    logger.debug(f"RF P(win) for {symbol}: {rf_pwin:.4f}")
                    
                except Exception as e:
                    logger.error(f"RF prediction error: {e}")
                    predictions['rf_pwin'] = 0.5
            else:
                predictions['rf_pwin'] = 0.5
            
            # LSTM prediction
            if feature_sequence is not None:
                if self.use_onnx and onnx_exporter.lstm_session is not None:
                    try:
                        # ONNX inference
                        seq = feature_sequence.astype(np.float32)
                        volatility, direction = onnx_exporter.predict_lstm_onnx(seq)
                        
                        predictions['lstm_sigma'] = float(volatility)
                        predictions['lstm_direction'] = float(direction)
                        
                        logger.debug(f"LSTM ONNX for {symbol}: vol={volatility:.6f}, dir={direction:.4f}")
                        
                    except Exception as e:
                        logger.error(f"LSTM ONNX prediction error: {e}")
                        predictions['lstm_sigma'] = 0.01
                        predictions['lstm_direction'] = 0.0
                elif lstm_model.model is not None:
                    try:
                        # Native PyTorch inference
                        volatility, direction = lstm_model.predict(feature_sequence)
                        
                        predictions['lstm_sigma'] = float(volatility)
                        predictions['lstm_direction'] = float(direction)
                        
                        logger.debug(f"LSTM for {symbol}: vol={volatility:.6f}, dir={direction:.4f}")
                        
                    except Exception as e:
                        logger.error(f"LSTM prediction error: {e}")
                        predictions['lstm_sigma'] = 0.01
                        predictions['lstm_direction'] = 0.0
                else:
                    predictions['lstm_sigma'] = features_dict.get('realized_vol', 0.01)
                    predictions['lstm_direction'] = features_dict.get('ema_slope', 0.0) * 100
            else:
                # Use realized volatility from features as fallback
                predictions['lstm_sigma'] = features_dict.get('realized_vol', 0.01)
                predictions['lstm_direction'] = features_dict.get('ema_slope', 0.0) * 100
            
            # Add regime
            predictions['regime'] = self._get_regime(features_dict)
            
            # Add raw features for logging
            predictions['features'] = features_dict
            
            # Add inference time
            inference_time_ms = (time.perf_counter() - start_time) * 1000
            predictions['inference_time_ms'] = inference_time_ms
            
            if inference_time_ms > 1.0:
                logger.warning(f"Slow inference for {symbol}: {inference_time_ms:.4f} ms")
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in ML inference: {e}", exc_info=True)
            return None
    
    def _get_regime(self, features: Dict) -> str:
        """Determine market regime from features"""
        if features.get('regime_trend', 0) > 0.5:
            return 'trend_up'
        elif features.get('regime_revert', 0) > 0.5:
            return 'revert'
        elif features.get('regime_choppy', 0) > 0.5:
            return 'choppy'
        else:
            return 'unknown'
    
    def calculate_q_star(
        self,
        p_win: float,
        expected_rr: float,
        vol_forecast: float,
        entropy: float = 0.5
    ) -> float:
        """
        Calculate Q* confidence score
        
        Q* = (P_win * RR - (1 - P_win)) * (1 - entropy/H_max) / vol_forecast
        
        Args:
            p_win: Probability of winning (from RF)
            expected_rr: Expected risk-reward ratio
            vol_forecast: Volatility forecast (from LSTM)
            entropy: Signal entropy (0 = certain, 1 = random)
        
        Returns:
            Q* score (0-10 scale)
        """
        try:
            # Edge calculation
            edge = p_win * expected_rr - (1 - p_win)
            
            # Entropy penalty (H_max = log(2) for binary outcome)
            h_max = np.log(2)
            entropy_penalty = 1 - (entropy / h_max)
            
            # Risk adjustment
            if vol_forecast > 0:
                risk_adj = edge * entropy_penalty / vol_forecast
            else:
                risk_adj = 0
            
            # Scale to 0-10
            q_star = risk_adj * 100
            
            # Clip to reasonable range
            q_star = np.clip(q_star, 0, 10)
            
            return float(q_star)
            
        except Exception as e:
            logger.error(f"Error calculating Q*: {e}")
            return 0.0
    
    def calculate_es95(
        self,
        position_size: float,
        stop_loss_distance: float,
        vol_forecast: float
    ) -> float:
        """
        Calculate Expected Shortfall at 95% confidence
        
        Args:
            position_size: Position size in lots
            stop_loss_distance: Distance to stop loss in price units
            vol_forecast: Volatility forecast
        
        Returns:
            ES95 in dollars
        """
        try:
            # Simplified ES95 calculation
            # In production, use historical simulation or parametric method
            
            # Assume normal distribution
            # ES95 ≈ mean + 1.645 * std (for 95% confidence)
            
            # Expected loss at stop
            expected_loss = position_size * stop_loss_distance
            
            # Volatility adjustment
            vol_adjusted_loss = expected_loss * (1 + 1.645 * vol_forecast)
            
            return float(vol_adjusted_loss)
            
        except Exception as e:
            logger.error(f"Error calculating ES95: {e}")
            return 0.0


# Global inference engine instance
ml_inference = MLInference()
