# Deployment Checklist - Quant Ω Supra AI

## Pre-Deployment Checklist

### Environment Setup
- [ ] Python 3.11+ installed
- [ ] Redis server installed and running
- [ ] MT5 terminal installed (Windows)
- [ ] Node.js 18+ installed
- [ ] Git repository cloned

### Configuration Files
- [ ] `Vproptrader/sidecar/.env` created with:
  - [ ] MT5_LOGIN
  - [ ] MT5_PASSWORD
  - [ ] MT5_SERVER
  - [ ] FRED_API_KEY
  - [ ] REDIS_HOST
  - [ ] DATABASE_PATH
- [ ] `Vproptrader/mt5_ea/config.mqh` updated with:
  - [ ] SidecarURL (correct IP:port)
  - [ ] TradingSymbols
  - [ ] LogOnlyMode setting
- [ ] `Vproptrader/dashboard/.env.local` created with:
  - [ ] NEXT_PUBLIC_API_URL

### Dependencies Installation
- [ ] Python: `cd sidecar && pip install -r requirements.txt`
- [ ] Dashboard: `cd dashboard && npm install`
- [ ] MT5 EA: Compiled in MetaEditor

---

## Testing Phase

### Unit Testing
- [ ] Test ML model inference speed (<1ms)
- [ ] Test Redis connection
- [ ] Test SQLite database operations
- [ ] Test FAISS vector store
- [ ] Test MT5 Python API connection
- [ ] Test FRED API connection
- [ ] Test REST API endpoints
- [ ] Test WebSocket connection

### Integration Testing
- [ ] Start Sidecar Service: `python -m app.main`
- [ ] Verify health endpoint: `curl http://localhost:8000/health`
- [ ] Start Dashboard: `npm run dev`
- [ ] Verify dashboard loads at http://localhost:3000
- [ ] Attach EA to MT5 chart (log-only mode)
- [ ] Verify EA connects to Sidecar
- [ ] Verify signals are generated
- [ ] Verify dashboard receives data

### Compliance Testing
- [ ] Test daily loss limit (-$45)
- [ ] Test total loss limit ($900 equity)
- [ ] Test profit target ($100)
- [ ] Test time-based close (21:45 UTC)
- [ ] Test Friday close (20:00 UTC)
- [ ] Test news embargo
- [ ] Test daily profit cap (1.8%)
- [ ] Verify all governors trigger correctly

### Paper Trading (1 Week Minimum)
- [ ] Day 1: Monitor all systems
- [ ] Day 2: Verify ML predictions
- [ ] Day 3: Check alpha performance
- [ ] Day 4: Validate risk management
- [ ] Day 5: Test retraining cycle
- [ ] Day 6: Review compliance logs
- [ ] Day 7: Analyze performance metrics

### Performance Validation
- [ ] Inference speed < 1ms ✓
- [ ] API latency < 100ms ✓
- [ ] Dashboard load time < 2s ✓
- [ ] Signal generation < 1s ✓
- [ ] Memory usage stable ✓
- [ ] No memory leaks ✓

---

## Production Deployment

### VPS Setup (Ubuntu 20.04+)
- [ ] Create VPS instance
- [ ] Install Python 3.11+
- [ ] Install Redis: `sudo apt install redis-server`
- [ ] Install system dependencies
- [ ] Configure firewall (port 8000)
- [ ] Set up SSH keys
- [ ] Configure automatic updates

### Sidecar Service Deployment
- [ ] Clone repository to VPS
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Copy production `.env` file
- [ ] Create systemd service file:
  ```bash
  sudo nano /etc/systemd/system/sidecar.service
  ```
- [ ] Enable service: `sudo systemctl enable sidecar`
- [ ] Start service: `sudo systemctl start sidecar`
- [ ] Verify status: `sudo systemctl status sidecar`
- [ ] Check logs: `sudo journalctl -u sidecar -f`

### Nightly Retrain Cron Job
- [ ] Edit crontab: `crontab -e`
- [ ] Add: `0 2 * * * /path/to/venv/bin/python -m app.ml.retraining_engine`
- [ ] Verify cron is running

### Dashboard Deployment (Vercel/Netlify)
- [ ] Build production bundle: `npm run build`
- [ ] Deploy to Vercel: `vercel deploy --prod`
- [ ] Or deploy to Netlify: `netlify deploy --prod`
- [ ] Configure environment variables
- [ ] Test production URL
- [ ] Verify WebSocket connection

### MT5 EA Deployment (Windows)
- [ ] Compile EA in MetaEditor
- [ ] Copy to MT5 Experts folder
- [ ] Update `config.mqh` with production Sidecar URL
- [ ] Attach to chart for each symbol:
  - [ ] NAS100
  - [ ] XAUUSD
  - [ ] EURUSD
- [ ] Enable AutoTrading
- [ ] Verify connection to Sidecar
- [ ] Start in log-only mode

### Database Backups
- [ ] Set up daily SQLite backups:
  ```bash
  0 3 * * * cp /path/to/trades.db /path/to/backups/trades_$(date +\%Y\%m\%d).db
  ```
- [ ] Set up FAISS index backups
- [ ] Test restore procedure

### Monitoring & Alerting
- [ ] Set up health check monitoring
- [ ] Configure email alerts for:
  - [ ] Service downtime
  - [ ] Hard governor triggers
  - [ ] High latency
  - [ ] API errors
- [ ] Set up log aggregation
- [ ] Configure dashboard alerts

---

## Go-Live Procedure

### Pre-Live Checks (Day Before)
- [ ] All systems running smoothly
- [ ] No errors in logs
- [ ] Paper trading results reviewed
- [ ] Compliance verified (zero violations)
- [ ] Performance metrics acceptable
- [ ] Team briefed on go-live plan

### Go-Live Day

**Morning (Before Market Open)**
- [ ] Verify all services running
- [ ] Check VPS resources (CPU, RAM, disk)
- [ ] Verify MT5 connection
- [ ] Check Sidecar health endpoint
- [ ] Verify dashboard loads
- [ ] Review overnight logs

**Log-Only Mode (First Session)**
- [ ] Enable EA in log-only mode
- [ ] Monitor for 1 full trading session
- [ ] Review all generated signals
- [ ] Verify compliance checks
- [ ] Check execution quality filters
- [ ] Review dashboard data

**Live Trading (If Log-Only Successful)**
- [ ] Disable log-only mode in `config.mqh`
- [ ] Recompile and reload EA
- [ ] Start with minimum position sizes
- [ ] Monitor first trade closely
- [ ] Verify execution reporting
- [ ] Check PnL tracking
- [ ] Monitor compliance panel

**First Hour Monitoring**
- [ ] Watch for any errors
- [ ] Verify signals are executed
- [ ] Check execution quality
- [ ] Monitor latency
- [ ] Verify stop loss/take profit placement
- [ ] Check dashboard updates

**First Day Monitoring**
- [ ] Monitor all trading sessions
- [ ] Review each trade execution
- [ ] Verify compliance (zero violations)
- [ ] Check performance metrics
- [ ] Review logs for any warnings
- [ ] Verify retraining scheduled

**End of Day Review**
- [ ] Review daily PnL
- [ ] Check compliance status
- [ ] Review all trades
- [ ] Analyze alpha performance
- [ ] Check for any issues
- [ ] Plan for next day

---

## Post-Deployment

### Daily Monitoring
- [ ] Check service health
- [ ] Review overnight logs
- [ ] Verify compliance status
- [ ] Monitor performance metrics
- [ ] Check for any alerts

### Weekly Review
- [ ] Analyze weekly performance
- [ ] Review alpha weights
- [ ] Check model retraining logs
- [ ] Verify drift detection
- [ ] Review execution quality
- [ ] Update documentation

### Monthly Maintenance
- [ ] Review system performance
- [ ] Optimize configurations
- [ ] Update dependencies
- [ ] Clean old logs
- [ ] Backup databases
- [ ] Review and update documentation

---

## Emergency Procedures

### Service Downtime
1. Check service status: `sudo systemctl status sidecar`
2. Review logs: `sudo journalctl -u sidecar -n 100`
3. Restart service: `sudo systemctl restart sidecar`
4. If persistent, check:
   - VPS resources
   - Network connectivity
   - Database connections
   - Redis status

### EA Issues
1. Check MT5 Experts log
2. Verify Sidecar connection
3. Check network connectivity
4. Restart EA
5. If persistent, use kill switch

### Hard Governor Trigger
1. **DO NOT OVERRIDE**
2. Review logs to understand cause
3. Close all positions (automatic)
4. Analyze what went wrong
5. Fix issue before re-enabling
6. Document incident

### Kill Switch Activation
1. Click kill switch in dashboard OR
2. Disable AutoTrading in MT5 OR
3. Stop Sidecar service
4. Verify all positions closed
5. Review logs
6. Identify and fix issue

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

## Rollback Plan

If critical issues arise:

1. **Immediate Actions**
   - Activate kill switch
   - Close all positions
   - Stop Sidecar service
   - Disable EA

2. **Investigation**
   - Review all logs
   - Identify root cause
   - Document issue

3. **Fix or Rollback**
   - Fix issue if minor
   - Rollback to previous version if major
   - Test fix in paper trading

4. **Re-deployment**
   - Follow deployment checklist again
   - Extra monitoring for first week

---

## Contact Information

**System Administrator**: [Your Name]
**Email**: [Your Email]
**Phone**: [Your Phone]

**VPS Provider**: [Provider Name]
**Support**: [Support Contact]

**VProp Account**: [Account Number]
**Support**: [VProp Support]

---

## Notes

- Always test in log-only mode first
- Never override hard governors
- Monitor closely during first week
- Document all issues and resolutions
- Keep backups of all configurations
- Review logs daily

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Status**: _______________

---

*Last Updated: 2025-10-25*
*Version: 1.0.0*
