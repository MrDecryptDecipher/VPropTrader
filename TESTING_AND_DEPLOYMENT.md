# Testing and Deployment Guide

## Overview

This guide covers the complete testing, deployment, and go-live procedures for the Quant Ω Supra AI system.

---

## Phase 1: Testing

### 1.1 Unit Tests

Run all unit tests to verify core functionality:

```bash
# Navigate to project root
cd Vproptrader

# Run test suite
bash scripts/run_tests.sh
```

**Tests included:**
- ✅ ML inference speed (<1ms)
- ✅ Hard governor enforcement
- ✅ Soft governor behavior
- ✅ Trading schedule validation
- ✅ API endpoint functionality

**Expected results:**
- All tests pass
- Inference speed < 1ms
- API latency < 100ms
- Zero failures

### 1.2 Integration Tests

Test component integration:

```bash
# Start Sidecar service
cd sidecar
python -m app.main

# In another terminal, run integration tests
cd ..
python tests/test_integration.py
```

**Tests included:**
- ✅ EA → Sidecar communication
- ✅ Signal generation pipeline
- ✅ Execution reporting
- ✅ Dashboard data flow
- ✅ WebSocket streaming

### 1.3 Paper Trading (1 Week Minimum)

**Setup:**
1. Configure MT5 demo account
2. Start Sidecar service
3. Attach EA to charts (log-only mode)
4. Start dashboard
5. Monitor for 1 week

**Daily checklist:**
- [ ] Review all generated signals
- [ ] Check ML predictions
- [ ] Verify compliance (zero violations)
- [ ] Monitor alpha performance
- [ ] Review execution quality
- [ ] Check retraining logs

**Success criteria:**
- Zero system crashes
- Zero rule violations
- All signals valid
- Latency < 400ms
- Inference < 1ms
- Dashboard updates correctly

---

## Phase 2: Deployment

### 2.1 VPS Setup (Ubuntu 20.04+)

**Initial setup:**
```bash
# SSH into VPS
ssh root@your-vps-ip

# Run setup script
wget https://your-repo/deploy/setup_vps.sh
sudo bash setup_vps.sh
```

**What it does:**
- Installs Python 3.11
- Installs Redis
- Configures firewall
- Creates application user
- Sets up directories

### 2.2 Deploy Sidecar Service

```bash
# Clone repository
cd /opt/vproptrader
git clone https://your-repo.git .

# Run deployment script
bash deploy/deploy_sidecar.sh
```

**Configuration:**
```bash
# Edit environment variables
nano sidecar/.env

# Required variables:
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
FRED_API_KEY=your_key
REDIS_HOST=127.0.0.1
DATABASE_PATH=/var/lib/vproptrader/data/trades.db
```

**Verify deployment:**
```bash
# Check service status
sudo systemctl status vprop-sidecar

# Test health endpoint
curl http://localhost:8000/health | python3 -m json.tool

# View logs
sudo journalctl -u vprop-sidecar -f
```

### 2.3 Deploy Dashboard

**Option A: Vercel (Recommended)**
```bash
cd dashboard

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

**Option B: Self-hosted**
```bash
cd dashboard

# Build
npm run build

# Start
npm start
```

**Configure environment:**
```bash
# Edit .env.local
NEXT_PUBLIC_API_URL=http://your-vps-ip:8000
```

### 2.4 Configure MT5 EA (Windows)

**Setup:**
1. Copy `mt5_ea` folder to MT5 `Experts` directory
2. Edit `config.mqh`:
   ```cpp
   input string SidecarURL = "http://your-vps-ip:8000";
   input string TradingSymbols = "NAS100,XAUUSD,EURUSD";
   input bool LogOnlyMode = true;  // Start in log-only mode
   ```
3. Compile in MetaEditor
4. Attach to charts

---

## Phase 3: Go-Live

### 3.1 Pre-Live Checks

Run automated pre-flight checks:

```bash
bash scripts/go_live.sh log-only
```

**Checklist:**
- [ ] Sidecar service running
- [ ] Redis running
- [ ] Database accessible
- [ ] ML models loaded
- [ ] Dashboard accessible
- [ ] All API endpoints responding
- [ ] MT5 EA connected

### 3.2 Log-Only Mode (First Session)

**Purpose:** Verify system without executing trades

**Steps:**
1. Ensure `LogOnlyMode = true` in `config.mqh`
2. Attach EA to charts
3. Monitor for 1 full trading session
4. Review all logs

**What to check:**
- ✅ Signals generated correctly
- ✅ Risk calculations accurate
- ✅ Compliance checks working
- ✅ Execution quality filters active
- ✅ Dashboard updates in real-time
- ✅ No errors in logs

**Review:**
```bash
# View Sidecar logs
sudo journalctl -u vprop-sidecar -n 1000

# Check MT5 EA logs
# Open MT5 → Experts tab

# Review dashboard
# Open browser → your-dashboard-url
```

### 3.3 Enable Live Trading

**⚠️ CRITICAL: Only proceed if log-only mode was successful**

**Steps:**
1. Edit `config.mqh`:
   ```cpp
   input bool LogOnlyMode = false;  // Enable live trading
   ```
2. Recompile EA
3. Reload EA on charts
4. Enable AutoTrading in MT5
5. Run go-live script:
   ```bash
   bash scripts/go_live.sh live
   ```

**First Hour Monitoring:**
- [ ] Watch for any errors
- [ ] Verify first trade execution
- [ ] Check execution quality (latency, slippage)
- [ ] Monitor compliance panel
- [ ] Verify PnL tracking
- [ ] Check stop loss/take profit placement

**First Day Monitoring:**
- [ ] Monitor all trading sessions
- [ ] Review each trade
- [ ] Verify zero violations
- [ ] Check performance metrics
- [ ] Review logs for warnings
- [ ] Verify nightly retrain scheduled

---

## Phase 4: Monitoring

### 4.1 Real-Time Monitoring

**Terminal dashboard:**
```bash
bash scripts/monitor.sh
```

**Shows:**
- System status (Sidecar, Redis, Dashboard)
- Account overview (equity, PnL, trades)
- Compliance status
- Active signals
- System resources

### 4.2 Log Monitoring

**Sidecar logs:**
```bash
# Real-time
sudo journalctl -u vprop-sidecar -f

# Last 100 lines
sudo journalctl -u vprop-sidecar -n 100

# Errors only
sudo journalctl -u vprop-sidecar -p err
```

**Trade logs:**
```bash
# Daily trades
cat /var/log/vproptrader/trades_$(date +%Y-%m-%d).jsonl

# Retrain logs
cat /var/log/vproptrader/retrain.log
```

### 4.3 Dashboard Monitoring

**Access:** `http://your-dashboard-url`

**Key pages:**
- **Overview**: Real-time equity, PnL, drawdown
- **Compliance**: All 7 VProp rules with status lights
- **Alphas**: Performance by strategy
- **Risk**: VaR, ES95, exposure
- **Learning**: Model performance, drift detection

### 4.4 Alerts

**Set up email alerts for:**
- Service downtime
- Hard governor triggers
- High latency (>400ms)
- API errors
- Compliance violations

**Example (using systemd):**
```bash
# Create alert script
sudo nano /usr/local/bin/vprop-alert.sh

#!/bin/bash
echo "VProp Alert: $1" | mail -s "VProp System Alert" your@email.com

# Make executable
sudo chmod +x /usr/local/bin/vprop-alert.sh

# Add to systemd service
sudo nano /etc/systemd/system/vprop-sidecar.service

[Service]
OnFailure=vprop-alert@%n.service
```

---

## Phase 5: Maintenance

### 5.1 Daily Tasks

- [ ] Check service health
- [ ] Review overnight logs
- [ ] Verify compliance status
- [ ] Monitor performance metrics
- [ ] Check for any alerts

### 5.2 Weekly Tasks

- [ ] Analyze weekly performance
- [ ] Review alpha weights
- [ ] Check model retraining logs
- [ ] Verify drift detection
- [ ] Review execution quality
- [ ] Update documentation

### 5.3 Monthly Tasks

- [ ] Review system performance
- [ ] Optimize configurations
- [ ] Update dependencies
- [ ] Clean old logs
- [ ] Backup databases
- [ ] Security audit

---

## Emergency Procedures

### Kill Switch

**Method 1: Dashboard**
- Click kill switch button
- Confirms all positions closed

**Method 2: MT5**
- Disable AutoTrading
- Manually close positions

**Method 3: Sidecar**
```bash
sudo systemctl stop vprop-sidecar
```

### Hard Governor Trigger

**⚠️ DO NOT OVERRIDE**

1. Review logs to understand cause
2. All positions automatically closed
3. EA automatically disabled
4. Analyze what went wrong
5. Fix issue before re-enabling
6. Document incident

### Service Recovery

**Sidecar crashed:**
```bash
# Check status
sudo systemctl status vprop-sidecar

# View recent logs
sudo journalctl -u vprop-sidecar -n 100

# Restart
sudo systemctl restart vprop-sidecar

# If persistent, check:
# - VPS resources
# - Network connectivity
# - Database connections
# - Redis status
```

**Redis crashed:**
```bash
sudo systemctl restart redis-server
sudo systemctl restart vprop-sidecar
```

**Database corruption:**
```bash
# Restore from backup
cp /var/lib/vproptrader/backups/trades_YYYYMMDD.db \
   /var/lib/vproptrader/data/trades.db

# Restart service
sudo systemctl restart vprop-sidecar
```

---

## Performance Benchmarks

### Expected Metrics

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Inference Speed | <0.5ms | <1ms | >1ms |
| API Latency | <50ms | <100ms | >100ms |
| Execution Latency | <200ms | <400ms | >400ms |
| Daily Returns | 1.2-1.8% | 0.8-2.0% | <0% or >2.5% |
| Max Drawdown | <0.6% | <1.0% | >1.5% |
| Hit Rate | ~65% | >60% | <55% |
| Sharpe Ratio | >4.0 | >3.0 | <2.0 |
| Rule Violations | 0 | 0 | >0 |

### System Resources

**VPS Requirements:**
- CPU: 2+ cores
- RAM: 4GB minimum, 8GB recommended
- Disk: 50GB SSD
- Network: 100Mbps+

**Monitoring:**
```bash
# CPU usage
top -bn1 | grep "Cpu(s)"

# Memory usage
free -h

# Disk usage
df -h

# Network
iftop
```

---

## Troubleshooting

### Common Issues

**1. Sidecar won't start**
- Check logs: `sudo journalctl -u vprop-sidecar -n 50`
- Verify .env file exists and is correct
- Check Redis is running
- Verify Python dependencies installed

**2. EA not connecting**
- Verify SidecarURL in config.mqh
- Check firewall allows port 8000
- Test: `curl http://your-vps-ip:8000/health`
- Check MT5 Experts log for errors

**3. No signals generated**
- Check MT5 connection to broker
- Verify symbols are correct
- Check trading schedule (London/NY sessions only)
- Review scanner logs

**4. High latency**
- Check VPS resources
- Verify network connectivity
- Review API endpoint performance
- Consider upgrading VPS

**5. Model inference slow**
- Verify ONNX models loaded
- Check model file sizes
- Review inference logs
- Consider model optimization

---

## Success Criteria

### Week 1
- [ ] Zero system crashes
- [ ] Zero rule violations
- [ ] All trades executed successfully
- [ ] Latency < 400ms
- [ ] Inference speed < 1ms
- [ ] Dashboard updates in real-time

### Month 1
- [ ] Daily returns: 1.2% - 1.8%
- [ ] Max drawdown < 1.5%
- [ ] Hit rate ~65%
- [ ] Sharpe ratio ≥ 4.0
- [ ] Zero rule violations
- [ ] Model retraining successful

### VProp Challenge Pass
- [ ] Profit target reached ($100)
- [ ] Zero rule violations
- [ ] Minimum 4 trading days
- [ ] Max daily loss not exceeded
- [ ] Consistency maintained
- [ ] Ready for funded account

---

## Support

**Documentation:**
- README.md - System overview
- DEPLOYMENT_GUIDE.md - Detailed deployment
- QUICK_START.md - Quick setup guide
- MT5_EA_COMPLETE_GUIDE.md - EA documentation

**Logs:**
- Sidecar: `/var/log/vproptrader/sidecar.log`
- Trades: `/var/log/vproptrader/trades_YYYY-MM-DD.jsonl`
- Retrain: `/var/log/vproptrader/retrain.log`

**Commands:**
```bash
# Service management
sudo systemctl start|stop|restart|status vprop-sidecar

# Logs
sudo journalctl -u vprop-sidecar -f

# Monitoring
bash scripts/monitor.sh

# Health check
curl http://localhost:8000/health | python3 -m json.tool
```

---

*Last Updated: 2025-10-25*
*Version: 1.0.0*
