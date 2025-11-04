# AWS Lightsail Firewall Configuration Guide

## Current Issue

Your VPropTrader services are running correctly on the server, but external connections to ports 4001 and 8002 are timing out even though you've added firewall rules in AWS Lightsail.

## Diagnosis Results

From the server:
- ✅ Nginx is listening on 0.0.0.0:4001 and 0.0.0.0:8002
- ✅ Services work on localhost
- ❌ Server cannot ping its own public IP (3.111.22.56)
- ❌ External connections timeout

**This indicates the AWS Lightsail firewall rules may not be correctly configured.**

---

## Step-by-Step Fix

### Step 1: Verify Current Firewall Rules in AWS Lightsail

1. Go to https://lightsail.aws.amazon.com/
2. Click on your instance
3. Click the "Networking" tab
4. Look at the "Firewall" section

You should see these rules:

| Application | Protocol | Port or range | Restricted to IP address |
|-------------|----------|---------------|--------------------------|
| SSH | TCP | 22 | (any IP) |
| HTTP | TCP | 80 | (any IP) |
| HTTPS | TCP | 443 | (any IP) |
| Custom | TCP | 4001 | (any IP) |
| Custom | TCP | 8002 | (any IP) |

### Step 2: Check If Rules Are Actually There

**Important**: Make sure you see BOTH ports 4001 AND 8002 in the list.

If you don't see them:
1. Click "+ Add rule"
2. Select "Custom" from the Application dropdown
3. Select "TCP" for Protocol
4. Enter "4001" for Port or range
5. Leave "Restrict to IP address" empty (or use 0.0.0.0/0)
6. Click "Create"
7. Repeat for port 8002

### Step 3: Verify the Rules Are Applied

After adding the rules, wait 30-60 seconds for them to take effect, then test:

```bash
# From your local machine (not the server):
curl -v http://3.111.22.56:4001
curl -v http://3.111.22.56:8002/health
```

---

## Common Issues and Solutions

### Issue 1: Rules Added But Still Not Working

**Possible Cause**: Rules were added to the wrong instance

**Solution**:
1. In Lightsail console, verify you're looking at the correct instance
2. Check the instance's public IP matches 3.111.22.56
3. If you have multiple instances, make sure you added rules to the right one

### Issue 2: IPv6 Firewall Rules

**Possible Cause**: You only added IPv4 rules but your connection is using IPv6

**Solution**:
1. In the Lightsail firewall section, check if there's an IPv6 tab
2. Add the same rules for IPv6 if needed
3. Or disable IPv6 on the instance

### Issue 3: Instance Behind a Load Balancer

**Possible Cause**: The instance is behind a Lightsail load balancer

**Solution**:
1. Check if you have a load balancer configured
2. If yes, add the firewall rules to the load balancer instead
3. Or remove the load balancer and connect directly to the instance

### Issue 4: VPC Peering or Custom Networking

**Possible Cause**: Instance is in a custom VPC with additional security groups

**Solution**:
1. Check if the instance is in a VPC
2. If yes, check VPC security groups in addition to Lightsail firewall
3. You may need to configure both

---

## Alternative: Use Different Ports

If the firewall configuration continues to fail, we can use ports that are already open:

### Option A: Use Port 80 (HTTP)

Change nginx to listen on port 80 for the dashboard:

```bash
# This would make dashboard accessible at:
http://3.111.22.56/
```

### Option B: Use Port 443 (HTTPS)

Set up SSL and use port 443:

```bash
# This would make dashboard accessible at:
https://3.111.22.56/
```

---

## Testing from Server

The fact that the server can't ping its own public IP is normal for AWS - this is called "hairpin NAT" and AWS doesn't support it. So don't worry about that.

What matters is testing from OUTSIDE the server.

### Test from Your Local Machine

```bash
# Test if port is reachable (should connect even if it returns error)
telnet 3.111.22.56 4001

# Or use curl with verbose output
curl -v --max-time 10 http://3.111.22.56:4001

# Test API port
curl -v --max-time 10 http://3.111.22.56:8002/health
```

**Expected Results**:
- ✅ Connection succeeds (even if page doesn't load)
- ❌ Connection timeout = firewall blocking

---

## Screenshot Guide

If you're still having issues, take screenshots of:

1. **Lightsail Networking Tab**
   - Show the full firewall rules list
   - Make sure ports 4001 and 8002 are visible

2. **Instance Details**
   - Show the public IP address
   - Confirm it's 3.111.22.56

3. **Error Message**
   - Show the exact error when trying to connect

---

## Verification Checklist

Before asking for help, verify:

- [ ] You're logged into the correct AWS account
- [ ] You're looking at the correct Lightsail instance
- [ ] The instance public IP is 3.111.22.56
- [ ] Port 4001 is listed in firewall rules
- [ ] Port 8002 is listed in firewall rules
- [ ] Rules show "Any IP" or "0.0.0.0/0" (not restricted)
- [ ] You waited 60 seconds after adding rules
- [ ] You tested from a different network (not the server itself)

---

## Quick Test Commands

### From Your Local Machine (Windows)

```powershell
# Test port 4001
Test-NetConnection -ComputerName 3.111.22.56 -Port 4001

# Test port 8002
Test-NetConnection -ComputerName 3.111.22.56 -Port 8002
```

### From Your Local Machine (Mac/Linux)

```bash
# Test port 4001
nc -zv 3.111.22.56 4001

# Test port 8002
nc -zv 3.111.22.56 8002
```

**Expected Output if Working**:
```
Connection to 3.111.22.56 4001 port [tcp/*] succeeded!
```

**Expected Output if Blocked**:
```
Connection timed out
```

---

## If Nothing Works

If you've verified everything and it still doesn't work:

### Option 1: Use SSH Tunnel (Temporary Solution)

```bash
# From your local machine:
ssh -L 4001:localhost:4001 -L 8002:localhost:8002 ubuntu@3.111.22.56

# Then access:
http://localhost:4001  (Dashboard)
http://localhost:8002/health  (API)
```

### Option 2: Contact AWS Support

1. Go to AWS Support Center
2. Create a case about Lightsail firewall rules not working
3. Provide instance ID and the ports you're trying to open

### Option 3: Recreate the Instance

As a last resort:
1. Create a snapshot of your current instance
2. Create a new instance from the snapshot
3. Configure firewall rules BEFORE starting services
4. Test connectivity

---

## Current Server Status

Your services ARE working correctly:

```
✅ Sidecar API: Running on port 8001
✅ Dashboard: Running on port 3001
✅ Nginx: Listening on ports 4001 and 8002
✅ Internal connectivity: Working
❌ External connectivity: Blocked by firewall
```

The issue is 100% with the AWS Lightsail firewall configuration, not with your services or nginx.

---

## Next Steps

1. **Double-check the Lightsail firewall rules** (most common issue)
2. **Wait 60 seconds** after adding rules
3. **Test from external network** (not from the server)
4. **Try the test commands above** to verify ports are open
5. **If still blocked**, try using port 80 or 443 instead

Once the firewall is properly configured, your VPropTrader system will be immediately accessible.
