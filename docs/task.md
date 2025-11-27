# MCP Integration - Deployment Task List

## 🎯 Phase 1: MCP Intelligence Integration

**Goal**: Deploy news intelligence and reasoning engine to production  
**Expected Impact**: 25-40% improvement in risk-adjusted returns  
**Timeline**: 3-5 days

---

## ✅ Pre-Deployment (Completed)

- [x] Deep analysis of VPropTrader system (206+ files)
- [x] Identified MCP integration opportunities
- [x] Created comprehensive improvement plan
- [x] Implemented MCP News Intelligence module
- [x] Implemented MCP Reasoning Engine module
- [x] Created installation scripts and documentation
- [x] Generated walkthrough and integration guides

**Deliverables Location**: `/tmp/`
- `mcp_news_intelligence.py` (6.9 KB)
- `mcp_reasoning_engine.py` (9.1 KB)
- `README_MCP_IMPLEMENTATION.md` (8.7 KB)
- `install_mcp_modules.sh` (3.2 KB)

---

## 📋 Deployment Tasks

### Task 1: Environment Setup

**Estimated Time**: 15 minutes

- [ ] **1.1** Navigate to project directory
  ```bash
  cd /home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader
  ```

- [ ] **1.2** Activate virtual environment
  ```bash
  cd sidecar
  source venv/bin/activate
  ```

- [ ] **1.3** Install MCP SDK
  ```bash
  pip install mcp
  ```
  **Acceptance**: `pip show mcp` shows package info

- [ ] **1.4** Verify Node.js/NPM available
  ```bash
  node --version
  npm --version
  ```
  **Acceptance**: Both commands show version numbers

- [ ] **1.5** Test MCP servers accessibility
  ```bash
  npx -y @modelcontextprotocol/server-brave-search --help
  npx -y @modelcontextprotocol/server-sequential-thinking --help
  ```
  **Acceptance**: Both commands execute without errors

**Checkpoint**: MCP infrastructure ready ✅

---

### Task 2: Module Installation

**Estimated Time**: 10 minutes

- [ ] **2.1** Copy News Intelligence module
  ```bash
  # Manual copy (due to .gitignore)
  sudo cp /tmp/mcp_news_intelligence.py sidecar/app/data/
  sudo chown ubuntu:ubuntu sidecar/app/data/mcp_news_intelligence.py
  ```

- [ ] **2.2** Copy Reasoning Engine module
  ```bash
  sudo cp /tmp/mcp_reasoning_engine.py sidecar/app/ml/
  sudo chown ubuntu:ubuntu sidecar/app/ml/mcp_reasoning_engine.py
  ```

- [ ] **2.3** Verify files copied successfully
  ```bash
  ls -la sidecar/app/data/mcp_news_intelligence.py
  ls -la sidecar/app/ml/mcp_reasoning_engine.py
  ```
  **Acceptance**: Both files exist and are readable

- [ ] **2.4** Update requirements.txt
  ```bash
  echo "mcp>=0.1.0  # Model Context Protocol SDK" >> sidecar/requirements.txt
  ```

- [ ] **2.5** Verify Python imports work
  ```bash
  cd sidecar
  python -c "from app.data.mcp_news_intelligence import mcp_news_intelligence; print('✓ News module OK')"
  python -c "from app.ml.mcp_reasoning_engine import mcp_reasoning_engine; print('✓ Reasoning module OK')"
  ```
  **Acceptance**: Both imports succeed without errors

**Checkpoint**: Modules installed and importable ✅

---

### Task 3: Integration with Scanner

**Estimated Time**: 20 minutes

- [ ] **3.1** Backup original scanner.py
  ```bash
  cp sidecar/app/scanner/scanner.py sidecar/app/scanner/scanner.py.backup
  ```

- [ ] **3.2** Edit scanner.py
  Open `sidecar/app/scanner/scanner.py` in editor

- [ ] **3.3** Add import at top of file
  ```python
  from app.data.mcp_news_intelligence import mcp_news_intelligence
  ```

- [ ] **3.4** Add news intelligence in scan() method
  Location: After `features = await feature_engineer.extract_features(symbol)` (~line 147)
  
  Insert:
  ```python
  # MCP News Intelligence Integration
  try:
      news_sentiment = await mcp_news_intelligence.get_market_sentiment(symbol)
      
      # Skip if high-risk news environment
      if mcp_news_intelligence.is_high_risk_environment(symbol):
          logger.warning(f"⚠️ Skipping {symbol} - high-risk news environment")
          logger.warning(f"   Headlines: {news_sentiment['top_headlines'][:2]}")
          self.skip_count += 1
          continue
      
      # Add news to features
      features['news_sentiment'] = news_sentiment['sentiment_score']
      features['news_impact'] = news_sentiment['impact_level']
      
      if abs(news_sentiment['sentiment_score']) > 0.5:
          logger.info(f"📰 Strong {news_sentiment['sentiment_label']} news for {symbol}")
          
  except Exception as e:
      logger.warning(f"Could not get news sentiment for {symbol}: {e}")
      features['news_sentiment'] = 0.0
      features['news_impact'] = 'low'
  ```

- [ ] **3.5** Verify syntax
  ```bash
  python -m py_compile sidecar/app/scanner/scanner.py
  ```
  **Acceptance**: No syntax errors

**Checkpoint**: Scanner integrated with news intelligence ✅

---

### Task 4: Integration with Signals API

**Estimated Time**: 25 minutes

- [ ] **4.1** Backup original signals.py
  ```bash
  cp sidecar/app/api/signals.py sidecar/app/api/signals.py.backup
  ```

- [ ] **4.2** Edit signals.py
  Open `sidecar/app/api/signals.py` in editor

- [ ] **4.3** Add import at top
  ```python
  from app.ml.mcp_reasoning_engine import mcp_reasoning_engine
  ```

- [ ] **4.4** Add AI validation before returning signals
  Location: Before `return SignalsResponse(...)` (~line 260)
  
  Insert:
  ```python
  # MCP Reasoning Engine Validation
  validated_signals = []
  original_count = len(signals)
  
  for signal in signals:
      try:
          # Prepare market context
          market_context = {
              'regime': signal.regime,
              'vix_z': signal.features.get('vix_z', 0),
              'trend_strength': signal.features.get('trend_strength', 0.5),
              'volatility': signal.features.get('realized_vol', 0.01),
              'news_sentiment': signal.features.get('news_sentiment', 0),
              'news_impact': signal.features.get('news_impact', 'low'),
              'current_drawdown_pct': 0.5,  # TODO: Get from account manager
              'daily_pnl': 0.0,              # TODO: Get from daily tracker
          }
          
          # AI reasoning check
          should_trade, explanation, confidence_adj = await mcp_reasoning_engine.should_take_trade(
              signal={
                  'symbol': signal.symbol,
                  'action': signal.action,
                  'q_star': signal.q_star,
                  'confidence': signal.confidence,
              },
              market_context=market_context
          )
          
          if not should_trade:
              logger.info(f"🧠 AI Override: Rejecting {signal.symbol} {signal.action}")
              logger.info(f"   Reason: {explanation[:100]}")
              continue
          
          # Adjust confidence if recommended
          if abs(confidence_adj) > 0.01:
              original_conf = signal.confidence
              signal.confidence = max(0.1, min(1.0, signal.confidence + confidence_adj))
              signal.lots = signal.lots * (signal.confidence / original_conf)
              
              logger.info(f"🧠 Confidence adjusted: {signal.symbol} {original_conf:.2f} → {signal.confidence:.2f}")
          
          validated_signals.append(signal)
          
      except Exception as e:
          logger.error(f"Reasoning engine error for {signal.symbol}: {e}")
          validated_signals.append(signal)  # Fail-safe: allow trade
  
  logger.info(f"🧠 AI Validation: {len(validated_signals)}/{original_count} signals approved")
  signals = validated_signals
  ```

- [ ] **4.5** Verify syntax
  ```bash
  python -m py_compile sidecar/app/api/signals.py
  ```
  **Acceptance**: No syntax errors

**Checkpoint**: Signals API integrated with reasoning engine ✅

---

### Task 5: Add Monitoring Endpoints

**Estimated Time**: 15 minutes

- [ ] **5.1** Backup analytics.py
  ```bash
  cp sidecar/app/api/analytics.py sidecar/app/api/analytics.py.backup
  ```

- [ ] **5.2** Add MCP analytics endpoints
  
  Add to end of `analytics.py`:
  ```python
  @router.get("/mcp/news")
  async def get_mcp_news_analytics():
      """Get MCP news intelligence analytics"""
      from app.data.mcp_news_intelligence import mcp_news_intelligence
      
      return {
          'status': 'ok',
          'cache_size': len(mcp_news_intelligence.news_cache),
          'symbols_tracked': list(mcp_news_intelligence.sentiment_history.keys()),
          'average_sentiment_24h': {
              symbol: sum(h['sentiment'] for h in history) / len(history)
              for symbol, history in mcp_news_intelligence.sentiment_history.items()
              if history
          },
      }
  
  @router.get("/mcp/reasoning")
  async def get_mcp_reasoning_analytics():
      """Get MCP reasoning engine analytics"""
      from app.ml.mcp_reasoning_engine import mcp_reasoning_engine
      
      return {
          'status': 'ok',
          **mcp_reasoning_engine.get_override_stats()
      }
  ```

- [ ] **5.3** Verify syntax
  ```bash
  python -m py_compile sidecar/app/api/analytics.py
  ```

**Checkpoint**: Monitoring endpoints added ✅

---

### Task 6: Testing (Log-Only Mode)

**Estimated Time**: 4-8 hours (mostly waiting)

- [ ] **6.1** Ensure EA is in log-only mode
  Open `mt5_ea/config.mqh`, verify:
  ```cpp
  input bool LogOnlyMode = true;  // Must be TRUE for testing
  ```

- [ ] **6.2** Start sidecar service
  ```bash
  cd sidecar
  source venv/bin/activate
  python -m app.main
  ```
  **Acceptance**: Service starts without errors

- [ ] **6.3** Monitor startup logs
  Check for:
  ```
  ✓ MCP modules loaded successfully
  ✓ News intelligence initialized
  ✓ Reasoning engine initialized
  ```

- [ ] **6.4** Test news intelligence manually
  ```bash
  curl http://localhost:8000/api/analytics/mcp/news
  ```
  **Acceptance**: Returns JSON with news data

- [ ] **6.5** Test reasoning analytics
  ```bash
  curl http://localhost:8000/api/analytics/mcp/reasoning
  ```
  **Acceptance**: Returns override statistics

- [ ] **6.6** Check signal generation
  ```bash
  curl http://localhost:8000/api/signals?equity=1000
  ```
  **Acceptance**: Returns signals (may be empty if no setups)

- [ ] **6.7** Monitor logs for 1 hour
  Watch for:
  - 📰 News sentiment logs
  - 🧠 AI reasoning decisions
  - Any errors or warnings

- [ ] **6.8** Run overnight test (8 hours)
  Let system run through London/NY sessions
  
- [ ] **6.9** Check logs next day
  ```bash
  tail -100 sidecar/logs/app.log | grep -E "(📰|🧠|⚠️)"
  ```

**Acceptance Criteria**:
- ✅ No errors or crashes
- ✅ News sentiment retrieved for symbols
- ✅ AI reasoning validates signals
- ✅ Override rate between 5-20%
- ✅ System stable for 8+ hours

**Checkpoint**: Testing complete, ready for validation ✅

---

### Task 7: Performance Validation

**Estimated Time**: 1 week (ongoing monitoring)

- [ ] **7.1** Baseline metrics (before MCP)
  Document current:
  - Win rate
  - Sharpe ratio
  - Max drawdown
  - Avg winner/loser ratio

- [ ] **7.2** Enable live trading with MCP
  After successful testing:
  - Set `LogOnlyMode = false` in MT5 EA
  - Monitor first 10 trades closely

- [ ] **7.3** Daily monitoring checklist
  Each day for 7 days:
  - [ ] Check override rate (target: 10-15%)
  - [ ] Review AI rejections (were they correct?)
  - [ ] Monitor win rate improvement
  - [ ] Check news-driven trade outcomes
  - [ ] Verify no false positives

- [ ] **7.4** Week 1 analysis
  After 7 days:
  - Calculate new win rate
  - Calculate new Sharpe ratio
  - Compare news-event trade outcomes
  - Measure override accuracy

- [ ] **7.5** Tune parameters if needed
  Adjust:
  - Confidence adjustment thresholds
  - News impact detection sensitivity
  - Reasoning prompts

**Success Criteria**:
- ✅ Win rate improved by 5%+
- ✅ Sharpe ratio improved by 15%+
- ✅ News-driven losses reduced by 50%+
- ✅ Override accuracy >80%
- ✅ No system crashes or errors

**Checkpoint**: Validation complete, MCP proven ✅

---

## 🚨 Troubleshooting

### Issue: MCP modules import fails

**Solution**:
```bash
# Check Python path
cd sidecar
python -c "import sys; print('\n'.join(sys.path))"

# Ensure app directory is in path
export PYTHONPATH="${PYTHONPATH}:/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/sidecar"
```

### Issue: Brave Search MCP not working

**Solution**:
```bash
# Verify NPM can access package
npx -y @modelcontextprotocol/server-brave-search --version

# Check if API key needed (free tier available)
# Get key from: https://brave.com/search/api/
```

### Issue: High override rate (>30%)

**Analysis**: Reasoning engine may be too conservative

**Solution**:
1. Review recent override reasons
2. Check if news sentiment threshold too strict
3. Adjust confidence reduction amounts in code

### Issue: Low override rate (<5%)

**Analysis**: Reasoning engine may be too permissive

**Solution**:
1. Check if MCP calls are succeeding
2. Verify market context data is populated
3. Review reasoning prompts for clarity

### Issue: Performance degradation

**Analysis**: MCP calls adding too much latency

**Solution**:
1. Check MCP call times in logs
2. Increase cache duration if needed
3. Consider running MCP calls in background

---

## 📊 Success Metrics Dashboard

Create tracking spreadsheet:

| Date | Signals | Overrides | Override % | Win Rate | Sharpe | Notes |
|------|---------|-----------|------------|----------|--------|-------|
| Day 1 | | | | | | |
| Day 2 | | | | | | |
| ... | | | | | | |
| Week 1 Avg | | | | | | |

**Target Metrics After 1 Week**:
- Override rate: 10-15%
- Win rate: 70%+ (up from 65%)
- Sharpe ratio: 5.0+ (up from 4.0)
- News loss reduction: 60%+

---

## 🎯 Rollback Plan

If issues arise:

1. **Stop sidecar service**
   ```bash
   # Ctrl+C or
   pm2 stop vprop-sidecar
   ```

2. **Restore backups**
   ```bash
   cp sidecar/app/scanner/scanner.py.backup sidecar/app/scanner/scanner.py
   cp sidecar/app/api/signals.py.backup sidecar/app/api/signals.py
   cp sidecar/app/api/analytics.py.backup sidecar/app/api/analytics.py
   ```

3. **Restart without MCP**
   ```bash
   cd sidecar
   python -m app.main
   ```

**Rollback triggers**:
- System crashes or errors
- Win rate decreases
- Too many false positive overrides (>20%)
- Unacceptable latency (>  2 seconds per signal)

---

## ✅ Completion Checklist

Phase 1 is COMPLETE when:

- [x] Deep analysis completed
- [x] MCP modules created
- [x] Documentation written
- [ ] MCP SDK installed
- [ ] Modules copied to sidecar
- [ ] Scanner integrated
- [ ] Signals API integrated
- [ ] Monitoring endpoints added
- [ ] Tested in log-only mode (8+ hours)
- [ ] Live trading enabled
- [ ] Week 1 validation complete
- [ ] Performance metrics meet targets
- [ ] No critical issues

**Final Status**: 
- **Current**: 🟡 Ready for Deployment
- **Target**: 🟢 Production Complete

---

## 📞 Support Resources

- **Implementation Guide**: `/tmp/README_MCP_IMPLEMENTATION.md`
- **Walkthrough**: Artifact `mcp_implementation_walkthrough.md`
- **Product Analysis**: Artifact `product_improvement_analysis.md`
- **Source Files**: `/tmp/mcp_*.py`

---

## 🚀 Next Phases

After Phase 1 complete:

**Phase 2**: Cognitive Architecture (Weeks 5-8)
- [x] **Memory Engine Implementation**
    - [x] Install `chromadb`
    - [x] Create `vector_store.py`
    - [x] Create `episodic_memory.py`
    - [x] Integrate with `signals.py` (RAG)
- [x] **Self-Learning Loop**
    - [x] Implement trade outcome recording
    - [x] Create nightly "Researcher Agent" job
- [x] **Advanced Alphas**
    - [x] Implement Microstructure features (OFI, VPIN)

**Phase 3**: Order Flow Analysis (Weeks 9-10)
- [x] Delta analysis (buy vs sell volume)
- [x] Large print detection
- [x] Iceberg order detection
- [x] Order book imbalance

**Phase 4**: Enhanced Memory MCP (Weeks 13-14)
- [x] Persistent pattern learning (Online Learning)
- [x] Historical similarity search (Episodic Memory)
**Phase 4**: Enhanced Memory MCP (Weeks 13-14)
- [x] Persistent pattern learning (Online Learning)
- [x] Historical similarity search (Episodic Memory)
- [x] Cross-session knowledge retention (Vector DB)

**Phase 5**: Macro-Fundamental Intelligence (The "Global View")
- [x] **FRED Integration**: Yield Curve, Inflation, Corporate Spreads.
- [x] **Macro Regime Model**: Detect "Risk-On" vs "Risk-Off" environments.
- [x] **Event-Driven Arbitrage**: Trade earnings and FOMC with specialized logic.

**Phase 6**: Deep Quant Strategies (The "Math Whiz")
- [x] **Statistical Arbitrage**: Cointegration-based Pairs Trading.
- [x] **Spectral Analysis**: Fourier Transforms for cycle detection.
- [x] **Fractal Geometry**: Hurst Exponent for trend persistency.

**Phase 7**: Next-Gen Machine Learning (The "Future")
- [ ] **Transformer Models**: Replace LSTMs with Temporal Fusion Transformers.
- [ ] **Reinforcement Learning**: PPO Agent for optimal execution.

**Phase 8**: User & Prop Firm Management (The "Cockpit")
- [x] **ElectronJS App**: Popup for User/Prop Firm credentials & rules.
- [x] **Database Integration**: Store User, Prop Firm, and Rule data.
- [x] **MT5 Handler**: Dynamic connection based on stored credentials.
- [x] **Prop Risk Engine**: Enforce Max Drawdown, Daily Loss, and Trading Hours.

---

*Task list created by Antigravity AI*  
*Date: November 24, 2025*  
*Status: Ready for Execution*
