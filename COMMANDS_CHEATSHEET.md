# Commands Cheatsheet

## Your Configuration
- **Ubuntu IP:** `3.111.22.56`
- **Sidecar URL:** `http://3.111.22.56:8000`
- **Dashboard URL:** `http://3.111.22.56:3000`

---

## Ubuntu Commands

### Start Sidecar
```bash
cd ~/Sandeep/projects/Vproptrader/sidecar
source venv/bin/activate
python -m app.main
```

### Check Health
```bash
curl http://localhost:8000/health
curl http://3.111.22.56:8000/health
```

### View Logs
```bash
# Real-time logs
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log

# Last 100 lines
tail -n 100 ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log

# Trade logs
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/trades_$(date +%Y-%m-%d).jsonl
```

### Firewall
```bash
# Open port 8000
sudo ufw allow 8000/tcp

# Open port 3000 (dashboard)
sudo ufw allow 3000/tcp

# Check status
sudo ufw status

# Check what's listening
netstat -tuln | grep 8000
```

### Monitor System
```bash
cd ~/Sandeep/projects/Vproptrader
bash scripts/monitor.sh
```

### Run Tests
```bash
cd ~/Sandeep/projects/Vproptrader
bash scripts/run_tests.sh
```

### Start Dashboard
```bash
cd ~/Sandeep/projects/Vproptrader/dashboard
npm run dev
```

---

## Windows Commands

### Test Connection
```cmd
REM Test health endpoint
curl http://3.111.22.56:8000/health

REM Test signals endpoint
curl http://3.111.22.56:8000/api/signals?equity=1000

REM Ping server
ping 3.111.22.56

REM Check if port is open
telnet 3.111.22.56 8000
```

### MT5 Locations
```
Data Folder:
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\

Experts Folder:
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\

Logs:
Check MT5 → Toolbox (Ctrl+T) → Experts tab
```

---

## API Endpoints

### Health Check
```bash
curl http://3.111.22.56:8000/health
```

### Get Signals
```bash
curl http://3.111.22.56:8000/api/signals?equity=1000
```

### Analytics Overview
```bash
curl http://3.111.22.56:8000/api/analytics/overview
```

### Compliance Status
```bash
curl http://3.111.22.56:8000/api/analytics/compliance
```

### Alpha Performance
```bash
curl http://3.111.22.56:8000/api/analytics/alphas
```

### Risk Metrics
```bash
curl http://3.111.22.56:8000/api/analytics/risk
```

---

## Troubleshooting Commands

### Check if Sidecar is Running
```bash
ps aux | grep python | grep app.main
```

### Check Redis
```bash
redis-cli ping
# Should return: PONG
```

### Check Ports
```bash
# What's listening on port 8000
sudo netstat -tulpn | grep 8000

# Check if port is accessible
nc -zv 3.111.22.56 8000
```

### Check Logs for Errors
```bash
# Sidecar errors
grep -i error ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log | tail -20

# System logs
sudo journalctl -xe | tail -50
```

### Restart Services
```bash
# If running as systemd service
sudo systemctl restart vprop-sidecar
sudo systemctl status vprop-sidecar

# Redis
sudo systemctl restart redis-server
sudo systemctl status redis-server
```

---

## Quick Diagnostics

### Full System Check
```bash
# 1. Check Sidecar
curl http://localhost:8000/health

# 2. Check from public IP
curl http://3.111.22.56:8000/health

# 3. Check firewall
sudo ufw status | grep 8000

# 4. Check what's listening
netstat -tuln | grep 8000

# 5. Check Redis
redis-cli ping

# 6. Check logs
tail -20 ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```

### From Windows
```cmd
REM 1. Ping server
ping 3.111.22.56

REM 2. Test health
curl http://3.111.22.56:8000/health

REM 3. Test signals
curl http://3.111.22.56:8000/api/signals?equity=1000
```

---

## File Locations

### Ubuntu
```
Project Root:
~/Sandeep/projects/Vproptrader/

Sidecar:
~/Sandeep/projects/Vproptrader/sidecar/

Logs:
~/Sandeep/projects/Vproptrader/sidecar/logs/

Config:
~/Sandeep/projects/Vproptrader/sidecar/.env

Dashboard:
~/Sandeep/projects/Vproptrader/dashboard/

Scripts:
~/Sandeep/projects/Vproptrader/scripts/

Tests:
~/Sandeep/projects/Vproptrader/tests/
```

### Windows
```
MT5 Data:
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\

EA Files:
...\MQL5\Experts\QuantSupraAI.mq5
...\MQL5\Experts\config.mqh
...\MQL5\Experts\Include\*.mqh
```

---

## Emergency Commands

### Kill Switch
```bash
# Stop Sidecar
pkill -f "python -m app.main"

# Or if running as service
sudo systemctl stop vprop-sidecar
```

### Close All Positions (MT5)
```
In MT5:
1. Disable AutoTrading (click button)
2. Right-click on position → Close
3. Or use EA kill switch in dashboard
```

### Check System Resources
```bash
# CPU and memory
top

# Disk space
df -h

# Network
ifconfig
netstat -tuln
```

---

## Useful Aliases (Optional)

Add to `~/.bashrc`:

```bash
# Vproptrader aliases
alias vpstart='cd ~/Sandeep/projects/Vproptrader/sidecar && source venv/bin/activate && python -m app.main'
alias vplogs='tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log'
alias vphealth='curl http://localhost:8000/health | python3 -m json.tool'
alias vpmonitor='cd ~/Sandeep/projects/Vproptrader && bash scripts/monitor.sh'
alias vptest='cd ~/Sandeep/projects/Vproptrader && bash scripts/run_tests.sh'
```

Then reload:
```bash
source ~/.bashrc
```

Now you can use:
```bash
vpstart    # Start Sidecar
vplogs     # View logs
vphealth   # Check health
vpmonitor  # Monitor system
vptest     # Run tests
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              QUICK REFERENCE                            │
├─────────────────────────────────────────────────────────┤
│ Ubuntu IP:        3.111.22.56                          │
│ Sidecar:          http://3.111.22.56:8000              │
│ Dashboard:        http://3.111.22.56:3000              │
│                                                         │
│ Start Sidecar:    cd sidecar && source venv/bin/activate│
│                   python -m app.main                    │
│                                                         │
│ Check Health:     curl http://localhost:8000/health    │
│                                                         │
│ View Logs:        tail -f sidecar/logs/app.log         │
│                                                         │
│ Monitor:          bash scripts/monitor.sh              │
│                                                         │
│ Firewall:         sudo ufw allow 8000/tcp              │
│                                                         │
│ From Windows:     curl http://3.111.22.56:8000/health  │
└─────────────────────────────────────────────────────────┘
```

---

*Commands Cheatsheet*
*Ubuntu IP: 3.111.22.56*
*Last Updated: 2025-10-25*
