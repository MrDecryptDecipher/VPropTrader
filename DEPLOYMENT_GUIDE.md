# Vproptrader Deployment Guide

## 🚀 Complete Deployment Instructions

This guide will take you from installation to live trading in a structured, safe manner.

---

## Phase 1: Installation & Setup (30 minutes)

### Step 1: Install Prerequisites

#### Python 3.11+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Mac
brew install python@3.11

# Windows
# Download from python.org
```

#### Redis (Optional but Recommended)
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Mac
brew install redis
brew services start redis

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
```

#### MT5 Terminal
1. Download from your broker (VPropTrader)
2. Install and login with your demo account credentials
3. Enable AutoTrading (Tools → Options → Expert Advisors → Allow AutoTrading)
4. Add Sidecar URL to allowed list:
   - Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add: `http://localhost:8000`

### Step 2: Install Sidecar Service

```bash
cd Vproptrader/sidecar

# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Edit `.env` with your settings:
```env
# MT5 Configuration
MT5_LOGIN=your_vproptrader_login
MT5_PASSWORD=your_password
MT5_SERVER=VPropTrader-Demo
MT5_PATH=  # Leave empty for auto-detect

# FRED API (already configured)
FRED_API_KEY=6858ba9ffde019d58ee6ca8190418307

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Symbols
SYMBOLS=NAS100,XAUUSD,EURUSD

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Step 4: Test Sidecar Service

```bash
# Start the service
python -m app.main
```

You should see:
```
✓ Database connected
✓ Redis connected
✓ FAISS index created
✓ MT5 connected
✓ FRED API connected
✓ Calendar: X high-impact events loaded
✓ Sidecar Service started successfully
```

Test endpoints:
```bash
# In another terminal
curl http://localhost:8000/health
curl http://localhost:8000/api/signals
```

---

## Phase 2: MT5 EA Installation (15 minutes)

### Step 1: Copy EA Files

```bash
# Find your MT5 data folder
# Windows: C:\Users\[YourName]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\
# Mac: ~/Library/Application Support/MetaTrader 5/MQL5/

# Copy the entire mt5_ea folder
cp -r Vproptrader/mt5_ea/* [MT5_DATA_FOLDER]/MQL5/Experts/QuantSupraAI/
```

### Step 2: Compile EA

1. Open MetaEditor (F4 in MT5)
2. Navigate to Experts → QuantSupraAI → QuantSupraAI.mq5
3. Click Compile (F7)
4. Check for errors in the Toolbox window
5. Close MetaEditor

### Step 3: Configure EA

1. In MT5, open Navigator (Ctrl+N)
2. Expand "Expert Advisors"
3. Find "QuantSupraAI"
4. Drag onto a chart (any symbol)
5. In the settings dialog:
   - **Common tab**:
     - ✅ Allow live trading
     - ✅ Allow DLL imports
     - ✅ Allow WebRequest
   - **Inputs tab**:
     - SidecarURL: `http://localhost:8000`
     - PollInterval: `1500` (1.5 seconds)
     - LogOnlyMode: `true` (for testing)
     - MagicNumber: `20251025`
   - Click OK

---

## Phase 3: Testing (1-2 days)

### Day 1: Log-Only Mode

**Goal**: Verify all connections and signal generation without real trades

1. **Start Sidecar**:
   ```bash
   cd Vproptrader/sidecar
   source venv/bin/activate
   python -m app.main
   ```

2. **Start MT5 EA** (LogOnlyMode = true)

3. **Monitor Logs**:
   - Sidecar logs: `Vproptrader/sidecar/logs/`
   - MT5 logs: MT5 → Experts tab

4. **What to Check**:
   - ✅ Sidecar connects to MT5
   - ✅ FRED API fetches macro data
   - ✅ Calendar scraper gets events
   - ✅ Features are extracted (50 dimensions)
   - ✅ Signals are generated
   - ✅ EA receives signals
   - ✅ EA logs "LOG-ONLY: Would BUY/SELL..."
   - ✅ No errors in logs

5. **Expected Behavior**:
   - Signals generated every 1-2 seconds
   - Most scans return 0 signals (>90% skip rate)
   - When signals appear, they have Q* > 7.0
   - EA logs signal details but doesn't trade

### Day 2: Paper Trading

**Goal**: Execute trades on demo account, verify compliance

1. **Switch to Live Mode**:
   - Right-click EA on chart
   - Properties → Inputs
   - LogOnlyMode: `false`
   - Click OK

2. **Monitor First Trades**:
   - Watch for first signal execution
   - Verify SL/TP levels are set correctly
   - Check position size is reasonable
   - Confirm execution reports sent to Sidecar

3. **Compliance Checks**:
   - ✅ Daily loss never exceeds -$45
   - ✅ Positions close at 21:45 UTC
   - ✅ No trading on Friday after 20:00 UTC
   - ✅ No trades during news embargo
   - ✅ Max 3 positions at once
   - ✅ Profit target halts at $100

4. **Performance Monitoring**:
   ```bash
   # Check database
   sqlite3 Vproptrader/sidecar/data/vproptrader.db
   SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;
   
   # Check analytics
   curl http://localhost:8000/api/analytics/overview
   curl http://localhost:8000/api/analytics/compliance
   ```

---

## Phase 4: Model Training (After 100+ Trades)

### When to Train

Wait until you have:
- ✅ At least 100 closed trades
- ✅ Mix of wins and losses
- ✅ Multiple symbols traded
- ✅ Different market conditions

### Training Process

```python
# In Python console
cd Vproptrader/sidecar
source venv/bin/activate
python

>>> from app.ml.trainer import model_trainer
>>> import asyncio
>>> 
>>> # Train all models
>>> results = asyncio.run(model_trainer.train_all_models())
>>> 
>>> # Check results
>>> print(results)
```

Expected output:
```
Training Random Forest on 100 samples...
✓ Random Forest trained - Train Acc: 0.72, Val Acc: 0.68
Training LSTM on 80 sequences...
✓ LSTM trained - Best Val Loss: 0.0234
✓ All models trained successfully
```

### After Training

1. **Restart Sidecar** to load new models
2. **Monitor Performance** - signals should improve
3. **Retrain Weekly** or when drift detected

---

## Phase 5: Production Deployment (VPS)

### VPS Requirements

- **OS**: Ubuntu 20.04+ or Windows Server
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: 2 cores minimum
- **Storage**: 20GB SSD
- **Network**: Stable, low latency to broker

### VPS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv redis-server -y

# Clone/upload your code
scp -r Vproptrader user@vps-ip:/home/user/

# Setup Sidecar
cd /home/user/Vproptrader/sidecar
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Update with production settings
```

### Systemd Service (Linux)

Create `/etc/systemd/system/vproptrader.service`:
```ini
[Unit]
Description=Vproptrader Sidecar Service
After=network.target redis.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/Vproptrader/sidecar
Environment="PATH=/home/your_user/Vproptrader/sidecar/venv/bin"
ExecStart=/home/your_user/Vproptrader/sidecar/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vproptrader
sudo systemctl start vproptrader
sudo systemctl status vproptrader
```

### MT5 on VPS

1. Install MT5 on VPS
2. Login with your account
3. Copy EA files
4. Configure EA with VPS Sidecar URL
5. Enable AutoTrading
6. Monitor via VPS remote desktop

---

## Phase 6: Monitoring & Maintenance

### Daily Checks

1. **Morning** (before London open):
   - Check Sidecar is running
   - Verify MT5 connection
   - Review overnight logs
   - Check compliance status

2. **During Trading**:
   - Monitor open positions
   - Watch for alerts
   - Check PnL vs targets

3. **Evening** (after NY close):
   - Review daily performance
   - Check for violations
   - Verify positions closed

### Weekly Tasks

1. **Performance Review**:
   ```bash
   curl http://localhost:8000/api/analytics/overview
   curl http://localhost:8000/api/analytics/alphas
   ```

2. **Model Retraining** (if needed):
   ```python
   asyncio.run(model_trainer.train_all_models())
   ```

3. **Log Rotation**:
   ```bash
   # Logs auto-rotate, but check disk space
   du -sh Vproptrader/sidecar/logs/
   ```

4. **Database Backup**:
   ```bash
   cp Vproptrader/sidecar/data/vproptrader.db \
      backups/vproptrader_$(date +%Y%m%d).db
   ```

### Monthly Tasks

1. **Performance Analysis**:
   - Calculate Sharpe ratio
   - Review max drawdown
   - Analyze alpha performance
   - Check compliance record

2. **System Updates**:
   ```bash
   cd Vproptrader/sidecar
   source venv/bin/activate
   pip list --outdated
   # Update carefully, test in dev first
   ```

3. **Model Evaluation**:
   - Check model accuracy
   - Review feature importance
   - Assess drift detection

---

## Troubleshooting

### Sidecar Won't Start

**Issue**: Import errors
```bash
# Solution: Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Issue**: MT5 connection failed
```bash
# Solution: Check MT5 is running and credentials are correct
# Verify MT5_PATH in .env
```

**Issue**: Redis connection failed
```bash
# Solution: Start Redis or disable in config
sudo systemctl start redis
# OR set REDIS_HOST= in .env to disable
```

### EA Not Trading

**Issue**: No signals received
- Check Sidecar is running: `curl http://localhost:8000/health`
- Verify URL in EA settings
- Check MT5 WebRequest is allowed

**Issue**: Signals received but not executed
- Check LogOnlyMode is false
- Verify AutoTrading is enabled
- Check account has sufficient margin

**Issue**: Trades rejected
- Check spread conditions
- Verify lot size is valid
- Check SL/TP distances meet minimum

### Performance Issues

**Issue**: Slow signal generation
- Check Redis is running
- Verify feature caching is working
- Monitor CPU/RAM usage

**Issue**: High skip rate (>95%)
- Normal! System is selective
- Lower Q* threshold if needed (not recommended)
- Check market conditions

---

## Emergency Procedures

### Kill Switch

**Immediate Stop**:
1. In MT5: Click "AutoTrading" button (turns red)
2. Or: Remove EA from chart
3. Or: Close MT5

**Close All Positions**:
```python
# Via Sidecar
from app.data.mt5_client import mt5_client
mt5_client.connect()
# Close all manually in MT5
```

### System Recovery

**If Sidecar Crashes**:
```bash
# Check logs
tail -100 Vproptrader/sidecar/logs/errors_*.log

# Restart
sudo systemctl restart vproptrader
```

**If Database Corrupted**:
```bash
# Restore from backup
cp backups/vproptrader_YYYYMMDD.db \
   Vproptrader/sidecar/data/vproptrader.db
```

---

## Success Metrics

### Week 1 Targets
- ✅ System runs 24/7 without crashes
- ✅ Zero rule violations
- ✅ At least 10 trades executed
- ✅ Drawdown < 2%

### Month 1 Targets
- ✅ 100+ trades for model training
- ✅ Positive total PnL
- ✅ Sharpe ratio > 2.0
- ✅ Max drawdown < 5%

### Challenge Completion
- ✅ $100 profit target reached
- ✅ Zero rule violations
- ✅ 4+ trading days
- ✅ Consistency maintained

---

## Support & Resources

### Logs Location
- Sidecar: `Vproptrader/sidecar/logs/`
- MT5: MT5 → Experts tab
- Database: `Vproptrader/sidecar/data/vproptrader.db`

### API Documentation
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Configuration Files
- Sidecar: `Vproptrader/sidecar/.env`
- MT5 EA: In EA settings dialog

---

## Next Steps

1. ✅ Complete Phase 1-2 (Installation)
2. ✅ Run Phase 3 (Testing) for 1-2 days
3. ✅ Collect 100+ trades
4. ✅ Train models (Phase 4)
5. ✅ Deploy to VPS (Phase 5)
6. ✅ Monitor daily (Phase 6)
7. 🎯 Pass VPropTrader challenge!

**Good luck with your trading! The system is ready.** 🚀
