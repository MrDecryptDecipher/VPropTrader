# Resolution Steps for Vproptrader MT5 Connection Issues

## Overview

This document provides a step-by-step guide to resolve the issues encountered when setting up and running the Vproptrader project, specifically focusing on transferring and executing the MT5 Expert Advisor (EA) from an Ubuntu server to a Windows host machine running MetaTrader 5 (MT5).

## Prerequisites

1. Ubuntu server with Vproptrader project installed
2. Windows machine with MT5 installed
3. SSH access to Ubuntu server
4. Network connectivity between Ubuntu and Windows machines

## Step 1: Verify Ubuntu Sidecar Service

### 1.1 Check if Sidecar is running
```bash
cd ~/Sandeep/projects/Vproptrader/sidecar
curl http://localhost:8000/health
```

If the service is not running, start it:
```bash
source venv/bin/activate
python -m app.main
```

### 1.2 Verify network binding
```bash
netstat -tuln | grep 8000
```
Should show: `0.0.0.0:8000` (not `127.0.0.1:8000`)

If it shows `127.0.0.1:8000`, check the configuration in [sidecar/app/core/config.py](file:///home/ubuntu/Sandeep/projects/Vproptrader/sidecar/app/core/config.py):
```python
host: str = "0.0.0.0"
```

### 1.3 Configure firewall
```bash
sudo ufw allow 8000/tcp
sudo ufw status
```

## Step 2: Get Ubuntu Server IP Address

```bash
hostname -I
```
Note down the IP address for use in the EA configuration.

## Step 3: Prepare EA Files for Transfer

### 3.1 Use the provided fixed zip file
The project includes a corrected zip file that should be used:
```bash
cd ~/Sandeep/projects/Vproptrader
ls -la mt5_ea_fixed.zip
```

### 3.2 If you need to create a new zip file
```bash
cd ~/Sandeep/projects/Vproptrader
zip -r mt5_ea_transfer.zip mt5_ea/
```

## Step 4: Transfer Files to Windows

### 4.1 Using SCP (from Ubuntu)
```bash
scp ~/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip username@windows_ip:/path/to/destination/
```

### 4.2 Using WinSCP or FileZilla
1. Connect to Ubuntu server
2. Navigate to `~/Sandeep/projects/Vproptrader/`
3. Download [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip)
4. Transfer to Windows machine

## Step 5: Extract and Place Files on Windows

### 5.1 Locate MT5 Experts Folder
The typical path is:
```
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
```

### 5.2 Extract Files
1. Extract [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip) to a temporary location
2. Copy the contents to the MT5 Experts folder:
   ```
   MT5 Experts Folder/
   ├── QuantSupraAI.mq5
   ├── config.mqh
   └── Include/
       ├── RestClient.mqh
       ├── RiskManager.mqh
       ├── TradeEngine.mqh
       └── Governors.mqh
   ```

## Step 6: Configure EA on Windows

### 6.1 Edit config.mqh
Open [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh) in MetaEditor and update:
```cpp
input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";  // Replace with actual IP
input bool LogOnlyMode = true;  // Keep true for initial testing
```

### 6.2 Configure MT5 WebRequest
1. In MT5, go to **Tools → Options → Expert Advisors**
2. In "Allow WebRequest for listed URL:" section, add:
   ```
   http://YOUR_UBUNTU_IP:8000
   ```
3. Check "Allow DLL imports"

## Step 7: Compile EA

### 7.1 Open MetaEditor
Press F4 in MT5 or go to **Tools → MetaQuotes Language Editor**

### 7.2 Compile the EA
1. Open [QuantSupraAI.mq5](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/QuantSupraAI.mq5)
2. Press F7 or click **Compile**
3. Verify you see: "0 error(s), 0 warning(s)"

## Step 8: Attach EA to Chart

### 8.1 Open a Chart
Open a chart for one of the supported symbols (NAS100, XAUUSD, or EURUSD)

### 8.2 Attach the EA
1. In the **Navigator** panel (Ctrl+N), expand **Expert Advisors**
2. Find **QuantSupraAI**
3. Drag and drop onto the chart
4. In the EA settings dialog:
   - Check "Allow live trading" (even in log-only mode)
   - Verify settings are correct
   - Click OK

## Step 9: Verify Connection

### 9.1 Check MT5 Experts Log
1. Open **Toolbox** panel (Ctrl+T)
2. Go to **Experts** tab
3. Look for initialization messages:
   ```
   === Quant Ω Supra AI Expert Advisor ===
   Version: 1.00
   Sidecar URL: http://YOUR_UBUNTU_IP:8000
   ✓ REST Client initialized
   ✓ Risk Manager initialized
   ✓ Trade Engine initialized
   ✓ Governors initialized
   Testing connection to Sidecar Service...
   ✓ Sidecar connection successful
   EA Initialization Complete - Ready to Trade
   ```

### 9.2 Test from Windows Command Line
Open Command Prompt and run:
```cmd
curl http://YOUR_UBUNTU_IP:8000/health
```
Should return JSON response.

### 9.3 Monitor Sidecar Logs
On Ubuntu, monitor the Sidecar logs:
```bash
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```
Look for requests from the EA.

## Step 10: Test in Log-Only Mode

### 10.1 Monitor for 1 Hour
- Watch MT5 Experts log for signal requests every 1-2 seconds
- Look for "LOG-ONLY MODE: Would execute..." messages
- Verify no connection errors
- Check that latency is acceptable (<400ms)

### 10.2 Verify Sidecar Logs
On Ubuntu:
```bash
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```
Look for:
- `GET /api/signals` requests
- Signal generation (if any)
- No errors

## Step 11: Enable Live Trading (When Ready)

### 11.1 Update Configuration
1. Edit [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh):
   ```cpp
   input bool LogOnlyMode = false;
   ```
2. Recompile (F7)
3. Remove EA from chart
4. Attach EA again

### 11.2 Enable AutoTrading
In MT5 toolbar, click the AutoTrading button (should turn green)

### 11.3 Monitor First Trade
- Watch for first signal
- Verify trade execution
- Check stop loss and take profit
- Monitor PnL tracking
- Verify no errors

## Common Issues and Solutions

### Issue 1: "WebRequest error: 4060 - Function not allowed"
**Solution**: Add the Sidecar URL to MT5's WebRequest allowed list:
1. Tools → Options → Expert Advisors
2. Add `http://YOUR_UBUNTU_IP:8000` to allowed URLs

### Issue 2: Connection Timeout
**Solution**: 
1. Increase timeout in [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh):
   ```cpp
   input int RequestTimeout = 10000;
   ```
2. Check network connectivity between machines

### Issue 3: No Signals Generated
**Solution**:
1. Check trading hours (London 07:00-10:00 UTC or NY 13:30-16:00 UTC)
2. Verify market is open
3. Test manually:
   ```bash
   curl http://YOUR_UBUNTU_IP:8000/api/signals?equity=1000
   ```

### Issue 4: Compilation Errors
**Solution**:
1. Ensure all Include files are present
2. Verify file placement in correct directories
3. Check for syntax errors in MetaEditor

## Verification Checklist

### Initial Setup
- [ ] Sidecar running on Ubuntu
- [ ] Firewall port 8000 open
- [ ] Can curl health endpoint from Ubuntu
- [ ] Can curl health endpoint from Windows
- [ ] EA files copied to Windows MT5
- [ ] config.mqh updated with Ubuntu IP
- [ ] EA compiled successfully
- [ ] EA attached to chart
- [ ] Smiley face icon visible

### Testing
- [ ] Connection successful in MT5 log
- [ ] Signal requests every 1-2 seconds
- [ ] No errors in MT5 log
- [ ] No errors in Sidecar log
- [ ] Tested for 1 hour minimum
- [ ] Log-only mode working correctly

### Production
- [ ] Paper trading complete (1 week)
- [ ] Zero violations
- [ ] Performance acceptable
- [ ] Ready to enable live trading

## Additional Tips

1. **Network Optimization**: If possible, place both machines on the same local network to minimize latency.

2. **Security**: Restrict firewall access to only your Windows IP:
   ```bash
   sudo ufw allow from YOUR_WINDOWS_IP to any port 8000
   ```

3. **Backup Configuration**: Keep a backup of your working [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh) file.

4. **Monitoring**: Regularly check both MT5 logs and Sidecar logs for any issues.

5. **Updates**: When updating the EA, always recompile and verify it works in log-only mode before enabling live trading.

## Conclusion

By following these steps, you should be able to successfully set up and run the Vproptrader project with the MT5 EA connecting to the Sidecar service on Ubuntu. Always start with log-only mode for testing and only enable live trading after thorough verification.