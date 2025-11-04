#!/bin/bash
# VPropTrader Nginx Proxy Setup Script

echo "Setting up Nginx reverse proxy for VPropTrader..."

# Copy nginx config
sudo cp /home/ubuntu/Sandeep/projects/Vproptrader/vproptrader-nginx.conf /etc/nginx/sites-available/vproptrader

# Enable the site
sudo ln -sf /etc/nginx/sites-available/vproptrader /etc/nginx/sites-enabled/vproptrader

# Test nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Reloading..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Restart PM2 services with new ports
echo "Restarting PM2 services..."
cd /home/ubuntu/Sandeep/projects/Vproptrader
pm2 restart ecosystem.config.js

echo "✅ Setup complete!"
echo ""
echo "Services are now accessible at:"
echo "  Dashboard: http://3.111.22.56:4001"
echo "  API: http://3.111.22.56:8000"
echo ""
echo "Internal services running on:"
echo "  Dashboard: http://127.0.0.1:3000"
echo "  API: http://127.0.0.1:8001"
