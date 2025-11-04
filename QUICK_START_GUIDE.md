# VPropTrader - Quick Start Guide

## 🎉 Current Status: READY FOR NGINX SETUP

Both services are running and healthy. You're one command away from full external access!

---

## ⚡ Quick Commands

### Enable External Access (Required)
```bash
cd /home/ubuntu/Sandeep/projects/Vproptrader
sudo bash setup-nginx.sh
```

### Check Service Status
```bash
pm2 list | grep vproptrader
```

### View Logs
```bash
# Sidecar logs
pm2 logs vproptrader-sidecar

# Dashboard logs
pm2 logs vproptrader-dashboard
```

### Restart Services
```bash
# Restart both
pm2 restart vproptrader-sidecar vproptrader-dashboard

# Restart individually
pm2 restart vproptrader-sidecar
pm2 restart vproptrader-dashboard
```

### Health Checks
```bash
# Sidecar API
curl http://localhost:8001/health | python3 -m json.tool

# Dashboard
curl -I http://localhost:3001
```

---

## 🌐 Access URLs

### Internal (from server)
- **Sidecar API**: http://localhost:8001
- **Dashboard**: http://localhost:3001

### External (after nginx setup)
- **Sidecar API**: http://3.111.22.56:8000
- **Dashboard**: http://3.111.22.56:4001

---

## 📋 Service Details

### Sidecar API (FastAPI)
- **Port**: 127.0.0.1:8001
- **Status**: ✅ ONLINE
- **Health**: Degraded (MT5 not connected - expected)
- **Uptime**: 5+ hours
- **Memory**: 699 MB

### Dashboard (Next.js)
- **Port**: 0.0.0.0:3001
- **Status**: ✅ ONLINE
- **Health**: HTTP 200 OK
- **Uptime**: 20+ minutes
- **Memory**: 54 MB

---

## 🔧 What Was Fixed

1. ✅ Database import errors (`database` → `db`)
2. ✅ Missing `base_path` in Settings
3. ✅ Port conflict (3000 → 3001)
4. ✅ Next.js SSR window errors

---

## 📚 Documentation

- **DEPLOYMENT_SUCCESS.md** - Complete deployment summary
- **VPROPTRADER_DEPLOYMENT_COMPLETE.md** - Detailed deployment guide
- **MT5_EA_COMPLETE_GUIDE.md** - MetaTrader 5 setup

---

## 🚀 Next Steps

1. **Run nginx setup** (see command above)
2. **Test external access**
3. **Configure PM2 auto-start**: `pm2 save && pm2 startup`
4. **Set up MT5 connection** (see MT5_EA_COMPLETE_GUIDE.md)

---

## 💡 Pro Tips

### Monitor Services
```bash
# Watch PM2 in real-time
pm2 monit

# Follow logs
pm2 logs --lines 50
```

### Troubleshooting
```bash
# If service stops
pm2 restart <service-name>

# If port conflict
ss -tlnp | grep <port>

# If nginx issues
sudo nginx -t
sudo systemctl status nginx
```

### Performance
```bash
# Check resource usage
pm2 info vproptrader-sidecar
pm2 info vproptrader-dashboard

# Clear logs if too large
pm2 flush
```

---

## ✅ Deployment Checklist

- [x] Services running on PM2
- [x] Health checks passing
- [x] Internal access working
- [ ] Nginx configured (run setup-nginx.sh)
- [ ] External access verified
- [ ] PM2 auto-start enabled
- [ ] MT5 connected

---

**Need Help?** Check the detailed documentation files or run:
```bash
pm2 logs <service-name> --lines 100
```

**Ready to go live?** Run:
```bash
sudo bash setup-nginx.sh
```
