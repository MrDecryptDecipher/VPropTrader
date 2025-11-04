# MT5 and Ubuntu Connection Checklist

## Overview

This checklist ensures proper setup and connection between MetaTrader 5 (MT5) running on Windows and the Vproptrader Sidecar service running on Ubuntu.

## Pre-Requirements

- [ ] Ubuntu server with Vproptrader project installed
- [ ] Windows machine with MT5 installed
- [ ] Network connectivity between Windows and Ubuntu machines
- [ ] SSH access to Ubuntu server
- [ ] WinSCP or similar file transfer tool

## Ubuntu Sidecar Setup

### Service Configuration
- [ ] Sidecar configured to listen on all interfaces (0.0.0.0:8000)
  - Check `~/Sandeep/projects/Vproptrader/sidecar/app/core/config.py`
  - Verify: `host: str = "0.0.0.0"`
- [ ] Sidecar service running
  - Command: `cd ~/Sandeep/projects/Vproptrader/sidecar && source venv/bin/activate && python -m app.main`
- [ ] Service accessible locally
  - Test: `curl http://localhost:8000/health`

### Network Configuration
- [ ] Ubuntu firewall configured to allow port 8000
  - Command: `sudo ufw allow 8000/tcp`
  - Verify: `sudo ufw status`
- [ ] Service listening on correct interface
  - Command: `netstat -tuln | grep 8000`
  - Expected output: `0.0.0.0:8000` (not `127.0.0.1:8000`)
- [ ] Ubuntu server IP address identified
  - Command: `hostname -I`
  - Note the IP address for use in Windows configuration

### Cloud Provider Configuration (If Applicable)
- [ ] Security groups configured to allow port 8000
  - AWS: EC2 Security Group with inbound rule for TCP 8000
  - Azure: Network Security Group rule for port 8000

## Windows MT5 Setup

### File Transfer
- [ ] MT5 EA files prepared on Ubuntu
  - Command: `cd ~/Sandeep/projects/Vproptrader && zip -r mt5_ea.zip mt5_ea/`
- [ ] MT5 EA files transferred to Windows
  - Use WinSCP, FileZilla, or similar tool
- [ ] MT5 EA files extracted to correct location
  - Path: `C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\`
  - Files needed:
    - [ ] `QuantSupraAI.mq5`
    - [ ] `config.mqh`
    - [ ] `Include/RestClient.mqh`
    - [ ] `Include/RiskManager.mqh`
    - [ ] `Include/TradeEngine.mqh`
    - [ ] `Include/Governors.mqh`

### EA Configuration
- [ ] `config.mqh` updated with Ubuntu server IP
  - Line: `input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";`
- [ ] Log-only mode enabled for initial testing
  - Line: `input bool LogOnlyMode = true;`
- [ ] Other parameters configured as needed
  - Trading symbols
  - Poll interval
  - Risk parameters

### MT5 Configuration
- [ ] WebRequest permissions configured
  - In MT5: Tools → Options → Expert Advisors
  - Add `http://YOUR_UBUNTU_IP:8000` to "Allow WebRequest for listed URL" list
- [ ] DLL imports allowed
  - In MT5: Tools → Options → Expert Advisors
  - Check "Allow DLL imports"

### EA Compilation
- [ ] EA compiled successfully in MetaEditor
  - Open MetaEditor (F4)
  - Open `QuantSupraAI.mq5`
  - Compile (F7)
  - Verify: "0 error(s), 0 warning(s)"

## Connection Testing

### Network Connectivity
- [ ] Windows can ping Ubuntu server
  - Command: `ping YOUR_UBUNTU_IP`
- [ ] Windows can access Sidecar health endpoint
  - Command: `curl http://YOUR_UBUNTU_IP:8000/health`
  - Expected: JSON response with system health information

### EA Initialization
- [ ] EA attached to chart successfully
  - Open chart for NAS100, XAUUSD, or EURUSD
  - Drag EA from Navigator to chart
  - Enable "Allow live trading"
- [ ] EA initializes without errors
  - Check MT5 Experts log for initialization messages
  - Expected messages:
    ```
    === Quant Ω Supra AI Expert Advisor ===
    ✓ REST Client initialized
    ✓ Risk Manager initialized
    ✓ Trade Engine initialized
    ✓ Governors initialized
    ✓ Sidecar connection successful
    EA Initialization Complete - Ready to Trade
    ```

### Signal Polling
- [ ] EA polls Sidecar at configured interval
  - Check MT5 Experts log for periodic signal requests
  - Expected: Signal requests every 1-2 seconds
- [ ] Sidecar receives requests from EA
  - Check Sidecar logs:
    ```bash
    tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
    ```
  - Expected: `GET /api/signals` entries

### Log-Only Mode Testing
- [ ] EA operates correctly in log-only mode
  - Check MT5 Experts log for:
    - Signal processing messages
    - "LOG-ONLY MODE: Would execute..." messages
    - No error messages
- [ ] Sidecar operates correctly
  - Check Sidecar logs for:
    - Signal generation (if market conditions allow)
    - No error messages
    - Normal request/response patterns

## Live Trading Setup (After Successful Log-Only Testing)

### Configuration Update
- [ ] Log-only mode disabled
  - In `config.mqh`: `input bool LogOnlyMode = false;`
- [ ] EA recompiled
  - MetaEditor: Compile (F7)
- [ ] EA reattached to chart

### AutoTrading Enable
- [ ] MT5 AutoTrading enabled
  - Click AutoTrading button in MT5 toolbar (should turn green)

### First Trade Monitoring
- [ ] First signal received
- [ ] First trade executed (if market conditions allow)
- [ ] Stop loss set correctly
- [ ] Take profit set correctly
- [ ] Execution reported to Sidecar
- [ ] PnL tracking working
- [ ] No errors in MT5 or Sidecar logs

## Troubleshooting Checklist

If connection issues occur, verify:

### Ubuntu Side
- [ ] Sidecar service running
- [ ] Service listening on 0.0.0.0:8000
- [ ] Firewall allows port 8000
- [ ] Security groups allow port 8000 (if using cloud provider)
- [ ] Correct IP address used in configuration

### Windows Side
- [ ] Correct IP address in `config.mqh`
- [ ] Sidecar URL added to MT5 WebRequest allowed list
- [ ] DLL imports allowed in MT5
- [ ] EA compiled without errors
- [ ] Network connectivity to Ubuntu server

### Network
- [ ] Windows can ping Ubuntu server
- [ ] Windows can access Sidecar health endpoint via curl
- [ ] No network firewalls blocking connection

## Monitoring and Maintenance

### Regular Checks
- [ ] Daily: Verify connection between EA and Sidecar
- [ ] Weekly: Check Sidecar logs for errors
- [ ] Monthly: Update EA and Sidecar components

### Key Log Locations
- [ ] MT5 Experts log: Toolbox → Experts tab
- [ ] Sidecar logs: `~/Sandeep/projects/Vproptrader/sidecar/logs/app.log`

### Performance Metrics
- [ ] Connection latency: <400ms
- [ ] Signal response time: <1 second
- [ ] Error rate: 0%

## Security Best Practices

- [ ] Restrict firewall access to specific IP addresses when possible
- [ ] Use VPN for secure connection over internet
- [ ] Regularly update system and software components
- [ ] Monitor logs for suspicious activity
- [ ] Backup configuration files regularly

## Conclusion

By following this checklist, you should be able to successfully set up and maintain the connection between your Windows MT5 installation and the Ubuntu Sidecar service. Always start with log-only mode for testing before enabling live trading, and regularly monitor both systems for optimal performance.