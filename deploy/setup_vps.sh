#!/bin/bash
# VPS Setup Script for Ubuntu 20.04+
# Run as: sudo bash setup_vps.sh

set -e

echo "========================================="
echo "Quant Ω Supra AI - VPS Setup"
echo "========================================="

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install Python 3.11
echo "Installing Python 3.11..."
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev

# Install Redis
echo "Installing Redis..."
apt install -y redis-server
systemctl enable redis-server
systemctl start redis-server

# Install system dependencies
echo "Installing system dependencies..."
apt install -y \
    build-essential \
    git \
    curl \
    wget \
    nginx \
    supervisor \
    htop \
    vim

# Install pip for Python 3.11
echo "Installing pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Configure firewall
echo "Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Sidecar API
ufw --force enable

# Create application user
echo "Creating application user..."
if ! id -u vprop > /dev/null 2>&1; then
    useradd -m -s /bin/bash vprop
    echo "User 'vprop' created"
fi

# Create application directories
echo "Creating application directories..."
mkdir -p /opt/vproptrader
mkdir -p /var/log/vproptrader
mkdir -p /var/lib/vproptrader/data
mkdir -p /var/lib/vproptrader/models
mkdir -p /var/lib/vproptrader/backups

chown -R vprop:vprop /opt/vproptrader
chown -R vprop:vprop /var/log/vproptrader
chown -R vprop:vprop /var/lib/vproptrader

# Configure Redis
echo "Configuring Redis..."
sed -i 's/^bind 127.0.0.1/bind 127.0.0.1/' /etc/redis/redis.conf
sed -i 's/^# maxmemory <bytes>/maxmemory 512mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
systemctl restart redis-server

# Test Redis
echo "Testing Redis..."
redis-cli ping

echo "========================================="
echo "VPS Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Clone repository to /opt/vproptrader"
echo "2. Run deploy_sidecar.sh"
echo "3. Configure environment variables"
echo ""
