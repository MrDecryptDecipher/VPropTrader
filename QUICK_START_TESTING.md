# Quick Start - Testing & Deployment

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.11+
- Redis server
- MT5 terminal (for EA testing)
- Node.js 18+ (for dashboard)

---

## Step 1: Run Tests (2 minutes)

```bash
cd Vproptrader

# Run all tests
bash scripts/run_tests.sh
```

**Expected output:**
```
✓ ML Inference tests passed
✓ Governor tests passed
✓ Integration tests passed
✓ All tests passed!
```

---

## Step 2: Start Sidecar (1 minute)

```bash
cd sidecar

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit with your credentials
nano .env

# Start service
python -m app.main
```

**Verify:**
```bash
curl http://localhost:8000/health
```

---

## Step 3: Start Dashboard (1 minute)

```bash
cd dashboard

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit API URL
nano .env.local
# Set: NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dashboard
npm run dev
```

**Access:** http://localhost:3000

---

## Step 4: Configure MT5 EA (1 minute)

1. Copy `mt5_ea` folder to MT5 `Experts` directory
2. Edit `config.mqh`:
   ```cpp
   input string SidecarURL = "http://localhost:8000";
   input bool LogOnlyMode = true;  // Start in log-only mode
   ```
3. Compile in MetaEditor
4. Attach to chart (NAS100, XAUUSD, or EURUSD)

---

## Step 5: Monitor (Real-time)

```bash
# Terminal monitoring
bash scripts/monitor.sh
```

**Or use Dashboard:**
- Overview: http://localhost:3000
- Compliance: http://localhost:3000/compliance
- Alphas: http://localhost:3000/alphas
- Risk: http://localhost:3000/risk

---

## Quick Commands

**Start Everything:**
```bash
# Terminal 1: Sidecar
cd sidecar && source venv/bin/activate && python -m app.main

# Terminal 2: Dashboard
cd dashboard && npm run dev

# Terminal 3: Monitor
bash scripts/monitor.sh
```

**Run Tests:**
```bash
bash scripts/run_tests.sh
```

**Check Health:**
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

**View Logs:**
```bash
# Sidecar logs
tail -f sidecar/logs/app.log

# Trade logs
tail -f sidecar/logs/trades_$(date +%Y-%m-%d).jsonl
```

---

## Production Deployment

### VPS Setup (5 minutes)
```bash
# SSH to VPS
ssh root@your-vps-ip

# Run setup
wget https://your-repo/deploy/setup_vps.sh
sudo bash setup_vps.sh
```

### Deploy Sidecar (3 minutes)
```bash
cd /opt/vproptrader
git clone https://your-repo.git .
bash deploy/deploy_sidecar.sh
```

### Deploy Dashboard (2 minutes)
```bash
cd dashboard
npm install -g vercel
vercel --prod
```

### Configure MT5 EA (2 minutes)
1. Edit `config.mqh` with production Sidecar URL
2. Set `LogOnlyMode = true` initially
3. Compile and attach to charts

---

## Go-Live Procedure

### 1. Pre-Flight Checks
```bash
bash scripts/go_live.sh log-only
```

### 2. Log-Only Mode (1 session)
- Monitor all signals
- Verify compliance
- Review logs
- Check dashboard

### 3. Enable Live Trading
```bash
# Edit config.mqh
LogOnlyMode = false

# Recompile EA
# Reload on charts
# Enable AutoTrading

# Run go-live
bash scripts/go_live.sh live
```

### 4. Monitor
```bash
bash scripts/monitor.sh
```

---

## Troubleshooting

**Sidecar won't start:**
```bash
# Check logs
tail -f sidecar/logs/app.log

# Verify Redis
redis-cli ping

# Check .env file
cat sidecar/.env
```

**EA not connecting:**
```bash
# Test Sidecar
curl http://localhost:8000/health

# Check MT5 Experts log
# Verify SidecarURL in config.mqh
```

**No signals:**
```bash
# Check trading schedule (London/NY sessions only)
# Verify symbols in config.mqh
# Check scanner logs
```

---

## Emergency Stop

**Method 1: Dashboard**
- Click kill switch button

**Method 2: MT5**
- Disable AutoTrading

**Method 3: Sidecar**
```bash
sudo systemctl stop vprop-sidecar
```

---

## Success Checklist

**Testing Phase:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Sidecar starts successfully
- [ ] Dashboard loads correctly
- [ ] EA connects to Sidecar
- [ ] Signals generated

**Paper Trading:**
- [ ] 1 week of log-only mode
- [ ] Zero violations
- [ ] All signals valid
- [ ] Performance acceptable

**Production:**
- [ ] VPS deployed
- [ ] Sidecar running as service
- [ ] Dashboard deployed
- [ ] EA configured
- [ ] Monitoring active

**Go-Live:**
- [ ] Pre-flight checks pass
- [ ] Log-only mode successful
- [ ] Live trading enabled
- [ ] First trade executed
- [ ] Compliance verified

---

## Support

**Documentation:**
- `TESTING_AND_DEPLOYMENT.md` - Complete guide
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step
- `IMPLEMENTATION_COMPLETE_FINAL.md` - Full details

**Scripts:**
- `scripts/run_tests.sh` - Run all tests
- `scripts/go_live.sh` - Go-live procedures
- `scripts/monitor.sh` - Real-time monitoring

**Logs:**
- Sidecar: `sidecar/logs/app.log`
- Trades: `sidecar/logs/trades_YYYY-MM-DD.jsonl`
- MT5: Check Experts tab

---

## Next Steps

1. ✅ Run tests
2. ✅ Start local environment
3. ✅ Verify all components
4. 📊 Paper trade for 1 week
5. 🚀 Deploy to production
6. 🎯 Go live on VProp account

---

*Quick Start Guide*
*Version: 1.0.0*
*Last Updated: 2025-10-25*
