# Integration Guide - New ML Components

This guide shows how to integrate the newly created components (GBT Meta-Learner, Thompson Sampling Bandit, and Adaptive Alpha Weighting) into the existing system.

---

## 1. Integrate GBT Meta-Learner into Inference

### File: `sidecar/app/ml/inference.py`

Add GBT refinement after RF and LSTM predictions:

```python
from app.ml.gbt_meta_learner import gbt_meta_learner

class MLInference:
    def __init__(self):
        # ... existing code ...
        self.use_gbt = False
    
    def load_models(self, prefer_onnx: bool = True) -> bool:
        # ... existing code ...
        
        # Load GBT meta-learner
        gbt_loaded = gbt_meta_learner.load()
        if gbt_loaded:
            self.use_gbt = True
            logger.info("✓ GBT meta-learner loaded")
        
        return self.models_loaded
    
    async def predict(self, symbol: str, feature_sequence: Optional[np.ndarray] = None) -> Optional[Dict]:
        # ... existing RF and LSTM predictions ...
        
        # Apply GBT refinement if available
        if self.use_gbt and gbt_meta_learner.model is not None:
            try:
                refined_pwin = gbt_meta_learner.refine_prediction(
                    rf_pwin=predictions['rf_pwin'],
                    lstm_vol=predictions['lstm_sigma'],
                    lstm_dir=predictions['lstm_direction'],
                    regime=predictions['regime'],
                    q_star=0.0,  # Will be calculated later
                    confidence=0.8,  # Placeholder
                    expected_rr=1.5  # Placeholder
                )
                predictions['rf_pwin_refined'] = refined_pwin
                predictions['rf_pwin_original'] = predictions['rf_pwin']
                predictions['rf_pwin'] = refined_pwin  # Use refined
                
                logger.debug(f"GBT refinement: {predictions['rf_pwin_original']:.4f} → {refined_pwin:.4f}")
            except Exception as e:
                logger.error(f"GBT refinement error: {e}")
        
        return predictions
```

---

## 2. Integrate Thompson Sampling Bandit into Scanner

### File: `sidecar/app/scanner/scanner.py`

Use bandit to select best alpha per regime:

```python
from app.scanner.alpha_selector import alpha_bandit

class GlobalScanner:
    def __init__(self):
        # ... existing code ...
        self.use_bandit = True
        
        # Load bandit state
        alpha_bandit.load()
    
    async def scan(self, existing_positions: Optional[List[str]] = None) -> List[TradingPlan]:
        # ... existing code ...
        
        for symbol in self.symbols:
            # ... feature extraction ...
            
            # Get regime
            regime = ml_predictions.get('regime', 'unknown')
            
            # Select alphas to evaluate
            if self.use_bandit and regime != 'unknown':
                # Use bandit to select top alphas for this regime
                available_alphas = list(self.alphas.keys())
                
                # Get top 3 alphas for this regime
                top_alphas = []
                for _ in range(min(3, len(available_alphas))):
                    selected = alpha_bandit.select_alpha(regime, available_alphas)
                    top_alphas.append(selected)
                    available_alphas.remove(selected)
                
                alphas_to_evaluate = {aid: self.alphas[aid] for aid in top_alphas}
            else:
                # Evaluate all alphas
                alphas_to_evaluate = self.alphas
            
            # Evaluate selected alphas
            for alpha_id, alpha in alphas_to_evaluate.items():
                # ... existing evaluation logic ...
```

### Update Bandit After Trades

Add to `sidecar/app/api/executions.py`:

```python
from app.scanner.alpha_selector import alpha_bandit

@router.post("/executions")
async def report_execution(execution: ExecutionReport):
    # ... existing code ...
    
    # Update bandit with trade outcome
    if execution.exit_reason and execution.pnl is not None:
        reward = 1.0 if execution.exit_reason in ['TP1', 'TP2'] else 0.0
        
        alpha_bandit.update(
            regime=execution.regime,
            alpha_id=execution.alpha_id,
            reward=reward
        )
        
        # Save bandit state periodically
        if random.random() < 0.1:  # 10% of the time
            alpha_bandit.save()
```

---

## 3. Integrate Adaptive Alpha Weighting

### File: `sidecar/app/scanner/scanner.py`

Apply weights when evaluating signals:

```python
from app.scanner.alpha_weighting import alpha_weighting

class GlobalScanner:
    def __init__(self):
        # ... existing code ...
        self.use_weighting = True
        
        # Load alpha weights
        alpha_weighting.load()
    
    async def scan(self, existing_positions: Optional[List[str]] = None) -> List[TradingPlan]:
        # ... existing code ...
        
        for alpha_id, alpha in alphas_to_evaluate.items():
            # Generate signal
            signal = alpha.generate_signal(features)
            if not signal:
                continue
            
            # Apply alpha weight
            if self.use_weighting:
                weight = alpha_weighting.get_weight(alpha_id)
                signal['confidence'] *= weight
                
                logger.debug(f"Applied weight {weight:.2f} to {alpha_id}")
            
            # ... rest of evaluation ...
```

### Update Weights After Trades

Add to `sidecar/app/api/executions.py`:

```python
from app.scanner.alpha_weighting import alpha_weighting
from app.data.correlation_engine import correlation_engine

@router.post("/executions")
async def report_execution(execution: ExecutionReport):
    # ... existing code ...
    
    # Record trade for alpha weighting
    if execution.exit_reason and execution.pnl is not None:
        alpha_weighting.record_trade(
            alpha_id=execution.alpha_id,
            pnl=execution.pnl,
            outcome=execution.exit_reason,
            risk_reward=execution.realized_rr or 1.0
        )
        
        # Update weights periodically (e.g., every 10 trades)
        if alpha_weighting.performance[execution.alpha_id]['trades'] % 10 == 0:
            # Get portfolio correlations
            portfolio_corr = correlation_engine.get_all_correlations()
            
            # Update weights
            alpha_weighting.update_weights(portfolio_corr)
            alpha_weighting.save()
```

---

## 4. Train GBT Meta-Learner

### File: `sidecar/app/ml/trainer.py`

Add GBT training to the retraining workflow:

```python
from app.ml.gbt_meta_learner import gbt_meta_learner

class ModelTrainer:
    async def train_all_models(self, use_atomic_swap: bool = True) -> Dict[str, Dict]:
        # ... existing code ...
        
        # Prepare GBT training data
        if data is not None:
            # Create meta-features from RF and LSTM predictions
            gbt_features = []
            gbt_labels = []
            
            for i in range(len(data['X'])):
                # Get RF prediction
                rf_pred = random_forest.predict_proba(data['X'][i:i+1])[0]
                
                # Get LSTM prediction (simplified)
                lstm_vol = 0.01  # Placeholder
                lstm_dir = 0.0   # Placeholder
                
                # Create meta-feature vector
                meta_features = [
                    rf_pred,
                    lstm_vol,
                    lstm_dir,
                    0.0,  # regime_trend
                    0.0,  # regime_revert
                    0.0,  # regime_choppy
                    7.0,  # q_star (placeholder)
                    0.8,  # confidence
                    1.5,  # expected_rr
                ]
                
                gbt_features.append(meta_features)
                gbt_labels.append(data['y'][i])
            
            # Train GBT
            logger.info("Training GBT meta-learner...")
            gbt_X = np.array(gbt_features)
            gbt_y = np.array(gbt_labels)
            
            gbt_metrics = gbt_meta_learner.train(gbt_X, gbt_y)
            if gbt_metrics:
                gbt_meta_learner.save()
                results['gbt_meta_learner'] = gbt_metrics
        
        return results
```

---

## 5. Update Main Application Startup

### File: `sidecar/app/main.py`

Load all components on startup:

```python
from app.ml.gbt_meta_learner import gbt_meta_learner
from app.scanner.alpha_selector import alpha_bandit
from app.scanner.alpha_weighting import alpha_weighting

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Sidecar AI Service...")
    
    # ... existing startup code ...
    
    # Load ML models
    ml_inference.load_models(prefer_onnx=True)
    
    # Load GBT meta-learner
    gbt_meta_learner.load()
    
    # Load bandit state
    alpha_bandit.load()
    
    # Load alpha weights
    alpha_weighting.load()
    
    logger.info("✓ All components loaded")
```

---

## 6. Testing the Integration

### Test GBT Meta-Learner

```python
# Test script
from app.ml.gbt_meta_learner import gbt_meta_learner
import numpy as np

# Create dummy data
X = np.random.randn(100, 9)
y = np.random.randint(0, 2, 100)

# Train
metrics = gbt_meta_learner.train(X, y)
print(f"GBT Metrics: {metrics}")

# Test prediction
test_X = np.random.randn(1, 9)
pred = gbt_meta_learner.predict(test_X)
print(f"Prediction: {pred}")
```

### Test Thompson Sampling Bandit

```python
from app.scanner.alpha_selector import alpha_bandit

# Select alpha
regime = 'trend_up'
alphas = ['momentum_v3', 'breakout_v2', 'volume_v1']
selected = alpha_bandit.select_alpha(regime, alphas)
print(f"Selected: {selected}")

# Update with reward
alpha_bandit.update(regime, selected, reward=1.0)

# Get statistics
stats = alpha_bandit.get_statistics(regime)
print(f"Stats: {stats}")
```

### Test Adaptive Alpha Weighting

```python
from app.scanner.alpha_weighting import alpha_weighting

# Record trades
alpha_weighting.record_trade('momentum_v3', pnl=10.0, outcome='TP1', risk_reward=2.0)
alpha_weighting.record_trade('momentum_v3', pnl=15.0, outcome='TP2', risk_reward=2.5)
alpha_weighting.record_trade('breakout_v2', pnl=-5.0, outcome='SL', risk_reward=0.5)

# Update weights
portfolio_corr = {'momentum_v3': 0.2, 'breakout_v2': 0.5}
alpha_weighting.update_weights(portfolio_corr)

# Get weights
weights = alpha_weighting.get_all_weights()
print(f"Weights: {weights}")
```

---

## 7. Monitoring and Debugging

### Add Logging

All components have extensive logging. Monitor with:

```bash
# Watch logs
tail -f sidecar/logs/app.log | grep -E "GBT|Bandit|Weight"
```

### Check Component Status

Add endpoint to check status:

```python
@router.get("/ml/status")
async def get_ml_status():
    return {
        "gbt_loaded": gbt_meta_learner.model is not None,
        "bandit_regimes": len(alpha_bandit.params),
        "alpha_weights": alpha_weighting.get_all_weights(),
        "alpha_performance": alpha_weighting.get_all_performance(),
    }
```

---

## Summary

1. **GBT Meta-Learner**: Refines RF/LSTM predictions for better accuracy
2. **Thompson Sampling Bandit**: Selects best alpha per regime dynamically
3. **Adaptive Alpha Weighting**: Increases weights for profitable alphas

All three components work together to create a self-learning system that continuously improves performance.

**Next Steps**:
1. Integrate these components following this guide
2. Test each component individually
3. Test integrated system
4. Monitor performance improvements
5. Adjust hyperparameters (η, λ) as needed
