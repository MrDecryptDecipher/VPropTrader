# Correct MT5 and Ubuntu Server Architecture for Vproptrader

## Overview

This document explains the correct architecture and setup process for connecting MetaTrader 5 (MT5) running on a Windows machine with the Vproptrader Sidecar service running on an Ubuntu server. Based on the code analysis, the intended architecture is a distributed system where:

1. **Windows Machine**: Runs MT5 Terminal with the Expert Advisor (EA)
2. **Ubuntu Server**: Runs the Sidecar service that provides AI-driven trading signals

## Intended Architecture

```
┌─────────────────────────┐
│   Windows Machine       │
│   ┌─────────────────┐   │
│   │   MT5 Terminal  │   │
│   │   + EA          │   │
│   └────────┬────────┘   │
└────────────┼────────────┘
             │ HTTP/REST
             │ (Port 8000)
             ▼
┌─────────────────────────┐
│   Linux Machine         │
│   (Ubuntu/VPS)          │
│   ┌─────────────────┐   │
│   │ Sidecar Service │   │
│   │ + Dashboard     │   │
│   └─────────────────┘   │
└─────────────────────────┘
```

## How It Works

### 1. Ubuntu Sidecar Service
The Sidecar service on Ubuntu is the core of the Vproptrader system. It:
- Provides AI-driven trading signals via REST API endpoints
- Manages risk and portfolio through advanced algorithms
- Communicates with external data sources (FRED, economic calendars, etc.)
- Listens on port 8000 for incoming requests from the MT5 EA

### 2. Windows MT5 EA
The Expert Advisor running on Windows MT5:
- Periodically polls the Sidecar service for trading signals
- Executes trades based on received signals (in live mode)
- Reports trade executions back to the Sidecar
- Operates in either log-only mode (for testing) or live trading mode

### 3. Communication Protocol
The communication between Windows MT5 and Ubuntu Sidecar uses HTTP/REST:
- MT5 EA makes GET requests to `/api/signals` endpoint
- MT5 EA makes POST requests to `/api/executions` endpoint
- Health checks are performed at `/health` endpoint

## Correct Setup Process

### Phase 1: Ubuntu Server Setup

1. **Start Sidecar Service**
   ```bash
   cd ~/Sandeep/projects/Vproptrader/sidecar
   source venv/bin/activate
   python -m app.main
   ```

2. **Verify Service is Running**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Configure Network Access**
   ```bash
   # Ensure service listens on all interfaces
   # Check sidecar/app/core/config.py has: host: str = "0.0.0.0"
   
   # Configure firewall
   sudo ufw allow 8000/tcp
   ```

4. **Get Server IP Address**
   ```bash
   hostname -I
   # Note: Should be 3.111.22.56 according to your setup
   ```

### Phase 2: Windows MT5 Setup

1. **Transfer EA Files**
   From Ubuntu:
   ```bash
   cd ~/Sandeep/projects/Vproptrader
   zip -r mt5_ea.zip mt5_ea/
   ```
   
   Transfer `mt5_ea.zip` to Windows and extract to:
   ```
   C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
   ```

2. **Configure EA**
   Edit `config.mqh` with the correct Ubuntu server IP:
   ```cpp
   input string SidecarURL = "http://3.111.22.56:8000";  // Your Ubuntu IP
   input bool LogOnlyMode = true;  // Start with true for testing
   ```

3. **Configure MT5 WebRequest Permissions**
   In MT5:
   - Go to Tools → Options → Expert Advisors
   - Add `http://3.111.22.56:8000` to "Allow WebRequest for listed URL" list
   - Check "Allow DLL imports"

4. **Compile EA**
   - Open MetaEditor (F4)
   - Open `QuantSupraAI.mq5`
   - Compile (F7)
   - Verify "0 error(s), 0 warning(s)"

### Phase 3: Connection Testing

1. **Test from Windows**
   ```cmd
   curl http://3.111.22.56:8000/health
   ```

2. **Attach EA to Chart**
   - Open chart for NAS100, XAUUSD, or EURUSD
   - Drag EA from Navigator to chart
   - Enable "Allow live trading"

3. **Verify Connection**
   Check MT5 Experts log for:
   ```
   === Quant Ω Supra AI Expert Advisor ===
   Sidecar URL: http://3.111.22.56:8000
   ✓ REST Client initialized
   ✓ Sidecar connection successful
   ```

## Key Implementation Details

### REST Client Implementation
The EA uses a custom REST client (`RestClient.mqh`) that:
- Handles HTTP requests with retry logic
- Manages JSON communication with the Sidecar
- Provides error handling and logging

### Configuration Parameters
Key configurable parameters in `config.mqh`:
- `SidecarURL`: The Ubuntu server address
- `PollInterval`: How frequently to poll for signals (1500ms default)
- `LogOnlyMode`: Whether to execute trades or just log decisions
- `TradingSymbols`: Which symbols to trade

### Signal Processing Flow
1. EA polls Sidecar at configured interval
2. Sidecar returns JSON with trading signals
3. EA processes signals and either logs or executes trades
4. Trade executions are reported back to Sidecar

## Common Issues and Solutions

### 1. WebRequest Error 4060
**Issue**: "Function not allowed" error
**Solution**: 
- Add Sidecar URL to MT5 WebRequest allowed list
- Enable "Allow DLL imports" in MT5 settings

### 2. Connection Timeout
**Issue**: EA cannot connect to Sidecar
**Solution**:
- Verify Ubuntu firewall allows port 8000
- Check Sidecar is listening on 0.0.0.0:8000, not 127.0.0.1:8000
- Verify network connectivity between Windows and Ubuntu

### 3. No Trading Signals
**Issue**: EA connects but receives no signals
**Solution**:
- Check trading hours (London 07:00-10:00 UTC or NY 13:30-16:00 UTC)
- Verify market is open
- Test manually: `curl http://3.111.22.56:8000/api/signals?equity=1000`

## Security Considerations

1. **Firewall Configuration**: Only allow necessary ports (8000 for Sidecar)
2. **Network Security**: Use VPN for added security if connecting over internet
3. **Authentication**: Consider implementing authentication for production use
4. **Data Encryption**: For sensitive data, consider HTTPS instead of HTTP

## Monitoring and Maintenance

### Logs to Monitor
1. **MT5 Experts Log**: For EA operation and errors
2. **Sidecar Logs**: For signal generation and system health
   ```bash
   tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
   ```

### Performance Metrics
1. **Connection Latency**: Should be <400ms
2. **Signal Response Time**: Should be <1 second
3. **Error Rate**: Should be 0%

## Conclusion

The Vproptrader system is designed as a distributed architecture where the computational intelligence resides on the Ubuntu server (Sidecar service) while the execution engine runs on Windows MT5. This separation provides several advantages:

1. **Scalability**: Complex AI algorithms run on a powerful server
2. **Reliability**: Server can maintain persistent connections to data sources
3. **Security**: Sensitive credentials are stored on the server
4. **Maintainability**: Updates to trading logic only require server-side changes

By following the correct setup process outlined in this document, you should be able to successfully connect your Windows MT5 installation with the Ubuntu Sidecar service and begin using the Vproptrader system.