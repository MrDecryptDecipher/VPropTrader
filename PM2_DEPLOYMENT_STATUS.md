# VPropTrader PM2 Deployment Status

## ✅ System Successfully Deployed

**Deployment Date**: October 28, 2025  
**Public IP**: 3.111.22.56  
**Project Path**: /home/ubuntu/Sandeep/projects/Vproptrader

---

## 🚀 Running Services

### 1. Sidecar API (Backend)
- **PM2 Name**: `vproptrader-sidecar`
- **Port**: 8000
- **Status**: ✅ Online
- **Public URL**: http://3.111.22.56:8000
- **Health Check**: http://3.111.22.56:8000/health
- **API Docs**: http://3.111.22.56:8000/docs
- **Technology**: Python 3.12 + FastAPI + Uvicorn
- **Auto-restart**: Enabled

### 2. Dashboard (Frontend)
- **PM2 Name**: `vproptrader-dashboard`
- **Port**: 4001
- **Status**: ✅ Online
- **Public URL**: http://3.111.22.56:4001
- **Technology**: Next.js 14 (Development Mode)
- **Auto-restart**: Enabled

---

## 📊 Available Endpoints

### Dashboard Pages
- **Main Dashboard**: http://3.111.22.56:4001/
- **Trades**: http://3.111.22.56:4001/trades
- **Performance**: http://3.111.22.56:4001/performance
- **Risk Management**: http://3.111.22.56:4001/risk
- **Alpha Strategies**: http://3.111.22.56:4001/alphas
- **Compliance**: http://3.111.22.56:4001/compliance

### API Endpoints
- **Health**: GET http://3.111.22.56:8000/health
- **Signals**: GET http://3.111.22.56:8000/api/signals
- **Analytics Overview**: GET http://3.111.22.56:8000/api/analytics/overview
- **Compliance Status**: GET http://3.111.22.56:8000/api/analytics/compliance
- **Alpha Performance**: GET http://3.111.22.56:8000/api/analytics/alphas
- **Risk Metrics**: GET http://3.111.22.56:8000/api/analytics/risk
- **WebSocket**: ws://3.111.22.56:8000/ws/live

---

## 🔧 PM2 Management Commands

### View Status
```bash
pm2 list
pm2 status vproptrader-sidecar
pm2 status vproptrader-dashboard
```

### View Logs
```bash
# Real-time logs
pm2 logs vproptrader-sidecar
pm2 logs vproptrader-dashboard

# Last 100 lines
pm2 logs vproptrader-sidecar --lines 100
pm2 logs vproptrader-dashboard --lines 100
```

### Restart Services
```bash
# Restart both
pm2 restart ecosystem.config.js

# Restart individual services
pm2 restart vproptrader-sidecar
pm2 restart vproptrader-dashboard
```

### Stop Services
```bash
# Stop both
pm2 stop vproptrader-sidecar vproptrader-dashboard

# Stop individual
pm2 stop vproptrader-sidecar
pm2 stop vproptrader-dashboard
```

### Delete Services
```bash
pm2 delete vproptrader-sidecar vproptrader-dashboard
```

### Monitor Resources
```bash
pm2 monit
```

---

## 📁 Log Files

Logs are stored in: `/home/ubuntu/Sandeep/projects/Vproptrader/logs/`

- **Sidecar Output**: `logs/sidecar-out.log`
- **Sidecar Errors**: `logs/sidecar-error.log`
- **Dashboard Output**: `logs/dashboard-out.log`
- **Dashboard Errors**: `logs/dashboard-error.log`

---

## 🔐 Environment Configuration

### Sidecar (.env)
- Host: 0.0.0.0
- Port: 8000
- Environment: production
- Redis: localhost:6379
- Database: ./data/vproptrader.db
- Symbols: NAS100, XAUUSD, EURUSD

### Dashboard (.env.local)
- API URL: http://3.111.22.56:8000
- WebSocket URL: 3.111.22.56:8000

---

## ⚙️ System Features

### Active Components
- ✅ Thompson Sampling adaptive learning
- ✅ Multi-model ML ensemble (RF, LSTM, GBT, Autoencoder)
- ✅ Short-term memory (Redis - last 1000 trades)
- ✅ Long-term memory (SQLite + FAISS)
- ✅ Real-time WebSocket updates
- ✅ 7 hard governors (immutable safety rules)
- ✅ 3 soft governors (adaptive risk controls)
- ✅ Automated daily digest (22:00 UTC)
- ✅ Nightly model retraining (02:00 UTC)
- ✅ Hourly drift detection

### Data Sources
- ✅ FRED API (Macro data)
- ✅ TwelveData API
- ✅ Alpha Vantage API
- ✅ Polygon.io API
- ✅ ForexFactory Calendar (scraper)
- ⚠️ MT5 (Windows only - not available on Linux)

---

## 🛠️ Troubleshooting

### Service Not Starting
```bash
# Check logs
pm2 logs vproptrader-sidecar --err --lines 50

# Check if port is in use
lsof -i :8000
lsof -i :4001

# Restart with fresh logs
pm2 restart vproptrader-sidecar --update-env
```

### High Memory Usage
```bash
# Check memory
pm2 list
free -h

# Restart service
pm2 restart vproptrader-sidecar
```

### Can't Access from Public IP
- ✅ Ports 4001 and 8000 are already enabled in AWS Lightsail
- Check if services are listening on 0.0.0.0 (not 127.0.0.1)
- Verify with: `netstat -tulpn | grep -E ':(4001|8000)'`

---

## 🔄 Auto-Start on Reboot

To ensure services start automatically after server reboot:

```bash
# Save current PM2 process list
pm2 save

# Generate startup script
pm2 startup

# Follow the instructions shown (run the command it provides)
```

---

## 📝 Notes

1. **MT5 Integration**: MetaTrader5 package is Windows-only. The system gracefully handles its absence on Linux and uses alternative data sources.

2. **Development Mode**: Dashboard is running in development mode (`npm run dev`). For production, build with `npm run build` and use `npm start`.

3. **Firewall**: Ports 4001 and 8000 are already configured in AWS Lightsail networking console - no changes made.

4. **No Existing Processes Killed**: New PM2 processes were started without affecting any existing services.

---

## ✅ Verification

Test the deployment:

```bash
# Test sidecar health
curl http://3.111.22.56:8000/health

# Test dashboard
curl -I http://3.111.22.56:4001

# Check PM2 status
pm2 list | grep vproptrader
```

---

**System Status**: 🟢 OPERATIONAL  
**Both services are running and accessible via public IP!**
