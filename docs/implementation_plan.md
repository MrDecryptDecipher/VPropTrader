# Implementation Plan - Phase 2.1: Memory Engine (Episodic Memory)

**Goal**: Enable VPropTrader to "remember" past trades and use them to validate new signals (Retrieval Augmented Generation for Trading).

## User Review Required
> [!IMPORTANT]
> This implementation introduces a new dependency: `chromadb` (or `faiss-cpu`). ChromaDB is recommended for ease of use and metadata filtering capabilities.
> **Decision**: We will use `chromadb` for the local vector store.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/memory/vector_store.py`
- **Purpose**: Low-level wrapper for the Vector Database.
- **Implementation**:
    - Initialize ChromaDB client (persistent storage in `data/memory_db`).
    - Define collection `trade_episodes`.
    - Methods: `add_vectors`, `query_vectors`, `delete_vectors`.

#### [NEW] `app/memory/episodic_memory.py`
- **Purpose**: High-level manager for trade episodes.
- **Implementation**:
    - `store_episode(trade_context, outcome)`: Embeds market state and stores it.
    - `recall_similar_episodes(current_context, k=5)`: Retrieves top-k similar historical situations.
    - `_embed_context(context)`: Converts dictionary context into a vector (using simple normalization or a lightweight embedding model).

#### [MODIFY] `app/api/signals.py`
- **Change**: Integrate `episodic_memory` into the signal validation loop.
- **Logic**:
    - Before `mcp_reasoning_engine` is called:
    - Call `episodic_memory.recall_similar_episodes(current_context)`.
    - Pass the retrieved `similar_episodes` to the `mcp_reasoning_engine` as additional context.

#### [MODIFY] `requirements.txt`
- Add `chromadb`.
- Add `numpy` (if not present, likely is).

## Verification Plan

### Automated Tests
1.  **Unit Test (`tests/test_memory.py`)**:
    - Initialize `EpisodicMemory` with a temporary DB.
    - Store 3 distinct episodes (e.g., "High Volatility Loss", "Low Volatility Win", "Trend Win").
    - Query with a context similar to "High Volatility".
    - **Assert**: The "High Volatility Loss" episode is returned as the top match.

2.  **Integration Test (`tests/test_rag_signal.py`)**:
    - Mock the `mcp_reasoning_engine`.
    - Inject a signal.
    - Verify that `episodic_memory.recall_similar_episodes` is called.
    - Verify that the retrieved context is passed to the reasoning engine.

### Manual Verification
1.  **Script**: `scripts/test_memory_rag.py`
    - Stores dummy trade history.
    - Runs a query for a new signal.
    - Prints the "Recalled Memories" and the resulting AI decision.

# Implementation Plan - Phase 2.2: Self-Learning Loop

**Goal**: Automate the "Reflection" phase of the Cognitive Loop.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/learning/trade_recorder.py`
- **Purpose**: Listens for trade close events and stores them in Episodic Memory.
- **Logic**:
    - `record_trade_outcome(trade_data)`:
        - Reconstructs `MarketContext` (or retrieves it if cached).
        - Calculates PnL and Outcome (Win/Loss).
        - Calls `episodic_memory.store_episode()`.

#### [NEW] `app/learning/researcher.py`
- **Purpose**: Nightly job to analyze recent performance and suggest rules.
- **Logic**:
    - `analyze_recent_performance(days=1)`:
        - Queries `vector_store` for all trades in the last 24h.
        - Clusters losing trades.
        - Uses `mcp_reasoning_engine` to find commonalities (e.g., "All losses had High Volatility").
    - `suggest_new_rules()`:
        - Outputs suggestions to `data/suggested_rules.json`.

#### [MODIFY] `app/api/analytics.py`
- **Change**: Hook into the trade update endpoint.
- **Logic**:
    - When a trade status updates to "CLOSED":
    - Call `trade_recorder.record_trade_outcome()`.

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_learning.py`
    - Simulate a trade close event.
    - Verify it appears in the `vector_store`.
    - Run the `researcher` on dummy data and verify it produces a rule suggestion.

# Implementation Plan - Phase 2.3: Microstructure Alphas

**Goal**: Implement institutional-grade order flow features to detect "invisible" market pressure.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/features/microstructure.py`
- **Purpose**: Calculates advanced order flow metrics.
- **Logic**:
    - `calculate_ofi(bid_vol, ask_vol, bid_price, ask_price)`:
        - Computes Order Flow Imbalance (OFI) based on changes in best bid/ask.
        - Returns a normalized OFI score (-1 to +1).
    - `calculate_vpin(volume, price, bucket_size)`:
        - Computes Volume-Synchronized Probability of Informed Trading.
        - Detects toxic flow (high VPIN = high risk of adverse selection).

#### [MODIFY] `app/features/feature_engineering.py`
- **Change**: Integrate `microstructure` features into the main pipeline.
- **Logic**:
    - Import `microstructure`.
    - In `calculate_features()`:
        - Call `microstructure.calculate_ofi()`.
        - Call `microstructure.calculate_vpin()`.
        - Add results to the feature vector.

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_microstructure.py`
    - Feed synthetic order book data.
    - Verify OFI is positive when buying pressure increases.
    - Verify VPIN spikes when volume is one-sided.

# Implementation Plan - Phase 3: Order Flow Analysis

**Goal**: Detect "Whale" activity and hidden liquidity.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/features/order_flow.py`
- **Purpose**: Analyzes trade ticks for aggressive buying/selling.
- **Logic**:
    - `calculate_delta(trades)`:
        - Net difference between aggressive buys (at ask) and aggressive sells (at bid).
        - Cumulative Delta Volume (CVD).
    - `detect_large_prints(trades, threshold=10.0)`:
        - Identifies single trades larger than `threshold` lots.
        - Flags "Whale" activity.
    - `detect_icebergs(trades, price_level)`:
        - Detects if volume traded at a price level exceeds the visible liquidity.

#### [MODIFY] `app/features/feature_engineering.py` (or `scanner.py`)
- **Change**: Integrate `order_flow` features.
- **Logic**:
    - Call `order_flow.calculate_delta()`.
    - Call `order_flow.detect_large_prints()`.
    - Add `whale_alert` boolean to features.

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_order_flow.py`
    - Simulate a stream of trades.
    - Verify Delta calculation.
    - Verify Large Print detection triggers correctly.

# Implementation Plan - Phase 4: Online Learning (Procedural Memory)

**Goal**: Enable the system to adapt its "skills" (weights and models) in real-time.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/learning/online_learner.py`
- **Purpose**: Manages real-time adaptation of strategy weights and model parameters.
- **Logic**:
    - `update_alpha_weights(trade_outcome)`:
        - Implements a Multi-Armed Bandit (Thompson Sampling) approach.
        - Updates the Beta distribution parameters (alpha/beta) for the strategy used.
        - `weight = sample_beta(alpha, beta)`
    - `update_model(trade_context, outcome)`:
        - Performs a partial_fit (SGD) on a lightweight online model (e.g., SGDClassifier).
        - Keeps the model in sync with the latest market regime.

#### [MODIFY] `app/scanner/scanner.py`
- **Change**: Use dynamic weights from `online_learner`.
- **Logic**:
    - Replace static/config weights with `online_learner.get_current_weights()`.

#### [MODIFY] `app/learning/trade_recorder.py`
- **Change**: Trigger online learning after recording trade.
- **Logic**:
    - Call `online_learner.update_alpha_weights()`.
    - Call `online_learner.update_model()`.

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_online_learning.py`
    - Simulate a sequence of wins/losses for a strategy.
    - Verify its weight increases/decreases accordingly.

# Implementation Plan - Phase 5: Macro-Fundamental Intelligence

**Goal**: Give the system a "Top-Down" understanding of the global economy.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/data/macro_client.py`
- **Purpose**: Fetches economic data from FRED (Federal Reserve Economic Data).
- **Logic**:
    - `fetch_yield_curve()`: 10Y - 2Y Treasury Spread (Recession predictor).
    - `fetch_inflation_expectations()`: 5Y Breakeven Inflation Rate.
    - `fetch_credit_spreads()`: HYG vs LQD (Risk appetite).
    - `fetch_liquidity_index()`: Fed Balance Sheet + Reverse Repo.

#### [NEW] `app/features/macro_features.py`
- **Purpose**: Converts raw economic data into trading signals.
- **Logic**:
    - `calculate_regime()`:
        - **Goldilocks**: Growth Up, Inflation Down (Buy Tech).
        - **Reflation**: Growth Up, Inflation Up (Buy Energy/Value).
        - **Stagflation**: Growth Down, Inflation Up (Buy Gold/Cash).
        - **Deflation**: Growth Down, Inflation Down (Buy Bonds).
    - Returns a `regime_score` (-1 to +1) for Risk Assets.

#### [MODIFY] `app/scanner/scanner.py`
- **Change**: Use Macro Regime as a "Global Filter".
- **Logic**:
    - If `regime == "Recession"`:
        - Block all "Long" signals on High Beta assets (NAS100).
        - Boost "Short" signals.
        - Boost "Long" signals on Safe Havens (Gold, USD).

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_macro.py`
    - Mock FRED API responses.
    - Verify Regime Classifier correctly identifies "Recession" when Yield Curve inverts.

# Implementation Plan - Phase 6: Deep Quant Strategies

**Goal**: Apply advanced mathematics to find hidden alpha.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/features/quant_features.py`
- **Purpose**: Advanced mathematical feature engineering.
- **Logic**:
    - `calculate_hurst_exponent(series)`:
        - Measures long-term memory of time series.
        - H < 0.5: Mean Reverting.
        - H > 0.5: Trending.
    - `calculate_fft_cycle(series)`:
        - Fast Fourier Transform to identify dominant cycle period.
        - Returns `dominant_period` and `cycle_phase`.

#### [NEW] `app/strategies/stat_arb.py`
- **Purpose**: Cointegration-based Pairs Trading.
- **Logic**:
    - `check_cointegration(asset_a, asset_b)`: Engle-Granger test.
    - `calculate_z_score(spread)`: Standardized deviation from mean.
    - Signal: Short Spread if Z > 2, Long Spread if Z < -2.

#### [MODIFY] `app/features/feature_engineering.py` (or `scanner.py`)
- **Change**: Integrate `quant_features`.
- **Logic**:
    - Add `hurst` and `cycle_period` to feature vector.

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_quant.py`
    - Verify Hurst Exponent on random walk (approx 0.5) vs trend.
    - Verify FFT correctly identifies period of a sine wave.

# Implementation Plan - Phase 8: User & Prop Firm Management

**Goal**: Autonomous operation with strict Prop Firm compliance.

## Proposed Changes

### Frontend (`electron-app/`)

#### [NEW] `electron-app/`
- **Purpose**: Desktop GUI for user configuration.
- **Stack**: Electron, React (optional, keep simple HTML/JS for speed), IPC.
- **Features**:
    - **Login/Register**: User identity.
    - **Prop Firm Config**: Select Firm (FTMO, MFF, etc.), Enter Credentials (Login, Server, Password).
    - **Rules Config**: Max Daily Loss, Max Total Drawdown, Profit Target, Trading Hours.
    - **Dashboard**: View account status and rule compliance.

### Backend (`sidecar/`)

#### [NEW] `app/api/user_config.py`
- **Purpose**: API endpoints to receive config from Electron.
- **Endpoints**:
    - `POST /config/prop-firm`: Save credentials and rules.
    - `GET /config/prop-firm`: Retrieve current config.

#### [NEW] `app/data/user_db.py`
- **Purpose**: SQLite database manager for user data.
- **Schema**:
    - `users`: id, name, email.
    - `prop_firms`: id, user_id, firm_name, login, server, password (encrypted).
    - `rules`: id, firm_id, max_daily_loss, max_total_loss, trading_hours.

#### [MODIFY] `app/risk/risk_manager.py`
- **Change**: Enforce Prop Firm rules.
- **Logic**:
    - Load rules from `user_db`.
    - `check_trade_allowed()`:
        - Check Daily Loss limit.
        - Check Max Drawdown limit.
        - Check Trading Hours.
    - `monitor_account()`:
        - Real-time check of equity vs limits.
        - Auto-close all if limit breached (Hard Stop).

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_prop_risk.py`
    - Mock User Config.
    - Verify trade rejection if Daily Loss limit hit.
    - Verify trade rejection if outside Trading Hours.

# Implementation Plan - Phase 7: Next-Gen Machine Learning

**Goal**: State-of-the-art predictive capabilities and optimal control.

## Proposed Changes

### Sidecar Service (`sidecar/`)

#### [NEW] `app/ml/transformer_model.py`
- **Purpose**: Advanced Time Series Forecasting.
- **Architecture**: Simplified Temporal Fusion Transformer (TFT) or Informer.
- **Features**: Multi-head attention to capture long-range dependencies in price action.
- **Input**: Sequence of (Open, High, Low, Close, Volume, Indicators).
- **Output**: Next N steps price prediction or probability of up/down.

#### [NEW] `app/ml/rl_agent.py`
- **Purpose**: Reinforcement Learning for Trade Management.
- **Algorithm**: PPO (Proximal Policy Optimization).
- **State Space**: [Current PnL, Market Volatility, RSI, MACD, Time Held].
- **Action Space**: [Hold, Close 25%, Close 50%, Close 100%, Move SL to BE].
- **Reward Function**: Change in PnL - Penalty for Drawdown.

#### [MODIFY] `app/ml/predictor.py` (or `scanner.py`)
- **Change**: Integrate Transformer predictions.
- **Logic**:
    - `get_transformer_prediction(symbol)`: Returns confidence score.
    - Combine with Random Forest/XGBoost predictions (Ensemble).

## Verification Plan

### Automated Tests
1.  **Unit Test**: `tests/test_ml_models.py`
    - Verify Transformer forward pass works with dummy data.
    - Verify RL Agent can select an action given a state.
