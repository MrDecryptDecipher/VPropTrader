#!/bin/bash

# VPropTrader Signal Generation Startup Script
# This script will bootstrap the system and start generating trading signals

set -e

echo "======================================================================="
echo "VPROPTRADER SIGNAL GENERATION STARTUP"
echo "======================================================================="
echo ""

# Change to sidecar directory
cd "$(dirname "$0")/sidecar"

echo "Step 1: Testing data collection setup..."
echo "-----------------------------------------------------------------------"
python3 test_data_collection.py
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "✗ Test failed. Please check your API keys and network connection."
    echo "  Edit sidecar/.env to verify API keys are correct."
    exit 1
fi

echo ""
echo "✓ Test passed! Proceeding with full bootstrap..."
echo ""
read -p "Continue with full bootstrap? This will take 15-30 minutes. (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Bootstrap cancelled. Run this script again when ready."
    exit 0
fi

echo ""
echo "Step 2: Running complete bootstrap..."
echo "-----------------------------------------------------------------------"
python3 bootstrap_complete.py
BOOTSTRAP_RESULT=$?

if [ $BOOTSTRAP_RESULT -ne 0 ]; then
    echo ""
    echo "✗ Bootstrap failed. Check the logs above for errors."
    exit 1
fi

echo ""
echo "Step 3: Restarting sidecar service..."
echo "-----------------------------------------------------------------------"
cd ..
pm2 restart vproptrader-sidecar

echo ""
echo "Waiting for sidecar to initialize..."
sleep 5

echo ""
echo "Step 4: Verifying signal generation..."
echo "-----------------------------------------------------------------------"
curl -s "http://localhost:8002/signals?equity=1000" | python3 -m json.tool

echo ""
echo "======================================================================="
echo "✓ STARTUP COMPLETE!"
echo "======================================================================="
echo ""
echo "Your MT5 EA should now be receiving trading signals."
echo ""
echo "Next steps:"
echo "  1. Check MT5 terminal for signal logs"
echo "  2. Open dashboard: http://3.111.22.56:4001"
echo "  3. Monitor logs: pm2 logs vproptrader-sidecar"
echo ""
echo "To check signal generation stats:"
echo "  curl http://localhost:8002/signals/scanner/stats | jq"
echo ""
