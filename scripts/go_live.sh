#!/bin/bash
# Go-Live Procedure Script
# Usage: bash scripts/go_live.sh [log-only|live]

set -e

MODE=${1:-log-only}

echo "========================================="
echo "Quant Ω Supra AI - Go-Live Procedure"
echo "Mode: $MODE"
echo "========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Pre-flight checks
echo ""
echo -e "${BLUE}Running pre-flight checks...${NC}"
echo ""

# 1. Check Sidecar service
echo "1. Checking Sidecar service..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Sidecar is running${NC}"
    
    # Get health details
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "$HEALTH" | python3 -m json.tool | head -20
else
    echo -e "${RED}✗ Sidecar is not running${NC}"
    echo "Start with: sudo systemctl start vprop-sidecar"
    exit 1
fi

# 2. Check Redis
echo ""
echo "2. Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running${NC}"
    echo "Start with: sudo systemctl start redis-server"
    exit 1
fi

# 3. Check database
echo ""
echo "3. Checking database..."
if [ -f "/var/lib/vproptrader/data/trades.db" ]; then
    echo -e "${GREEN}✓ Database exists${NC}"
else
    echo -e "${YELLOW}⚠ Database not found - will be created${NC}"
fi

# 4. Check models
echo ""
echo "4. Checking ML models..."
if [ -d "/var/lib/vproptrader/models" ]; then
    MODEL_COUNT=$(ls -1 /var/lib/vproptrader/models/*.onnx 2>/dev/null | wc -l)
    if [ $MODEL_COUNT -gt 0 ]; then
        echo -e "${GREEN}✓ Found $MODEL_COUNT ONNX models${NC}"
    else
        echo -e "${YELLOW}⚠ No ONNX models found - will use defaults${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Models directory not found${NC}"
fi

# 5. Check dashboard
echo ""
echo "5. Checking dashboard..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Dashboard is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard not running locally${NC}"
    echo "If deployed to Vercel, this is normal"
fi

# 6. Test API endpoints
echo ""
echo "6. Testing API endpoints..."
ENDPOINTS=(
    "/health"
    "/api/signals?equity=1000"
    "/api/analytics/overview"
    "/api/analytics/compliance"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s "http://localhost:8000$endpoint" > /dev/null; then
        echo -e "${GREEN}✓ $endpoint${NC}"
    else
        echo -e "${RED}✗ $endpoint${NC}"
        exit 1
    fi
done

# Mode-specific instructions
echo ""
echo "========================================="
if [ "$MODE" == "log-only" ]; then
    echo -e "${YELLOW}LOG-ONLY MODE${NC}"
    echo "========================================="
    echo ""
    echo "The EA will:"
    echo "  ✓ Connect to Sidecar"
    echo "  ✓ Receive signals"
    echo "  ✓ Log all decisions"
    echo "  ✗ NOT execute trades"
    echo ""
    echo "MT5 EA Configuration:"
    echo "  1. Open config.mqh"
    echo "  2. Set: LogOnlyMode = true"
    echo "  3. Recompile EA"
    echo "  4. Attach to chart"
    echo ""
    echo "Monitor for 1 full trading session"
    echo "Review logs before enabling live trading"
    
elif [ "$MODE" == "live" ]; then
    echo -e "${RED}LIVE TRADING MODE${NC}"
    echo "========================================="
    echo ""
    echo -e "${RED}⚠ WARNING: This will enable LIVE TRADING${NC}"
    echo ""
    echo "Pre-requisites:"
    echo "  ✓ Log-only mode tested successfully"
    echo "  ✓ All compliance checks passed"
    echo "  ✓ Zero violations in test run"
    echo "  ✓ Team briefed and ready"
    echo ""
    echo "MT5 EA Configuration:"
    echo "  1. Open config.mqh"
    echo "  2. Set: LogOnlyMode = false"
    echo "  3. Recompile EA"
    echo "  4. Attach to chart"
    echo "  5. Enable AutoTrading"
    echo ""
    echo -e "${YELLOW}First Hour Monitoring:${NC}"
    echo "  • Watch for any errors"
    echo "  • Verify first trade execution"
    echo "  • Check compliance panel"
    echo "  • Monitor latency"
    echo "  • Verify PnL tracking"
    echo ""
    
    # Confirmation
    echo -e "${RED}Type 'GO LIVE' to confirm:${NC}"
    read -r CONFIRM
    
    if [ "$CONFIRM" != "GO LIVE" ]; then
        echo "Aborted"
        exit 0
    fi
    
    echo ""
    echo -e "${GREEN}✓ Confirmed - System is LIVE${NC}"
fi

# Monitoring commands
echo ""
echo "========================================="
echo "Monitoring Commands"
echo "========================================="
echo ""
echo "Sidecar logs:"
echo "  sudo journalctl -u vprop-sidecar -f"
echo ""
echo "System status:"
echo "  curl http://localhost:8000/health | python3 -m json.tool"
echo ""
echo "Compliance status:"
echo "  curl http://localhost:8000/api/analytics/compliance | python3 -m json.tool"
echo ""
echo "Current signals:"
echo "  curl http://localhost:8000/api/signals?equity=1000 | python3 -m json.tool"
echo ""
echo "Dashboard:"
echo "  http://localhost:3000 (or your Vercel URL)"
echo ""

# Emergency procedures
echo "========================================="
echo "Emergency Procedures"
echo "========================================="
echo ""
echo -e "${RED}KILL SWITCH:${NC}"
echo "  1. Dashboard: Click kill switch button"
echo "  2. MT5: Disable AutoTrading"
echo "  3. Sidecar: sudo systemctl stop vprop-sidecar"
echo ""
echo -e "${RED}Hard Governor Trigger:${NC}"
echo "  • DO NOT OVERRIDE"
echo "  • Review logs immediately"
echo "  • All positions auto-closed"
echo "  • Fix issue before re-enabling"
echo ""

# Final checklist
if [ "$MODE" == "live" ]; then
    echo "========================================="
    echo "Go-Live Checklist"
    echo "========================================="
    echo ""
    echo "[ ] All pre-flight checks passed"
    echo "[ ] MT5 EA attached to charts"
    echo "[ ] AutoTrading enabled"
    echo "[ ] Dashboard monitoring active"
    echo "[ ] Team ready for first hour"
    echo "[ ] Emergency procedures reviewed"
    echo ""
    echo -e "${GREEN}System is LIVE - Good luck!${NC}"
    echo ""
fi

echo "========================================="
echo "Timestamp: $(date)"
echo "========================================="
