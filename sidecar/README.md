# Sidecar AI Service

Python FastAPI service for ML inference, data processing, and model retraining.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run service
python -m app.main
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `GET /api/signals` - Get trading signals (polled by EA)
- `POST /api/executions` - Report trade executions
- `GET /api/analytics/overview` - Overview metrics
- `GET /api/analytics/compliance` - Compliance status
- `GET /api/analytics/alphas` - Alpha performance
- `GET /api/analytics/risk` - Risk metrics
- `WebSocket /ws/live` - Live data stream

## Directory Structure

```
app/
├── api/          # REST endpoints
├── core/         # Configuration, logging
├── data/         # Data ingestion & processing
├── ml/           # ML models & training
├── memory/       # Short/long-term memory
├── scanner/      # Strategy scanner & alphas
├── risk/         # Position sizing & risk
└── analytics/    # Metrics & logging
```

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black app/
```
