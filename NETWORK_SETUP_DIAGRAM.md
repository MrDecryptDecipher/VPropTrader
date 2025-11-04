# Network Setup Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR SETUP                                │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐         ┌──────────────────────────┐
│   WINDOWS MACHINE        │         │   LINUX MACHINE          │
│   (Your Trading PC)      │         │   (Ubuntu Server/VPS)    │
│                          │         │                          │
│  ┌────────────────────┐  │         │  ┌────────────────────┐  │
│  │   MT5 Terminal     │  │         │  │  Sidecar Service   │  │
│  │                    │  │         │  │  (Python/FastAPI)  │  │
│  │  ┌──────────────┐  │  │         │  │                    │  │
│  │  │ QuantSupraAI │  │  │  HTTP   │  │  Port: 8000        │  │
│  │  │     EA       │◄─┼──┼─────────┼─►│  IP: 192.168.1.100 │  │
│  │  │              │  │  │ REST API│  │                    │  │
│  │  └──────────────┘  │  │         │  │  ┌──────────────┐  │  │
│  │                    │  │         │  │  │   Redis      │  │  │
│  │  Polls every 1-2s  │  │         │  │  │   SQLite     │  │  │
│  │  for signals       │  │         │  │  │   FAISS      │  │  │
│  └────────────────────┘  │         │  │  └──────────────┘  │  │
│                          │         │  │                    │  │
│  IP: 192.168.1.50        │         │  │  ┌──────────────┐  │  │
│  OS: Windows 10/11       │         │  │  │  Dashboard   │  │  │
│                          │         │  │  │  (Next.js)   │  │  │
└──────────────────────────┘         │  │  │  Port: 3000  │  │  │
                                     │  │  └──────────────┘  │  │
                                     │  │                    │  │
                                     │  │  OS: Ubuntu 20.04+ │  │
                                     │  └────────────────────┘  │
                                     └──────────────────────────┘

                    ▲                           ▲
                    │                           │
                    └───────────────┬───────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   Local Network     │
                         │   Router/Switch     │
                         │   192.168.1.1       │
                         └─────────────────────┘
```

---

## Communication Flow

```
┌─────────────┐                                    ┌─────────────┐
│   MT5 EA    │                                    │   Sidecar   │
│  (Windows)  │                                    │   (Linux)   │
└──────┬──────┘                                    └──────┬──────┘
       │                                                  │
       │  1. GET /api/signals?equity=1000                │
       ├─────────────────────────────────────────────────►
       │                                                  │
       │                                                  │  2. Process
       │                                                  │     - Run ML models
       │                                                  │     - Calculate Q*
       │                                                  │     - Filter signals
       │                                                  │
       │  3. Response: {signals: [...]}                  │
       ◄─────────────────────────────────────────────────┤
       │                                                  │
       │  4. Execute trade (if signal valid)             │
       │                                                  │
       │  5. POST /api/executions                        │
       ├─────────────────────────────────────────────────►
       │     {trade_id, symbol, entry, lots, ...}        │
       │                                                  │
       │  6. Response: {status: "ok"}                    │
       ◄─────────────────────────────────────────────────┤
       │                                                  │
       │                                                  │  7. Store in
       │                                                  │     - Redis (STM)
       │                                                  │     - SQLite (LTM)
       │                                                  │     - Update stats
       │                                                  │
       │  8. Repeat every 1-2 seconds                    │
       ├─────────────────────────────────────────────────►
       │                                                  │
```

---

## Network Configurations

### Option 1: Same Local Network (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│                    Home Network                         │
│                    192.168.1.0/24                       │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Windows    │         │    Linux     │            │
│  │ 192.168.1.50 │◄───────►│192.168.1.100 │            │
│  │              │  LAN    │              │            │
│  │  MT5 + EA    │         │   Sidecar    │            │
│  └──────────────┘         └──────────────┘            │
│         │                        │                     │
│         └────────┬───────────────┘                     │
│                  │                                     │
│         ┌────────▼────────┐                           │
│         │  Router/Switch  │                           │
│         │  192.168.1.1    │                           │
│         └─────────────────┘                           │
└─────────────────────────────────────────────────────────┘

Advantages:
✓ Low latency (<10ms)
✓ No internet required
✓ More secure
✓ Free

Configuration:
- SidecarURL = "http://192.168.1.100:8000"
```

### Option 2: VPS (Cloud Server)

```
┌──────────────────┐                    ┌──────────────────┐
│   Windows PC     │                    │   Linux VPS      │
│   (Home)         │                    │   (Cloud)        │
│                  │                    │                  │
│  ┌────────────┐  │                    │  ┌────────────┐  │
│  │  MT5 + EA  │  │                    │  │  Sidecar   │  │
│  └─────┬──────┘  │                    │  └─────┬──────┘  │
│        │         │                    │        │         │
└────────┼─────────┘                    └────────┼─────────┘
         │                                       │
         │  Internet                             │
         │  (HTTP/REST)                          │
         │                                       │
         └───────────────┬───────────────────────┘
                         │
                ┌────────▼────────┐
                │   Public IP     │
                │  45.67.89.123   │
                └─────────────────┘

Advantages:
✓ Access from anywhere
✓ 24/7 uptime
✓ Professional setup
✓ Scalable

Configuration:
- SidecarURL = "http://45.67.89.123:8000"

Security:
- Use HTTPS (SSL certificate)
- Firewall rules (allow only your IP)
- VPN recommended
```

### Option 3: WSL (Windows Subsystem for Linux)

```
┌─────────────────────────────────────────────────────────┐
│              Windows Machine                            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Windows Host                        │  │
│  │                                                  │  │
│  │  ┌────────────┐                                 │  │
│  │  │  MT5 + EA  │                                 │  │
│  │  └─────┬──────┘                                 │  │
│  │        │                                        │  │
│  └────────┼────────────────────────────────────────┘  │
│           │                                           │
│           │  localhost or 172.x.x.x                   │
│           │                                           │
│  ┌────────▼────────────────────────────────────────┐  │
│  │              WSL2 (Ubuntu)                      │  │
│  │                                                  │  │
│  │  ┌────────────┐                                 │  │
│  │  │  Sidecar   │                                 │  │
│  │  └────────────┘                                 │  │
│  │                                                  │  │
│  │  IP: 172.x.x.x (dynamic)                        │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

Advantages:
✓ Everything on one machine
✓ Very low latency
✓ Easy setup
✓ Good for testing

Configuration:
- Get WSL IP: wsl hostname -I
- SidecarURL = "http://172.x.x.x:8000"

Note: WSL IP can change on restart
```

---

## Port Configuration

### Sidecar Service (Linux)

```
Port 8000 (HTTP)
├── /health              - Health check
├── /api/signals         - Trading signals (polled by EA)
├── /api/executions      - Execution reporting
├── /api/analytics/*     - Analytics endpoints
└── /ws/live            - WebSocket streaming
```

**Firewall rule:**
```bash
sudo ufw allow 8000/tcp
```

### Dashboard (Optional)

```
Port 3000 (HTTP)
├── /                    - Overview page
├── /compliance          - Compliance panel
├── /alphas              - Alpha heatmap
├── /risk                - Risk monitor
└── ...                  - Other pages
```

**Firewall rule:**
```bash
sudo ufw allow 3000/tcp
```

### Redis (Internal)

```
Port 6379 (Internal only)
- Should NOT be exposed to network
- Only accessible from localhost
```

---

## Security Considerations

### Local Network Setup

```
✓ Firewall on Linux
  - Allow port 8000 from local network only
  - Block external access

✓ No password needed (trusted network)

✓ Monitor access logs
```

### VPS/Cloud Setup

```
✓ HTTPS/SSL certificate
  - Use Let's Encrypt (free)
  - Encrypt all traffic

✓ Firewall rules
  - Allow port 8000 only from your IP
  - Use fail2ban for brute force protection

✓ VPN recommended
  - WireGuard or OpenVPN
  - Extra layer of security

✓ Authentication
  - API key in headers
  - JWT tokens
```

---

## Testing Connectivity

### From Windows to Linux

```cmd
REM 1. Test network connectivity
ping 192.168.1.100

REM 2. Test port is open
telnet 192.168.1.100 8000

REM 3. Test HTTP endpoint
curl http://192.168.1.100:8000/health

REM 4. Test signals endpoint
curl http://192.168.1.100:8000/api/signals?equity=1000
```

### From Linux

```bash
# 1. Check Sidecar is running
curl http://localhost:8000/health

# 2. Check what IP it's listening on
netstat -tuln | grep 8000
# Should show: 0.0.0.0:8000 (all interfaces)
# NOT: 127.0.0.1:8000 (localhost only)

# 3. Check firewall
sudo ufw status

# 4. Test from external
curl http://$(hostname -I | awk '{print $1}'):8000/health
```

---

## Latency Expectations

### Local Network
- **Ping:** <1ms
- **API call:** 5-20ms
- **Total round-trip:** <50ms
- **Status:** ✓ Excellent

### VPS (Same Region)
- **Ping:** 10-50ms
- **API call:** 20-100ms
- **Total round-trip:** 50-200ms
- **Status:** ✓ Good

### VPS (Different Region)
- **Ping:** 50-200ms
- **API call:** 100-300ms
- **Total round-trip:** 200-500ms
- **Status:** ⚠ Acceptable (but not ideal)

### VPS (Different Continent)
- **Ping:** 200-500ms
- **API call:** 300-800ms
- **Total round-trip:** 500-1000ms
- **Status:** ✗ Too slow (>400ms threshold)

**Recommendation:** Use local network or VPS in same region as your location.

---

## Quick Setup Summary

1. **Get Linux IP:** `hostname -I` → `192.168.1.100`
2. **Start Sidecar:** `python -m app.main`
3. **Open firewall:** `sudo ufw allow 8000/tcp`
4. **Test from Windows:** `curl http://192.168.1.100:8000/health`
5. **Update EA config:** `SidecarURL = "http://192.168.1.100:8000"`
6. **Compile and attach EA**
7. **Verify connection in MT5 Experts log**
8. **Monitor operation**

---

*Network Setup Guide*
*Version: 1.0.0*
*Last Updated: 2025-10-25*
