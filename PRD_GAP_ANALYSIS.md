# PRD Gap Analysis - VPropTrader Quant System

## Executive Summary

This document identifies gaps between the PRD requirements and current implementation, categorized by priority and impact.

---

## ✅ COMPLETED (Tasks 3.2, 4.2, 9.4)

### 1. ONNX Export and Inference
- ✅ Random Forest ONNX export
- ✅ LSTM ONNX export
- ✅ Inference < 1ms validation
- ✅ Model versioning and atomic swaps
- ✅ Rollback capability

### 2. Global Scanner
- ✅ 30-40 combinations/second evaluation
- ✅ Q* confidence scoring
- ✅ ES95 calculation and filtering
- ✅ Portfolio correlation checks
- ✅ >90% skip rate enforcement
- ✅ Priority queue for top K signals

### 3. Overview Dashboard
- ✅ Real-time equity chart
- ✅ PnL gauges (today/total)
- ✅ Drawdown meters
- ✅ Performance metrics (Sharpe, Sortino, Calmar)
- ✅ WebSocket live updates
- ✅ Connection status monitoring

---

## 🆕 JUST ADDED (Addressing PRD Gaps)

### 4. Gradient Boosted Tree Meta-Learner
**File**: `sidecar/app/ml/gbt_meta_learner.py`
- ✅ LightGBM-based meta-learner
- ✅ Refines RF and LSTM predictions
- ✅ Weekly update schedule (configurable)
- ✅ Feature importance tracking
- ✅ Save/load functionality

**PRD Requirement**: "Gradient Boosted Tree - meta-probability refiner - weekly"

### 5. Reinforcement Bandit (Thompson Sampling)
**File**: `sidecar/app/scanner/alpha_selector.py`
- ✅ Thompson Sampling for alpha selection
- ✅ Per-regime alpha optimization
- ✅ Online learning from trade outcomes
- ✅ Beta distribution tracking
- ✅ Statistics and performance monitoring

**PRD Requirement**: "Reinforcement Bandit - chooses alpha per regime - online"

### 6. Adaptive Alpha Weighting
**File**: `sidecar/app/scanner/alpha_weighting.py`
- ✅ Formula: `w_i^{t+1} = w_i^t + η(Sharpe_i - S̄) - λρ_{i,port}`
- ✅ Automatic weight updates based on Sharpe
- ✅ Correlation penalty
- ✅ Performance tracking per alpha
- ✅ Weight normalization

**PRD Requirement**: "w_i^{t+1}=w_i^t+η(Sharpe_i-S̄)-λρ_{i,port}"

---

## ⚠️ PARTIALLY IMPLEMENTED

### 7. Execution Quality Filters
**Status**: Framework exists, needs completion

**What's Missing**:
- [ ] Spread filter (60th percentile calculation)
- [ ] Slippage prediction model
- [ ] Latency monitor with 400ms threshold
- [ ] Quote flicker detector

**Current State**: Scanner checks some conditions but not all filters

**Priority**: HIGH - Critical for execution quality

**Recommendation**: Create `sidecar/app/execution/quality_filters.py`

### 8. Risk Management - Time Stops
**Status**: Position sizing exists, time-based exits missing

**What's Missing**:
- [ ] 45-minute time stop
- [ ] 2 adverse bars → partial exit logic
- [ ] Time-based position monitoring

**Current State**: SL/TP calculated but no time-based exits

**Priority**: MEDIUM - Risk management enhancement

**Recommendation**: Add to `sidecar/app/risk/` or MT5 EA

### 9. Memory System
**Status**: Database and Redis clients exist, memory logic incomplete

**What's Missing**:
- [ ] Short-term memory (last N trades with context)
- [ ] Long-term memory (FAISS vector store integration)
- [ ] Memory update flow after trades
- [ ] Rolling statistics calculation

**Current State**: Storage infrastructure ready, logic not implemented

**Priority**: HIGH - Required for self-learning

**Recommendation**: Complete `sidecar/app/memory/` module

### 10. Drift Detection and Retraining
**Status**: Drift detector exists, retraining scheduler missing

**What's Missing**:
- [ ] Nightly retrain scheduler (cron job)
- [ ] Drift detection integration with retraining
- [ ] Automatic model swap after retrain
- [ ] Training data preparation from memory

**Current State**: `drift_detector.py` exists, not integrated

**Priority**: HIGH - Core self-learning feature

**Recommendation**: Complete `sidecar/app/ml/trainer.py` integration

---

## ❌ NOT IMPLEMENTED

### 11. MT5 Expert Advisor Components
**Status**: Skeleton exists, needs completion

**What's Missing**:
- [ ] Trade execution engine (orders, fills, monitoring)
- [ ] Hard governors (all 7 VProp rules)
- [ ] Soft governors (cool-down, vol cap, profit lock)
- [ ] Trading scheduler (London/NY sessions)
- [ ] Fail-safe and emergency controls

**Current State**: Basic structure in `mt5_ea/` folder

**Priority**: CRITICAL - Required for live trading

**Recommendation**: Complete all MT5 EA tasks (8.1-8.8)

### 12. Dashboard - Additional Pages
**Status**: Overview complete, other pages missing

**What's Missing**:
- [ ] Compliance Panel (rule indicators)
- [ ] Alpha Heatmap
- [ ] Regime Statistics
- [ ] Risk Monitor
- [ ] Learning Dashboard
- [ ] Session Report

**Current State**: Only Overview page implemented

**Priority**: MEDIUM - Analytics and monitoring

**Recommendation**: Complete dashboard tasks (9.5-9.10)

### 13. Analytics and Logging System
**Status**: Basic endpoints exist, comprehensive logging missing

**What's Missing**:
- [ ] Complete trade logging with all fields
- [ ] Daily digest generation (JSON + CSV)
- [ ] Performance metrics calculators
- [ ] Compliance checking logic
- [ ] Alpha performance aggregation

**Current State**: Placeholder endpoints in `api/analytics.py`

**Priority**: HIGH - Required for audit trail

**Recommendation**: Complete tasks 7.1-7.3

### 14. Integration and Testing
**Status**: Not started

**What's Missing**:
- [ ] Demo/paper trading environment
- [ ] Integration tests (EA ↔ Sidecar ↔ Dashboard)
- [ ] Compliance testing
- [ ] Paper trading validation
- [ ] Performance testing

**Current State**: No test infrastructure

**Priority**: CRITICAL - Required before live trading

**Recommendation**: Complete tasks 10.1-10.4

---

## 📊 Priority Matrix

### CRITICAL (Must Have for Live Trading)
1. **MT5 Expert Advisor** - Complete all components
2. **Integration Testing** - Validate end-to-end flow
3. **Hard Governors** - Enforce all VProp rules

### HIGH (Core Functionality)
1. **Memory System** - Enable self-learning
2. **Drift Detection & Retraining** - Automatic model updates
3. **Execution Quality Filters** - Prevent bad trades
4. **Analytics & Logging** - Audit trail and compliance

### MEDIUM (Enhancements)
1. **Time-based Stops** - Additional risk management
2. **Dashboard Pages** - Full monitoring suite
3. **Soft Governors** - Adaptive risk controls

### LOW (Nice to Have)
1. **Multi-account Dashboard** - Scaling feature
2. **Advanced Visualizations** - Enhanced analytics

---

## 🎯 Recommended Implementation Order

### Phase 1: Core Trading System (Weeks 1-2)
1. Complete MT5 EA (tasks 8.1-8.8)
2. Integrate GBT meta-learner into inference pipeline
3. Integrate Thompson Sampling bandit into scanner
4. Integrate adaptive alpha weighting

### Phase 2: Self-Learning (Week 3)
1. Complete memory system (task 3.3)
2. Complete retraining engine (task 3.4)
3. Integrate drift detection
4. Test nightly retrain workflow

### Phase 3: Risk & Execution (Week 4)
1. Complete execution quality filters (tasks 6.1-6.3)
2. Add time-based stops and partial exits
3. Complete analytics and logging (tasks 7.1-7.3)

### Phase 4: Testing & Validation (Week 5)
1. Set up demo environment
2. Run integration tests
3. Validate compliance
4. Paper trading for 1 week

### Phase 5: Dashboard & Deployment (Week 6)
1. Complete remaining dashboard pages
2. Production deployment
3. Live trading validation
4. Documentation

---

## 🔧 Integration Points

### New Components Need Integration:

1. **GBT Meta-Learner** → `ml/inference.py`
   - Add refinement step after RF/LSTM predictions
   - Update Q* calculation to use refined probabilities

2. **Thompson Sampling Bandit** → `scanner/scanner.py`
   - Use bandit to select best alpha per regime
   - Update bandit after each trade outcome

3. **Adaptive Alpha Weighting** → `scanner/alphas.py`
   - Apply weights when evaluating alpha signals
   - Update weights based on trade outcomes

4. **All Components** → `api/executions.py`
   - Report trade outcomes to update all learning systems
   - Trigger memory updates, weight updates, bandit updates

---

## 📝 Next Steps

1. **Immediate**: Integrate the 3 new components (GBT, Bandit, Weighting)
2. **Short-term**: Complete MT5 EA and memory system
3. **Medium-term**: Complete testing and remaining dashboard
4. **Long-term**: Production deployment and monitoring

---

## 🎓 Key Learnings

### What's Working Well:
- ONNX inference is fast (<1ms)
- Scanner efficiently evaluates combinations
- Dashboard provides real-time updates
- Code is modular and maintainable

### What Needs Attention:
- MT5 EA is the critical path
- Memory system is essential for self-learning
- Testing infrastructure is needed
- Integration between components needs work

### Risks:
- MT5 EA complexity could delay timeline
- Integration testing may reveal issues
- Live trading validation is critical
- VProp rule compliance must be perfect

---

**Status**: 3 major tasks complete, 3 critical gaps addressed, ~60% of PRD implemented

**Estimated Completion**: 4-6 weeks for full production-ready system
