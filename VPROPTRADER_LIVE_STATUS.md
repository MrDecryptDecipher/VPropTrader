# VPropTrader System - LIVE on PM2 🚀

## Deployment Complete
**Date**: October 28, 2025  
**Public IP**: 3.111.22.56  
**Project Path**: /home/ubuntu/Sandeep/projects/Vproptrader

---

## ✅ Services Running on PM2

### 1. Sidecar API (Backend)
- **Process Name**: `vproptrader-sidecar`
- **PM2 ID**: 13
- **Status**: ✅ ONLINE
- **Port**: 8000
- **Binding**: 0.0.0.0:8000
- **Memory**: ~133 MB
- **Uptime**: Running
- **Command**: `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Working Directory**: `/home/ubuntu/Sandeep/projects/Vproptrader/sidecar`
- **Logs**: 
  - Output: `/home/ubuntu/Sandeep/projects/Vproptrader/logs/sidecar-out.log`
  - Error: `/home/ubuntu/Sandeep/projects/Vproptrader/logs/sidecar-error.log`

### 2. Dashboard (Frontend)
- **Process Name**: `vproptrader-dashboard`
- **PM2 ID**: 14
- **Status**: ✅ ONLINE
- **Port**: 4001
- **Binding**: :::4001 (IPv6 all interfaces)
- **Memory**: ~53 MB
- **Uptime**: Running
- **Command**: `npm run dev -- --port 4001`
- **Working Directory**: `/home/ubuntu/Sandeep/projects/Vproptrader/dashboard`
- **Logs**:
  - Output: `/home/ubuntu/Sandeep/projects/Vproptrader/logs/dashboard-out.log`
  - Error: `/home/ubuntu/Sandeep/projects/Vproptrader/logs/dashboard-error.log`

---

## 🌐 Access URLs

### Public Access (via your IP)
- **Dashboard**: http://3.111.22.56:4001
- **API Backend**: http://3.111.22.56:8000
- **API Health Check**: http://3.111.22.56:8000/health
- **API Documentation**: http://3.111.22.56:8000/docs
- **WebSocket**: ws://3.111.22.56:8000/ws

### Local Access (from server)
- **Dashboard**: http://localhost:4001
- **API Backend**: http://localhost:8000

---

## 📋 PM2 Management Commands

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
pm2 logs  # All processes

# Last 100 lines
pm2 logs vproptrader-sidecar --lines 100
pm2 logs vproptrader-dashboard --lines 100
```

### Restart Services
```bash
pm2 restart vproptrader-sidecar
pm2 restart vproptrader-dashboard
pm2 restart all  # Restart all PM2 processes
```

### Stop Services
```bash
pm2 stop vproptrader-sidecar
pm2 stop vproptrader-dashboard
```

### Start Services (if stopped)
```bash
pm2 start vproptrader-sidecar
pm2 start vproptrader-dashboard
# Or start from config
pm2 start ecosystem.config.js
```

### Delete from PM2
```bash
pm2 delete vproptrader-sidecar
pm2 delete vproptrader-dashboard
```

### Monitor Resources
```bash
pm2 monit
```

### Save PM2 Configuration (auto-start on reboot)
```bash
pm2 save
pm2 startup  # Follow the instructions
```

---

## 🔧 Configuration Files

### PM2 Ecosystem Config
**File**: `/home/ubuntu/Sandeep/projects/Vproptrader/ecosystem.config.js`

### Environment Variables

#### Sidecar (.env)
**File**: `/home/ubuntu/Sandeep/projects/Vproptrader/sidecar/.env`
- PORT=8000
- HOST=0.0.0.0
- ENVIRONMENT=production
- API Keys configured for TwelveData, AlphaVantage, Polygon, FRED

#### Dashboard (.env.local)
**File**: `/home/ubuntu/Sandeep/projects/Vproptrader/dashboard/.env.local`
- NEXT_PUBLIC_API_URL=http://3.111.22.56:8000
- NEXT_PUBLIC_WS_URL=3.111.22.56:8000

---

## 🔍 Health Checks

### API Health
```bash
curl http://localhost:8000/health
# or
curl http://3.111.22.56:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T19:33:48.745Z",
  "uptime": 118747
}
```

### Dashboard Check
```bash
curl -I http://localhost:4001
# or
curl -I http://3.111.22.56:4001
```

Expected: HTTP 200 OK

---

## 🛡️ Firewall & Network

### Ports Opened (AWS Lightsail)
- ✅ Port 4001 (Dashboard)
- ✅ Port 8000 (API)

**Note**: Ports are already configured in AWS Lightsail networking console. No local firewall changes were made.

### Verify Ports are Listening
```bash
netstat -tlnp | grep -E ":(4001|8000)"
# or
ss -tlnp | grep -E ":(4001|8000)"
```

---

## 📊 System Features

### Sidecar API Features
- ✅ FastAPI REST endpoints
- ✅ WebSocket support for real-time updates
- ✅ ML model inference (Random Forest, LSTM, GBT)
- ✅ Thompson Sampling adaptive learning
- ✅ Redis short-term memory
- ✅ SQLite + FAISS long-term memory
- ✅ Multi-source data providers (TwelveData, AlphaVantage, Polygon, FRED)
- ✅ Risk management & governors
- ✅ Performance analytics
- ✅ Compliance monitoring

### Dashboard Features
- ✅ Real-time equity & PnL tracking
- ✅ Trade history & analytics
- ✅ Performance metrics & charts
- ✅ Risk management dashboard
- ✅ Alpha strategy heatmap
- ✅ Compliance monitoring
- ✅ WebSocket live updates
- ✅ Market timer & session info

---

## 🐛 Troubleshooting

### If Sidecar Won't Start
1. Check logs: `pm2 logs vproptrader-sidecar --lines 50`
2. Verify Python dependencies: `cd sidecar && pip3 list | grep fastapi`
3. Check port availability: `lsof -i :8000`
4. Restart: `pm2 restart vproptrader-sidecar`

### If Dashboard Won't Start
1. Check logs: `pm2 logs vproptrader-dashboard --lines 50`
2. Verify node_modules: `cd dashboard && ls node_modules | wc -l`
3. Check port availability: `lsof -i :4001`
4. Reinstall if needed: `cd dashboard && npm install`
5. Restart: `pm2 restart vproptrader-dashboard`

### If Can't Access via Public IP
1. Verify services are running: `pm2 list`
2. Check ports are listening: `netstat -tlnp | grep -E ":(4001|8000)"`
3. Verify AWS Lightsail firewall rules (ports 4001, 8000 open)
4. Test locally first: `curl http://localhost:8000/health`
5. Check if services are binding to 0.0.0.0 (not 127.0.0.1)

### Common Issues
- **MetaTrader5 Import Error**: Fixed - MT5 imports are now optional on Linux
- **Port Already in Use**: Stop conflicting process or change port in ecosystem.config.js
- **Permission Denied**: Ensure user has access to project directory
- **Memory Issues**: Monitor with `pm2 monit` and adjust if needed

---

## 📝 Notes

### Linux Compatibility
- MetaTrader5 package is Windows-only, so MT5 imports are handled gracefully with try/except
- The system will work without MT5 for data collection and use alternative data sources
- For full MT5 integration, you'll need to run the MT5 EA on a Windows machine

### Auto-Start on Reboot
To make PM2 processes start automatically after server reboot:
```bash
pm2 save
pm2 startup
# Follow the command it gives you (run with sudo)
```

### Performance
- Sidecar typically uses 100-150 MB RAM
- Dashboard typically uses 50-60 MB RAM
- Both services have auto-restart enabled
- Max 10 restarts with 4-second delay between attempts

---

## ✅ Deployment Checklist

- [x] PM2 installed and configured
- [x] Sidecar service running on port 8000
- [x] Dashboard service running on port 4001
- [x] Both services binding to 0.0.0.0 (all interfaces)
- [x] Environment variables configured
- [x] Logs directory created
- [x] AWS Lightsail ports opened (4001, 8000)
- [x] MetaTrader5 import issue resolved
- [x] Health checks passing
- [x] Services accessible locally

---

## 🎯 Next Steps

1. **Test Public Access**: Open http://3.111.22.56:4001 in your browser
2. **Verify API**: Check http://3.111.22.56:8000/docs for API documentation
3. **Monitor Logs**: Use `pm2 logs` to watch for any issues
4. **Set Auto-Start**: Run `pm2 save && pm2 startup` for persistence
5. **Configure MT5 EA**: Set up the MT5 Expert Advisor to connect to your sidecar API

---

**System Status**: 🟢 OPERATIONAL  
**Last Updated**: October 28, 2025
