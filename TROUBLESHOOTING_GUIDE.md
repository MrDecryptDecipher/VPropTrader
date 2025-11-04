# Vproptrader MT5 Connection Troubleshooting Guide

## Overview

This document provides a comprehensive troubleshooting guide for resolving common issues encountered when setting up and running the Vproptrader project, specifically focusing on transferring and executing the MT5 Expert Advisor (EA) from an Ubuntu server to a Windows host machine running MetaTrader 5 (MT5).

## Error Categories and Solutions

### 1. Connection Errors

#### Error: "Connection failed" or "Timeout"
**Symptoms**: 
- MT5 Experts log shows "Connection failed" or "Timeout" messages
- EA cannot connect to Sidecar service

**Root Causes**:
1. Incorrect IP address in EA configuration
2. Firewall blocking port 8000
3. Sidecar service not running
4. Network connectivity issues

**Solutions**:
1. **Verify IP address**:
   ```bash
   # On Ubuntu
   hostname -I
   ```
   Ensure this IP is correctly set in [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh):
   ```cpp
   input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";
   ```

2. **Check Sidecar service**:
   ```bash
   # On Ubuntu
   curl http://localhost:8000/health
   ```
   If this fails, start the Sidecar service:
   ```bash
   cd ~/Sandeep/projects/Vproptrader/sidecar
   source venv/bin/activate
   python -m app.main
   ```

3. **Verify firewall settings**:
   ```bash
   # On Ubuntu
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

4. **Test network connectivity**:
   ```cmd
   # On Windows Command Prompt
   ping YOUR_UBUNTU_IP
   curl http://YOUR_UBUNTU_IP:8000/health
   ```

#### Error: "HTTP error: 404 Not Found"
**Symptoms**: 
- MT5 Experts log shows "HTTP error: 404 Not Found"
- EA cannot find the Sidecar endpoints

**Root Causes**:
1. Incorrect Sidecar URL in EA configuration
2. Sidecar service not properly started

**Solutions**:
1. **Verify Sidecar URL**:
   In [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh), ensure the URL is correct:
   ```cpp
   input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";  // No trailing slash
   ```

2. **Restart Sidecar service**:
   ```bash
   # On Ubuntu
   cd ~/Sandeep/projects/Vproptrader/sidecar
   source venv/bin/activate
   python -m app.main
   ```

### 2. WebRequest Errors

#### Error: "WebRequest error: 4060 - Function not allowed"
**Symptoms**: 
- MT5 Experts log shows "WebRequest error: 4060 - Function not allowed"
- EA cannot make HTTP requests to Sidecar

**Root Causes**:
1. URL not added to MT5's WebRequest allowed list
2. Incorrect URL format

**Solutions**:
1. **Add URL to allowed list**:
   - In MT5, go to **Tools → Options → Expert Advisors**
   - In "Allow WebRequest for listed URL:" section, add:
     ```
     http://YOUR_UBUNTU_IP:8000
     ```
   - Click OK

2. **Verify URL format**:
   Ensure the URL in [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh) uses HTTP (not HTTPS):
   ```cpp
   input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";
   ```

#### Error: "WebRequest error: 1001" or "WebRequest error: 1002"
**Symptoms**: 
- MT5 Experts log shows "WebRequest error: 1001" or "WebRequest error: 1002"
- Network-level connection issues

**Root Causes**:
1. Network connectivity issues
2. Firewall blocking connection
3. DNS resolution problems

**Solutions**:
1. **Test network connectivity**:
   ```cmd
   # On Windows Command Prompt
   ping YOUR_UBUNTU_IP
   ```

2. **Check firewall settings**:
   - On Ubuntu:
     ```bash
     sudo ufw status
     sudo ufw allow 8000/tcp
     ```
   - On Windows: Check Windows Firewall settings

3. **Use IP address instead of hostname**:
   In [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh), use the IP address directly:
   ```cpp
   input string SidecarURL = "http://192.168.1.100:8000";  // Use actual IP
   ```

### 3. Compilation Errors

#### Error: "Cannot open include file"
**Symptoms**: 
- MetaEditor shows "Cannot open include file" errors
- EA fails to compile

**Root Causes**:
1. Missing Include files
2. Incorrect file placement
3. File permission issues

**Solutions**:
1. **Verify file placement**:
   Ensure all files are in the correct directories:
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

2. **Use the provided zip file**:
   Use [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip) which contains all necessary files:
   ```bash
   # On Ubuntu
   cd ~/Sandeep/projects/Vproptrader
   # Transfer mt5_ea_fixed.zip to Windows
   ```

3. **Check file permissions**:
   Ensure files are not read-only on Windows.

#### Error: "Syntax error"
**Symptoms**: 
- MetaEditor shows syntax errors
- EA fails to compile

**Root Causes**:
1. Corrupted file transfer
2. Editing files on Windows instead of Ubuntu
3. Character encoding issues

**Solutions**:
1. **Re-transfer files**:
   Use the [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip) file and avoid editing files on Windows.

2. **Refresh MetaEditor**:
   - Press F5 in MetaEditor to refresh
   - Close and reopen MetaEditor

### 4. Runtime Errors

#### Error: "No signals received"
**Symptoms**: 
- EA connects successfully but no trading signals are received
- MT5 log shows "No trading signals available"

**Root Causes**:
1. Outside trading hours
2. Market closed
3. System selectivity (no high-quality setups)

**Solutions**:
1. **Check trading hours**:
   The system only generates signals during:
   - London session: 07:00-10:00 UTC
   - NY session: 13:30-16:00 UTC

2. **Test manually**:
   ```bash
   # On Ubuntu
   curl http://localhost:8000/api/signals?equity=1000
   ```

3. **Check Sidecar logs**:
   ```bash
   # On Ubuntu
   tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
   ```

#### Error: "Invalid pointer access" or "Array out of range"
**Symptoms**: 
- MT5 crashes or shows "Invalid pointer access" errors
- EA stops working unexpectedly

**Root Causes**:
1. Memory management issues in EA code
2. Corrupted EA files

**Solutions**:
1. **Re-transfer and recompile EA**:
   - Use the [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip) file
   - Delete existing EA files
   - Extract fresh files
   - Recompile in MetaEditor

2. **Restart MT5**:
   - Close MT5 completely
   - Restart MT5
   - Reattach EA

### 5. Performance Issues

#### Issue: High latency
**Symptoms**: 
- Slow response times
- Delays in signal processing

**Root Causes**:
1. Network latency between Windows and Ubuntu
2. Overloaded Sidecar service
3. Insufficient system resources

**Solutions**:
1. **Optimize network connection**:
   - Use wired connection if possible
   - Ensure both machines are on the same network

2. **Adjust polling interval**:
   In [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh):
   ```cpp
   input int PollInterval = 3000;  // Increase from default 1500
   ```

3. **Check system resources**:
   - Monitor CPU and memory usage on Ubuntu
   - Ensure adequate resources for Sidecar service

## Diagnostic Commands

### Ubuntu Side
```bash
# Check if Sidecar is running
curl http://localhost:8000/health

# Check network binding
netstat -tuln | grep 8000

# Check firewall
sudo ufw status

# Get IP address
hostname -I

# Monitor logs
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```

### Windows Side
```cmd
# Test connectivity
ping YOUR_UBUNTU_IP

# Test Sidecar health endpoint
curl http://YOUR_UBUNTU_IP:8000/health

# Test signals endpoint
curl http://YOUR_UBUNTU_IP:8000/api/signals?equity=1000
```

## MT5 Configuration Verification

1. **WebRequest Settings**:
   - Tools → Options → Expert Advisors
   - Verify "Allow WebRequest for listed URL:" includes your Sidecar URL
   - Check "Allow DLL imports" is enabled

2. **AutoTrading**:
   - Ensure AutoTrading button is enabled (green) in MT5 toolbar
   - Check "Allow live trading" when attaching EA to chart

3. **Expert Advisors Settings**:
   - Tools → Options → Expert Advisors
   - Verify settings allow the EA to run properly

## Log Analysis

### MT5 Experts Log
Look for these key messages:
```
=== Quant Ω Supra AI Expert Advisor ===
✓ REST Client initialized
✓ Risk Manager initialized
✓ Trade Engine initialized
✓ Governors initialized
Testing connection to Sidecar Service...
✓ Sidecar connection successful
EA Initialization Complete - Ready to Trade
```

Error messages to watch for:
```
WebRequest error: 4060 - Function not allowed
Connection failed
Timeout
HTTP error: 404 Not Found
```

### Sidecar Logs
Monitor for:
- Incoming requests: `GET /api/signals`
- Signal generation
- Error messages
- Connection logs

```bash
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```

## Recovery Procedures

### If EA becomes unresponsive
1. Remove EA from chart
2. Restart MT5
3. Reattach EA to chart
4. Verify connection in Experts log

### If Sidecar service fails
1. Check if service is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Restart service:
   ```bash
   cd ~/Sandeep/projects/Vproptrader/sidecar
   source venv/bin/activate
   python -m app.main
   ```

### If network connectivity is lost
1. Verify network connection between machines
2. Check firewall settings on both machines
3. Restart network services if necessary
4. Re-test connectivity:
   ```cmd
   ping YOUR_UBUNTU_IP
   ```

## Prevention Best Practices

1. **Regular Monitoring**:
   - Check MT5 Experts log regularly
   - Monitor Sidecar logs for errors
   - Verify connectivity periodically

2. **Backup Configuration**:
   - Keep backups of working [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh) files
   - Document working IP addresses and settings

3. **Update Procedures**:
   - Always test in log-only mode after updates
   - Verify all files are transferred correctly
   - Recompile EA after any file changes

4. **Network Stability**:
   - Use wired connections when possible
   - Ensure consistent IP addresses (consider static IPs)
   - Monitor network performance

## Conclusion

This troubleshooting guide covers the most common issues encountered when setting up the Vproptrader project. By following the diagnostic steps and solutions provided, most connection and runtime issues can be resolved. Always start with basic connectivity tests and work your way through the more complex issues if needed. Regular monitoring and maintenance are key to ensuring reliable operation of the Vproptrader system.