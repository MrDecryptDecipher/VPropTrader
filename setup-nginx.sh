#!/bin/bash

# VPropTrader Nginx Setup Script
# This script configures nginx to proxy external ports to internal services

set -e

echo "========================================="
echo "VPropTrader Nginx Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run with sudo"
    echo "Usage: sudo bash setup-nginx.sh"
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NGINX_CONF="$SCRIPT_DIR/vproptrader-nginx.conf"

echo "📁 Working directory: $SCRIPT_DIR"
echo ""

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx is not installed"
    echo "Install it with: sudo apt-get update && sudo apt-get install nginx"
    exit 1
fi

echo "✅ Nginx is installed"
echo ""

# Check if config file exists
if [ ! -f "$NGINX_CONF" ]; then
    echo "❌ Nginx config file not found: $NGINX_CONF"
    exit 1
fi

echo "✅ Config file found: $NGINX_CONF"
echo ""

# Backup existing config if it exists
if [ -f /etc/nginx/sites-available/vproptrader ]; then
    echo "📦 Backing up existing config..."
    cp /etc/nginx/sites-available/vproptrader /etc/nginx/sites-available/vproptrader.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
    echo ""
fi

# Copy config to nginx sites-available
echo "📋 Copying config to /etc/nginx/sites-available/vproptrader..."
cp "$NGINX_CONF" /etc/nginx/sites-available/vproptrader
echo "✅ Config copied"
echo ""

# Create symlink in sites-enabled
echo "🔗 Creating symlink in sites-enabled..."
ln -sf /etc/nginx/sites-available/vproptrader /etc/nginx/sites-enabled/vproptrader
echo "✅ Symlink created"
echo ""

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo ""
else
    echo "❌ Nginx configuration test failed"
    echo "Please check the error messages above"
    exit 1
fi

# Reload nginx
echo "🔄 Reloading nginx..."
systemctl reload nginx
echo "✅ Nginx reloaded"
echo ""

# Check if nginx is running
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "⚠️  Nginx is not running, attempting to start..."
    systemctl start nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx started successfully"
    else
        echo "❌ Failed to start nginx"
        exit 1
    fi
fi

echo ""
echo "========================================="
echo "✅ Nginx Setup Complete!"
echo "========================================="
echo ""
echo "Port Mappings:"
echo "  External Port 4001 → Internal Port 3001 (Dashboard)"
echo "  External Port 8000 → Internal Port 8001 (Sidecar API)"
echo ""
echo "Test External Access:"
echo "  Dashboard: http://3.111.22.56:4001"
echo "  API:       http://3.111.22.56:8000/health"
echo ""
echo "Check Nginx Status:"
echo "  sudo systemctl status nginx"
echo ""
echo "View Nginx Logs:"
echo "  sudo tail -f /var/log/nginx/error.log"
echo "  sudo tail -f /var/log/nginx/access.log"
echo ""
