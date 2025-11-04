#!/bin/bash
# Deploy Sidecar Service to VPS
# Run as: bash deploy_sidecar.sh

set -e

echo "========================================="
echo "Deploying Sidecar Service"
echo "========================================="

# Configuration
APP_DIR="/opt/vproptrader"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="vprop-sidecar"

# Navigate to app directory
cd $APP_DIR

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv $VENV_DIR

# Activate virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
cd sidecar
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠ WARNING: Please edit .env with your credentials!"
fi

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Quant Ω Supra AI Sidecar Service
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=vprop
Group=vprop
WorkingDirectory=$APP_DIR/sidecar
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=append:/var/log/vproptrader/sidecar.log
StandardError=append:/var/log/vproptrader/sidecar-error.log

# Resource limits
LimitNOFILE=65536
MemoryLimit=2G

[Install]
WantedBy=multi-user.target
EOF

# Create log rotation config
echo "Configuring log rotation..."
sudo tee /etc/logrotate.d/vproptrader > /dev/null <<EOF
/var/log/vproptrader/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 vprop vprop
    sharedscripts
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

# Create nightly retrain cron job
echo "Setting up nightly retrain cron..."
(crontab -l 2>/dev/null || echo "") | grep -v "vprop_retrain" | \
    { cat; echo "0 2 * * * $VENV_DIR/bin/python -m app.ml.retraining_engine >> /var/log/vproptrader/retrain.log 2>&1 # vprop_retrain"; } | \
    crontab -

# Create backup cron job
echo "Setting up backup cron..."
(crontab -l 2>/dev/null || echo "") | grep -v "vprop_backup" | \
    { cat; echo "0 3 * * * cp /var/lib/vproptrader/data/trades.db /var/lib/vproptrader/backups/trades_\$(date +\\%Y\\%m\\%d).db # vprop_backup"; } | \
    crontab -

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service..."
sudo systemctl enable $SERVICE_NAME

# Start service
echo "Starting service..."
sudo systemctl start $SERVICE_NAME

# Wait a moment
sleep 3

# Check status
echo ""
echo "========================================="
echo "Service Status:"
echo "========================================="
sudo systemctl status $SERVICE_NAME --no-pager

# Test health endpoint
echo ""
echo "Testing health endpoint..."
sleep 2
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check failed"

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Log files:"
echo "  Output: /var/log/vproptrader/sidecar.log"
echo "  Errors: /var/log/vproptrader/sidecar-error.log"
echo ""
