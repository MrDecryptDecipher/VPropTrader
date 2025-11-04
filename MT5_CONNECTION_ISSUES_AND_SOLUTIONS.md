# MT5 Connection Issues and Solutions for Vproptrader Project

## Overview

This document outlines the common issues encountered when setting up and running the Vproptrader project, specifically focusing on transferring and executing the MT5 Expert Advisor (EA) from an Ubuntu server to a Windows host machine running MetaTrader 5 (MT5). It also provides detailed solutions for these issues.

## Common Issues and Solutions

### 1. Connection Issues Between Windows MT5 and Ubuntu Sidecar

#### Issue
The MT5 EA running on Windows cannot connect to the Sidecar service running on the Ubuntu server.

#### Root Causes
1. **Firewall blocking**: The Ubuntu firewall is not configured to allow incoming connections on port 8000.
2. **Network configuration**: The Sidecar service is only listening on localhost (127.0.0.1) instead of all interfaces (0.0.0.0).
3. **Incorrect IP address**: Wrong IP address configured in the EA's [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh) file.
4. **Security group restrictions**: If using a cloud provider (AWS, Azure, etc.), security groups are not configured to allow port 8000.

#### Solutions
1. **Configure Ubuntu firewall**:
   ```bash
   sudo ufw allow 8000/tcp
   sudo ufw status
   ```

2. **Verify Sidecar configuration**:
   Check that the Sidecar service is configured to listen on all interfaces:
   ```python
   # In sidecar/app/core/config.py
   host: str = "0.0.0.0"  # Not "127.0.0.1"
   ```

3. **Verify network binding**:
   ```bash
   netstat -tuln | grep 8000
   # Should show: 0.0.0.0:8000 (not 127.0.0.1:8000)
   ```

4. **Configure cloud security groups** (if applicable):
   - AWS: Add inbound rule for TCP port 8000 from your IP or 0.0.0.0/0
   - Azure: Add Network Security Group rule for port 8000

5. **Update EA configuration**:
   In [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh), ensure the correct IP address is used:
   ```cpp
   input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";
   ```

### 2. WebRequest Error 4060 - Function Not Allowed

#### Issue
MT5 logs show "WebRequest error: 4060 - Function not allowed"

#### Root Cause
The URL is not added to MT5's allowed list for WebRequest calls.

#### Solution
1. In MT5, go to **Tools → Options → Expert Advisors**
2. In the "Allow WebRequest for listed URL:" section, add your Sidecar URL:
   ```
   http://YOUR_UBUNTU_IP:8000
   ```
3. Or enable "Allow DLL imports" which may resolve the issue

### 3. Connection Timeout Issues

#### Issue
The EA fails to connect to the Sidecar service with timeout errors.

#### Root Causes
1. **Network latency**: High latency between Windows and Ubuntu machines.
2. **Server overload**: Sidecar service is not responding in time.
3. **Incorrect timeout configuration**: The default timeout is too short.

#### Solutions
1. **Increase timeout in EA**:
   In [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh), adjust the timeout:
   ```cpp
   input int RequestTimeout = 10000;  // Increase from 5000 to 10000 ms
   ```

2. **Optimize network connection**:
   - Use a wired connection if possible
   - Ensure both machines are on the same network if possible
   - Check for network congestion

3. **Verify Sidecar performance**:
   Check Sidecar logs for any performance issues:
   ```bash
   tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
   ```

### 4. File Transfer and Compilation Issues

#### Issue
Errors when transferring EA files from Ubuntu to Windows or during compilation.

#### Root Causes
1. **Incomplete file transfer**: Missing or corrupted files during transfer.
2. **Incorrect file placement**: Files not placed in the correct MT5 directories.
3. **File permission issues**: Read-only files preventing compilation.

#### Solutions
1. **Use the provided zip file**:
   The project includes a corrected zip file [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip) that should be used:
   ```bash
   # On Ubuntu
   cd ~/Sandeep/projects/Vproptrader
   # Transfer mt5_ea_fixed.zip to Windows
   ```

2. **Correct file placement**:
   Ensure files are placed in the correct directories:
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

3. **Compilation steps**:
   - Open MetaEditor (F4 in MT5)
   - Open [QuantSupraAI.mq5](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/QuantSupraAI.mq5)
   - Click Compile (F7)
   - Check for "0 error(s), 0 warning(s)" message

### 5. "No Signals" Issue

#### Issue
The EA connects successfully but no trading signals are received.

#### Root Causes
1. **Outside trading hours**: The system only generates signals during specific trading sessions (London 07:00-10:00 UTC or NY 13:30-16:00 UTC).
2. **Market closed**: No trading opportunities during weekends or holidays.
3. **System selectivity**: The AI system is highly selective and may skip most setups.

#### Solutions
1. **Check trading hours**:
   Ensure testing is done during active trading sessions.

2. **Verify system is working**:
   Test the signals endpoint manually:
   ```bash
   curl http://YOUR_UBUNTU_IP:8000/api/signals?equity=1000
   ```

3. **Check Sidecar logs**:
   ```bash
   tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
   ```

### 6. SSL/HTTPS Issues

#### Issue
Connection fails when trying to use HTTPS instead of HTTP.

#### Root Cause
The Sidecar service is not configured with SSL certificates.

#### Solution
Use HTTP instead of HTTPS in the EA configuration:
```cpp
input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";  // Not https://
```

## Detailed Setup Process

### Ubuntu Sidecar Setup

1. **Start Sidecar service**:
   ```bash
   cd ~/Sandeep/projects/Vproptrader/sidecar
   source venv/bin/activate
   python -m app.main
   ```

2. **Verify service is running**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Configure firewall**:
   ```bash
   sudo ufw allow 8000/tcp
   ```

4. **Get Ubuntu IP address**:
   ```bash
   hostname -I
   ```

### Windows MT5 Setup

1. **Transfer files**:
   - Use the [mt5_ea_fixed.zip](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea_fixed.zip) file
   - Extract to MT5 Experts folder:
     ```
     C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
     ```

2. **Configure EA**:
   Edit [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh):
   ```cpp
   input string SidecarURL = "http://YOUR_UBUNTU_IP:8000";
   input bool LogOnlyMode = true;  // Start with true for testing
   ```

3. **Compile EA**:
   - Open MetaEditor (F4)
   - Open [QuantSupraAI.mq5](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/QuantSupraAI.mq5)
   - Compile (F7)
   - Verify "0 error(s), 0 warning(s)"

4. **Configure MT5 WebRequest**:
   - Tools → Options → Expert Advisors
   - Add your Sidecar URL to allowed list

5. **Attach EA to chart**:
   - Open chart for trading symbol (NAS100, XAUUSD, or EURUSD)
   - Navigator → Expert Advisors → QuantSupraAI
   - Drag to chart
   - Enable "Allow live trading"

## Testing and Verification

### Connection Testing

1. **Test from Windows command line**:
   ```cmd
   curl http://YOUR_UBUNTU_IP:8000/health
   ```

2. **Check MT5 Experts log**:
   Look for successful initialization messages:
   ```
   === Quant Ω Supra AI Expert Advisor ===
   ✓ REST Client initialized
   ✓ Risk Manager initialized
   ✓ Trade Engine initialized
   ✓ Governors initialized
   ✓ Sidecar connection successful
   ```

3. **Monitor Sidecar logs**:
   ```bash
   tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
   ```

### Log-Only Mode Testing

1. **Enable log-only mode**:
   ```cpp
   input bool LogOnlyMode = true;
   ```

2. **Monitor for 1 hour**:
   - Watch for signal requests every 1-2 seconds
   - Look for "LOG-ONLY MODE: Would execute..." messages
   - Verify no connection errors

## Troubleshooting Checklist

### Pre-Requirements
- [ ] Ubuntu machine with Sidecar installed and running
- [ ] Windows machine with MT5 installed
- [ ] Network connectivity between machines
- [ ] Python 3.11+ on Ubuntu
- [ ] Redis running on Ubuntu

### Connection Setup
- [ ] Sidecar configured to listen on 0.0.0.0:8000
- [ ] Ubuntu firewall allows port 8000
- [ ] Cloud security groups allow port 8000 (if applicable)
- [ ] Correct IP address in EA configuration
- [ ] URL added to MT5 WebRequest allowed list

### File Transfer
- [ ] All EA files transferred correctly
- [ ] Files placed in correct MT5 directories
- [ ] EA compiles with 0 errors
- [ ] EA attached to chart successfully

### Operation Verification
- [ ] EA polls Sidecar every 1-2 seconds
- [ ] No connection timeouts or errors
- [ ] Signals are generated (if market conditions allow)
- [ ] Log-only mode logs decisions correctly
- [ ] Latency is acceptable (<400ms)

## Advanced Configuration

### Performance Optimization

1. **Adjust polling interval**:
   In [config.mqh](file:///home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/config.mqh):
   ```cpp
   input int PollInterval = 2000;  // Increase to reduce load
   ```

2. **Optimize timeout settings**:
   ```cpp
   input int RequestTimeout = 10000;  // Increase for high latency networks
   ```

### Security Considerations

1. **Restrict firewall access**:
   Instead of allowing all IPs, restrict to specific IP:
   ```bash
   sudo ufw allow from YOUR_WINDOWS_IP to any port 8000
   ```

2. **Use VPN for secure connection**:
   Set up a VPN between Windows and Ubuntu machines for secure communication.

## Conclusion

Setting up the Vproptrader project to work between Ubuntu and Windows requires careful attention to network configuration, file transfer, and MT5-specific settings. By following the solutions outlined in this document, most connection issues can be resolved. Always start with log-only mode for testing before enabling live trading, and monitor both MT5 logs and Sidecar logs for any issues.

Regular monitoring and maintenance of the connection between the EA and Sidecar service is essential for reliable operation of the Vproptrader system.