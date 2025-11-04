# Quant Ω Supra AI - Memory-Adaptive Prop Trading System

A fully automated, self-learning research and execution framework for MT5 prop trading accounts.

## Architecture

- **MT5 Expert Advisor (MQL5)**: Trade execution, risk management, compliance guardrails
- **Sidecar AI Service (Python/FastAPI)**: ML inference, data processing, model retraining
- **Web Dashboard (Next.js)**: Real-time monitoring, analytics, compliance visualization

## Features

- Trades only on A/A+ setups (>90% rejection rate)
- Strict VPropTrader compliance (max DD < 1%, daily loss < 5%)
- Self-learning memory with nightly model retraining
- Multi-model ML ensemble (Random Forest, LSTM, GBT, Autoencoder, Bandit)
- Real-time analytics dashboard with compliance monitoring

## Project Structure

```
Vproptrader/
├── sidecar/              # Python FastAPI service
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── core/         # Configuration, logging
│   │   ├── data/         # Data ingestion & processing
│   │   ├── ml/           # ML models & training
│   │   ├── memory/       # Short/long-term memory
│   │   ├── scanner/      # Strategy scanner & alphas
│   │   ├── risk/         # Position sizing & risk
│   │   └── analytics/    # Metrics & logging
│   ├── models/           # Trained ONNX models
│   ├── data/             # SQLite, logs
│   └── requirements.txt
├── mt5_ea/               # MT5 Expert Advisor (MQL5)
│   ├── QuantSupraAI.mq5
│   ├── Include/
│   │   ├── RiskManager.mqh
│   │   ├── TradeEngine.mqh
│   │   ├── Governors.mqh
│   │   └── RestClient.mqh
│   └── config.mqh
├── dashboard/            # Next.js web dashboard
│   ├── src/
│   │   ├── app/          # Pages
│   │   ├── components/   # React components
│   │   ├── lib/          # API client, utils
│   │   └── types/        # TypeScript types
│   └── package.json
└── docs/                 # Documentation
```

## Quick Start

### 1. Sidecar Service

```bash
cd Vproptrader/sidecar
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # Configure API keys
python -m app.main
```

### 2. Dashboard

```bash
cd Vproptrader/dashboard
npm install
cp .env.example .env.local
npm run dev
```

### 3. MT5 EA

1. Copy `mt5_ea/` to MT5 `MQL5/Experts/` directory
2. Compile in MetaEditor
3. Configure Sidecar URL in EA settings
4. Attach to chart (NAS100, XAUUSD, or EURUSD)

## Configuration

See `.env.example` files in each component for required environment variables.

## Performance Targets

- Daily Return: 1.2-1.8%
- Max Intraday DD: ≤ 0.6%
- Peak DD: ≤ 1.5%
- Hit Rate: ~65%
- Sharpe Ratio: ≥ 4.0
- Rule Violations: 0

## License

Proprietary - All Rights Reserved
