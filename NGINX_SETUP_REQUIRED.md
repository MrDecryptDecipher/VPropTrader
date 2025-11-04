# VPropTrader - Nginx Setup Required

## Issue Identified

The services are running on PM2 but are NOT accessible via public IP because:

1. **Next.js dev server** binds to `localhost` only by default (not 0.0.0.0)
2. **Python uvicorn** can bind to 0.0.0.0 but there may be firewall restrictions
3. **Direct port access** from public IP is timing out

## Solution: Nginx Reverse Proxy

Use Nginx to proxy external ports (4001, 8000) to internal services (3000, 8001).

### Architecture:
```
Public IP:4001 → Nginx → localhost:3000 (Next.js Dashboard)
Public IP:8000 → Nginx → localhost:8001 (Python Sidecar)
```

## Setup Steps

### Option 1: Automated Setup (Recommended)

Run the setup script:
```bash
cd /home/ubuntu/Sandeep/projects/Vproptrader
./setup-nginx-proxy.sh
```

This script will:
1. Copy nginx configuration to `/etc/nginx/sites-available/`
2. Enable the site
3. Test and reload nginx
4. Restart PM2 services with new internal ports

### Option 2: Manual Setup

1. **Copy Nginx Configuration**:
```bash
sudo cp /home/ubuntu/Sandeep/projects/Vproptrader/vproptrader-nginx.conf /etc/nginx/sites-available/vproptrader
```

2. **Enable the Site**:
```bash
sudo ln -sf /etc/nginx/sites-available/vproptrader /etc/nginx/sites-enabled/vproptrader
```

3. **Test Nginx Configuration**:
```bash
sudo nginx -t
```

4. **Reload Nginx**:
```bash
sudo systemctl reload nginx
```

5. **Restart PM2 Services**:
```bash
cd /home/ubuntu/Sandeep/projects/Vproptrader
pm2 restart ecosystem.config.js
```

## Verification

After setup, test the services:

### From Server:
```bash
# Test dashboard
curl -I http://3.111.22.56:4001

# Test API
curl http://3.111.22.56:8000/health
```

### From Browser:
- Dashboard: http://3.111.22.56:4001
- API Docs: http://3.111.22.56:8000/docs

## Current Configuration

### PM2 Services (Internal):
- **Dashboard**: localhost:3000
- **Sidecar API**: localhost:8001

### Nginx Proxy (External):
- **Dashboard**: 0.0.0.0:4001 → localhost:3000
- **Sidecar API**: 0.0.0.0:8000 → localhost:8001

## Files Created

1. `vproptrader-nginx.conf` - Nginx configuration
2. `setup-nginx-proxy.sh` - Automated setup script
3. `ecosystem.config.js` - Updated with internal ports (3000, 8001)

## Troubleshooting

### If Nginx Fails to Start:
```bash
# Check nginx error log
sudo tail -50 /var/log/nginx/error.log

# Check if ports are already in use
sudo lsof -i :4001
sudo lsof -i :8000
```

### If Services Don't Respond:
```bash
# Check PM2 status
pm2 list

# Check PM2 logs
pm2 logs vproptrader-dashboard
pm2 logs vproptrader-sidecar

# Verify internal services are running
curl http://localhost:3000
curl http://localhost:8001/health
```

### If Public IP Still Doesn't Work:
1. Verify AWS Lightsail firewall rules (ports 4001, 8000 open)
2. Check if nginx is running: `sudo systemctl status nginx`
3. Verify nginx is listening: `sudo ss -tlnp | grep nginx`
4. Check for iptables rules: `sudo iptables -L -n | grep -E "4001|8000"`

## Why This Approach?

1. **Next.js Limitation**: Dev server doesn't reliably bind to 0.0.0.0
2. **Security**: Services run on localhost, nginx handles external access
3. **Flexibility**: Easy to add SSL, rate limiting, etc. via nginx
4. **Standard Practice**: This is how most production deployments work

## Next Steps

1. Run `./setup-nginx-proxy.sh` (requires sudo password)
2. Test access from browser
3. If working, consider setting up SSL with Let's Encrypt
4. Set up PM2 to auto-start on reboot: `pm2 save && pm2 startup`

---

**Status**: ⚠️ SETUP REQUIRED  
**Action Needed**: Run the setup script with sudo access
