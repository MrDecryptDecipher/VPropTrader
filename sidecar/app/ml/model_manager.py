"""Model Version Management and Atomic Swapping"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
import json

from app.core import settings
from app.ml.random_forest import random_forest
from app.ml.lstm_model import lstm_model
from app.ml.onnx_exporter import onnx_exporter
from app.ml.inference import ml_inference


class ModelManager:
    """Manages model versions and atomic swapping"""
    
    def __init__(self):
        self.model_dir = Path(settings.model_path)
        self.versions_dir = self.model_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_version_file = self.model_dir / "current_version.json"
        self.current_version = self._load_current_version()
    
    def _load_current_version(self) -> int:
        """Load current model version number"""
        if self.current_version_file.exists():
            try:
                with open(self.current_version_file, 'r') as f:
                    data = json.load(f)
                return data.get('version', 1)
            except Exception as e:
                logger.error(f"Error loading version: {e}")
        return 1
    
    def _save_current_version(self, version: int, metadata: Dict) -> bool:
        """Save current version info"""
        try:
            data = {
                'version': version,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata
            }
            with open(self.current_version_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving version: {e}")
            return False
    
    def create_version_snapshot(self) -> Optional[int]:
        """
        Create a snapshot of current models
        
        Returns:
            Version number of snapshot
        """
        try:
            new_version = self.current_version + 1
            version_dir = self.versions_dir / f"v{new_version}"
            version_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Creating model snapshot v{new_version}...")
            
            # Copy native models
            rf_path = Path(settings.model_path) / "random_forest_v4.pkl"
            lstm_path = Path(settings.model_path) / "lstm_2head.pt"
            
            if rf_path.exists():
                shutil.copy2(rf_path, version_dir / "random_forest_v4.pkl")
            
            if lstm_path.exists():
                shutil.copy2(lstm_path, version_dir / "lstm_2head.pt")
            
            # Copy ONNX models
            onnx_dir = Path(settings.model_path) / "onnx"
            if onnx_dir.exists():
                version_onnx_dir = version_dir / "onnx"
                version_onnx_dir.mkdir(exist_ok=True)
                
                for onnx_file in onnx_dir.glob("*.onnx"):
                    shutil.copy2(onnx_file, version_onnx_dir / onnx_file.name)
                
                # Copy metadata
                metadata_file = onnx_dir / "metadata.pkl"
                if metadata_file.exists():
                    shutil.copy2(metadata_file, version_onnx_dir / "metadata.pkl")
            
            # Save version metadata
            metadata = {
                'created_at': datetime.utcnow().isoformat(),
                'models': ['random_forest_v4', 'lstm_2head'],
                'onnx_exported': onnx_dir.exists(),
            }
            
            with open(version_dir / "version_info.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✓ Model snapshot v{new_version} created at {version_dir}")
            
            return new_version
            
        except Exception as e:
            logger.error(f"Error creating version snapshot: {e}", exc_info=True)
            return None
    
    def rollback_to_version(self, version: int) -> bool:
        """
        Rollback to a previous model version
        
        Args:
            version: Version number to rollback to
        
        Returns:
            True if rollback successful
        """
        try:
            version_dir = self.versions_dir / f"v{version}"
            
            if not version_dir.exists():
                logger.error(f"Version {version} not found")
                return False
            
            logger.info(f"Rolling back to model version {version}...")
            
            # Restore native models
            rf_backup = version_dir / "random_forest_v4.pkl"
            lstm_backup = version_dir / "lstm_2head.pt"
            
            if rf_backup.exists():
                shutil.copy2(rf_backup, Path(settings.model_path) / "random_forest_v4.pkl")
                logger.info("  ✓ Random Forest restored")
            
            if lstm_backup.exists():
                shutil.copy2(lstm_backup, Path(settings.model_path) / "lstm_2head.pt")
                logger.info("  ✓ LSTM restored")
            
            # Restore ONNX models
            version_onnx_dir = version_dir / "onnx"
            if version_onnx_dir.exists():
                onnx_dir = Path(settings.model_path) / "onnx"
                onnx_dir.mkdir(exist_ok=True)
                
                for onnx_file in version_onnx_dir.glob("*.onnx"):
                    shutil.copy2(onnx_file, onnx_dir / onnx_file.name)
                
                metadata_file = version_onnx_dir / "metadata.pkl"
                if metadata_file.exists():
                    shutil.copy2(metadata_file, onnx_dir / "metadata.pkl")
                
                logger.info("  ✓ ONNX models restored")
            
            # Update current version
            self.current_version = version
            self._save_current_version(version, {'rollback': True})
            
            # Reload models
            ml_inference.load_models(prefer_onnx=True)
            
            logger.info(f"✓ Rollback to v{version} complete")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}", exc_info=True)
            return False
    
    def retrain_and_swap(self, training_data: Dict) -> bool:
        """
        Complete retraining workflow with atomic swap
        
        Args:
            training_data: Dict with X, y for RF and sequences, targets for LSTM
        
        Returns:
            True if retrain and swap successful
        """
        try:
            logger.info("=== Starting model retraining workflow ===")
            
            # Step 1: Create snapshot of current models
            snapshot_version = self.create_version_snapshot()
            if snapshot_version is None:
                logger.error("Failed to create snapshot")
                return False
            
            # Step 2: Train new models
            logger.info("Training new models...")
            
            # Train Random Forest
            if 'rf_X' in training_data and 'rf_y' in training_data:
                rf_metrics = random_forest.train(
                    training_data['rf_X'],
                    training_data['rf_y']
                )
                if not rf_metrics:
                    logger.error("Random Forest training failed")
                    return False
                
                random_forest.save()
            
            # Train LSTM
            if 'lstm_sequences' in training_data and 'lstm_targets' in training_data:
                lstm_metrics = lstm_model.train(
                    training_data['lstm_sequences'],
                    training_data['lstm_targets']
                )
                if not lstm_metrics:
                    logger.error("LSTM training failed")
                    return False
                
                lstm_model.save()
            
            # Step 3: Export to ONNX
            logger.info("Exporting models to ONNX...")
            
            n_features = training_data.get('n_features', 50)
            sequence_length = training_data.get('sequence_length', 20)
            
            onnx_success = onnx_exporter.export_all_models(
                n_features=n_features,
                sequence_length=sequence_length
            )
            
            if not onnx_success:
                logger.error("ONNX export failed")
                # Rollback
                self.rollback_to_version(snapshot_version - 1)
                return False
            
            # Step 4: Validate inference speed
            logger.info("Validating inference speed...")
            benchmark = onnx_exporter.benchmark_inference_speed(n_iterations=1000)
            
            if benchmark.get('total_avg_ms', 999) > 5.0:
                logger.error(f"New models too slow: {benchmark['total_avg_ms']:.4f} ms")
                # Rollback
                self.rollback_to_version(snapshot_version - 1)
                return False
            
            # Step 5: Atomic swap
            logger.info("Performing atomic model swap...")
            swap_success = ml_inference.swap_models_atomic()
            
            if not swap_success:
                logger.error("Model swap failed")
                # Rollback
                self.rollback_to_version(snapshot_version - 1)
                return False
            
            # Step 6: Update version
            self.current_version = snapshot_version
            metadata = {
                'rf_metrics': rf_metrics if 'rf_X' in training_data else {},
                'lstm_metrics': lstm_metrics if 'lstm_sequences' in training_data else {},
                'benchmark': benchmark,
            }
            self._save_current_version(snapshot_version, metadata)
            
            logger.info(f"✓ Retrain and swap complete - now using v{snapshot_version}")
            logger.info(f"  Inference time: {benchmark.get('total_avg_ms', 0):.4f} ms")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in retrain workflow: {e}", exc_info=True)
            # Attempt rollback
            if snapshot_version:
                self.rollback_to_version(snapshot_version - 1)
            return False
    
    def list_versions(self) -> list:
        """List all available model versions"""
        versions = []
        
        for version_dir in sorted(self.versions_dir.glob("v*")):
            version_num = int(version_dir.name[1:])
            
            info_file = version_dir / "version_info.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info = json.load(f)
            else:
                info = {}
            
            versions.append({
                'version': version_num,
                'path': str(version_dir),
                'info': info,
                'is_current': version_num == self.current_version
            })
        
        return versions


# Global model manager instance
model_manager = ModelManager()
