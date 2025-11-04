#!/bin/bash

echo "=================================="
echo "VPropTrader - Start Live Trading"
echo "=================================="
echo ""

# Check if system is running
echo "Checking system status..."
pm2 list | grep vproptrader

echo ""
echo "⚠️  WARNING: You are about to enable LIVE TRADING with REAL MONEY"
echo ""
echo "Before proceeding, confirm:"
echo "  1. MT5 is running and logged in"
echo "  2. QuantSupraAI EA is loaded on a chart"
echo "  3. You have read GO_LIVE_CHECKLIST.md"
echo "  4. You understand the risks"
echo ""
read -p "Type 'YES' to continue with live trading: " confirm

if [ "$confirm" != "YES" ]; then
    echo "Live trading NOT enabled. Exiting safely."
    exit 0
fi

echo ""
echo "✅ Proceeding with live trading setup..."
echo ""

# Check sidecar logs
echo "Recent sidecar activity:"
pm2 logs vproptrader-sidecar --lines 20 --nostream

echo ""
echo "=================================="
echo "NEXT STEPS:"
echo "=================================="
echo ""
echo "1. Open MT5 platform"
echo "2. Find the QuantSupraAI EA on your chart"
echo "3. Right-click the EA → Properties"
echo "4. In the 'Inputs' tab, find 'EnableLiveTrading'"
echo "5. Change it from 'false' to 'true'"
echo "6. Click OK"
echo ""
echo "The EA will now execute REAL trades based on signals."
echo ""
echo "MONITOR CLOSELY for the first hour!"
echo ""
echo "To stop trading:"
echo "  - In MT5: Click the 'AutoTrading' button to disable"
echo "  - Or run: pm2 stop vproptrader-sidecar"
echo ""
echo "Dashboard: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "Good luck! Trade responsibly."
echo ""
