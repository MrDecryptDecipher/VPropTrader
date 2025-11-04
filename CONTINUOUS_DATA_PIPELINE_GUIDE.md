# Continuous Data Pipeline - Deployment & Operations Guide

## Overview

The Continuous Data Pipeline is a high-performance, real-time market data collection system that:
- Collects data every 1 second from multiple sources
- Validates and normalizes all incoming data
- Stores data in Redis (real-time cache) and SQLite (historical storage)
- Computes technical indicators incrementally
- Provides <5ms data access for signal generation
- Handles source failures with automatic fallback
- Operates 24/7 with circuit breaker protection

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  High-Frequency Orchestrator                 │
│                    (1-second collection loop)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌───▼────┐    ┌───▼────┐
   │ Yahoo   │    │ Alpha  │    │ Twelve │
   │ Finance │    │Vantage │    │  Data  │
   └────┬────┘    └───┬────┘    └───┬────┘
        │             │              │
        └─────────────┼──────────────┘
                      │
              ┌───────▼────────┐
              │  Data Validator │
              │  (Quality Check)│
              └───────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        │                           │
   ┌────▼────┐              ┌──────▼──────┐
   │  Redis  │              │   SQLite    │
   │  Cache  │              │  Historical │
   │ (5000   │              │   Storage   │
   │  bars)  │              │             │
   └────┬────┘              └──────┬──────┘
        │                          │
        └──────────┬───────────────┘
                   │
          ┌────────▼─────────┐
          │ Feature Engine   │
          │ (Incremental)    │
          └────────┬─────────┘
                   │
          ┌────────▼─────────┐
          │  Scanner/Signals │
          │   (<50ms target) │
          └──────────────────┘
```

## Installation

### 1. Prerequisites

```bash
# Python 3.10+
python --version

# Redis Server
sudo apt-get install redis-server
redis-server --version

# TA-Lib (for technical indicators)
sudo apt-get install ta-lib
```

### 2. Install Python Dependencies

```bash
cd Vproptrader/sidecar
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create or update `.env` file:

```bash
# Data Pipeline Configuration
COLLECTION_INTERVAL=1              # Collection interval in seconds
MAX_BARS_CACHE=5000               # Max bars to keep in Redis per symbol
BATCH_WRITE_INTERVAL=10           # SQLite batch write interval (seconds)
FEATURE_CACHE_TTL=2               # Feature cache TTL (seconds)
REDIS_POOL_SIZE=20                # Redis connection pool size
HTTP_POOL_SIZE=10                 # HTTP connection pool size

# Data Source API Keys (Optional - Free tiers available)
ALPHAVANTAGE_API_KEY=your_key_here    # 5 calls/min free
TWELVEDATA_API_KEY=your_key_here      # 800 calls/day free
POLYGON_API_KEY=your_key_here         # Premium only

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                   # Leave empty if no password

# SQLite Configuration
DATABASE_PATH=./data/vproptrader.db

# Trading Symbols (Generic symbols - will be mapped to broker symbols)
SYMBOLS=NAS100,XAUUSD,EURUSD
```

### 4. Initialize Database

```bash
# Create data directory
mkdir -p data

# Database will be created automatically on first run
```

### 5. Start Redis

```bash
# Start Redis server
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

## Starting the Pipeline

### Development Mode

```bash
cd Vproptrader/sidecar
python -m app.main
```

### Production Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

# Or using PM2 (recommended)
pm2 start ecosystem.config.js --only sidecar
pm2 logs sidecar
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response includes:
- Overall system status
- Component health (Redis, SQLite, MT5, etc.)
- Data pipeline status
- Data freshness metrics
- Performance metrics
- Data source health

### Metrics Endpoint

```bash
# JSON format
curl http://localhost:8000/metrics/json

# Prometheus format
curl http://localhost:8000/metrics
```

Key metrics:
- `data_points_collected`: Total data points collected
- `cache_hit_rate`: Redis cache hit rate
- `collection_cycle_latency`: Collection cycle latency (p50, p95, p99)
- `signal_generation_latency`: Signal generation latency
- `api_calls_*`: API call statistics per source
- `data_freshness_*`: Data age per symbol

### Logs

```bash
# View logs in real-time
tail -f logs/sidecar.log

# Search for errors
grep ERROR logs/sidecar.log

# Monitor collection cycles
grep "Collection cycle" logs/sidecar.log
```

## Data Sources

### Priority Order (Automatic Fallback)

1. **Yahoo Finance** (Priority 0)
   - Free, unlimited
   - No API key required
   - Good for indices and forex

2. **Alpha Vantage** (Priority 1)
   - Free tier: 5 calls/minute
   - Requires API key
   - Good data quality

3. **Twelve Data** (Priority 2)
   - Free tier: 800 calls/day
   - Requires API key
   - Wide symbol coverage

4. **Polygon** (Priority 3)
   - Premium only
   - Real-time WebSocket support
   - Best for high-frequency data

### Getting API Keys

**Alpha Vantage:**
1. Visit: https://www.alphavantage.co/support/#api-key
2. Sign up for free API key
3. Add to `.env`: `ALPHAVANTAGE_API_KEY=your_key`

**Twelve Data:**
1. Visit: https://twelvedata.com/pricing
2. Sign up for free tier
3. Add to `.env`: `TWELVEDATA_API_KEY=your_key`

**Polygon:**
1. Visit: https://polygon.io/pricing
2. Subscribe to paid plan
3. Add to `.env`: `POLYGON_API_KEY=your_key`

## Symbol Mapping

The system uses **generic symbols** internally and maps them to broker-specific symbols for execution.

### Generic Symbols (Used for Data Collection & Analysis)
- `NAS100` - NASDAQ 100
- `XAUUSD` - Gold vs USD
- `EURUSD` - EUR/USD
- `GBPUSD` - GBP/USD
- `US30` - Dow Jones
- `US500` - S&P 500

### Broker Symbols (Used for MT5 Execution)
- `US100.e` - NASDAQ 100 (ECN)
- `XAUUSD` - Gold vs USD
- `EURUSD` - EUR/USD
- `GBPUSD` - GBP/USD
- `US30` - Dow Jones
- `US500` - S&P 500

### Data Provider Symbols
Each provider has its own symbol format:
- Yahoo: `NQ=F`, `GC=F`, `EURUSD=X`
- Alpha Vantage: `NDX`, `XAU/USD`, `EUR/USD`
- Twelve Data: `NAS100`, `XAU/USD`, `EUR/USD`
- Polygon: `I:NDX`, `C:XAUUSD`, `C:EURUSD`

**The system handles all translations automatically.**

## Circuit Breaker

The circuit breaker protects against cascading failures when data sources become unavailable.

### States

1. **CLOSED** (Normal Operation)
   - All requests pass through
   - Failures are counted

2. **OPEN** (Failing Fast)
   - Requests fail immediately
   - No calls to failing service
   - Timeout: 60 seconds

3. **HALF_OPEN** (Testing Recovery)
   - Single test request allowed
   - Success → CLOSED
   - Failure → OPEN

### Configuration

- Failure Threshold: 5 failures
- Timeout: 60 seconds
- Automatic recovery testing

### Monitoring Circuit Breakers

```bash
curl http://localhost:8000/health | jq '.data_sources'
```

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Collection Cycle | <100ms | ~50-80ms |
| Cache Access | <5ms | ~1-3ms |
| Feature Computation | <100ms | ~20-50ms |
| Signal Generation | <50ms | ~30-40ms |
| End-to-End Latency | <200ms | ~100-150ms |

## Troubleshooting

### Data Not Collecting

**Check orchestrator status:**
```bash
curl http://localhost:8000/health | jq '.components.data_pipeline'
```

**Check logs:**
```bash
grep "orchestrator" logs/sidecar.log
```

**Common causes:**
- Redis not running
- No API keys configured
- All data sources failing
- Network connectivity issues

### Stale Data

**Check data freshness:**
```bash
curl http://localhost:8000/health | jq '.components.data_pipeline.data_freshness_seconds'
```

**If data is stale (>10 seconds):**
1. Check data source health
2. Verify API keys are valid
3. Check rate limits
4. Review circuit breaker status

### High Latency

**Check performance metrics:**
```bash
curl http://localhost:8000/metrics/json | jq '.histograms'
```

**Common causes:**
- Slow data source responses
- Redis connection issues
- High system load
- Network latency

### Circuit Breakers Open

**Check which sources are failing:**
```bash
curl http://localhost:8000/health | jq '.data_sources'
```

**Recovery steps:**
1. Wait for automatic recovery (60 seconds)
2. Check API key validity
3. Verify rate limits not exceeded
4. Check data source status pages

### Redis Connection Issues

**Test Redis connection:**
```bash
redis-cli ping
```

**Check Redis logs:**
```bash
tail -f /var/log/redis/redis-server.log
```

**Restart Redis:**
```bash
sudo systemctl restart redis-server
```

### SQLite Database Issues

**Check database file:**
```bash
ls -lh data/vproptrader.db
sqlite3 data/vproptrader.db "SELECT COUNT(*) FROM market_data;"
```

**Backup database:**
```bash
cp data/vproptrader.db data/vproptrader.db.backup
```

## Testing

### Run Unit Tests

```bash
cd Vproptrader/sidecar
python test_data_pipeline.py
```

### Run Integration Tests

```bash
pytest test_data_pipeline.py::test_integration_data_flow -v
```

### Manual Testing

```bash
# Test data collection
curl http://localhost:8000/health

# Test signal generation
curl "http://localhost:8000/api/signals?equity=1000"

# Check metrics
curl http://localhost:8000/metrics/json
```

## Maintenance

### Daily Tasks

1. Monitor data freshness
2. Check circuit breaker status
3. Review error logs
4. Verify API rate limits

### Weekly Tasks

1. Review performance metrics
2. Check database size
3. Analyze data quality scores
4. Update API keys if needed

### Monthly Tasks

1. Backup SQLite database
2. Review and optimize queries
3. Update dependencies
4. Performance tuning

## Backup & Recovery

### Backup SQLite Database

```bash
# Create backup
sqlite3 data/vproptrader.db ".backup data/vproptrader_$(date +%Y%m%d).db"

# Compress backup
gzip data/vproptrader_$(date +%Y%m%d).db
```

### Restore from Backup

```bash
# Stop sidecar
pm2 stop sidecar

# Restore database
gunzip data/vproptrader_20240101.db.gz
cp data/vproptrader_20240101.db data/vproptrader.db

# Start sidecar
pm2 start sidecar
```

### Redis Backup

```bash
# Redis automatically saves to dump.rdb
# Copy dump file
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
```

## Performance Optimization

### Redis Optimization

```bash
# Edit redis.conf
sudo nano /etc/redis/redis.conf

# Recommended settings:
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""  # Disable RDB snapshots for performance
```

### SQLite Optimization

```sql
-- Run these periodically
PRAGMA optimize;
VACUUM;
ANALYZE;
```

### System Optimization

```bash
# Increase file descriptors
ulimit -n 65536

# Optimize network settings
sudo sysctl -w net.core.somaxconn=1024
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=2048
```

## Support

For issues or questions:
1. Check logs: `logs/sidecar.log`
2. Review health endpoint: `/health`
3. Check metrics: `/metrics/json`
4. Review this guide
5. Contact system administrator

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Multi-source data collection
- Circuit breaker protection
- Symbol mapping
- Real-time caching
- Historical storage
- Incremental feature computation
- Comprehensive monitoring
