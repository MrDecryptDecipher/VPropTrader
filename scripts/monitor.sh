#!/bin/bash
# Real-time monitoring script
# Usage: bash scripts/monitor.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Clear screen
clear

while true; do
    # Move cursor to top
    tput cup 0 0
    
    echo "========================================="
    echo "Quant Ω Supra AI - Live Monitor"
    echo "$(date '+%Y-%m-%d %H:%M:%S UTC')"
    echo "========================================="
    echo ""
    
    # System Status
    echo -e "${BLUE}SYSTEM STATUS${NC}"
    echo "─────────────────────────────────────────"
    
    # Sidecar
    if systemctl is-active --quiet vprop-sidecar 2>/dev/null; then
        echo -e "Sidecar:   ${GREEN}●${NC} Running"
    else
        echo -e "Sidecar:   ${RED}●${NC} Stopped"
    fi
    
    # Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "Redis:     ${GREEN}●${NC} Running"
    else
        echo -e "Redis:     ${RED}●${NC} Stopped"
    fi
    
    # Dashboard (check if port 3000 is listening)
    if netstat -tuln 2>/dev/null | grep -q ":3000 "; then
        echo -e "Dashboard: ${GREEN}●${NC} Running"
    else
        echo -e "Dashboard: ${YELLOW}●${NC} Not local"
    fi
    
    echo ""
    
    # Account Overview
    echo -e "${BLUE}ACCOUNT OVERVIEW${NC}"
    echo "─────────────────────────────────────────"
    
    OVERVIEW=$(curl -s http://localhost:8000/api/analytics/overview 2>/dev/null)
    if [ $? -eq 0 ]; then
        EQUITY=$(echo "$OVERVIEW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('equity', 0))" 2>/dev/null)
        PNL_TODAY=$(echo "$OVERVIEW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('pnl_today', 0))" 2>/dev/null)
        PNL_TOTAL=$(echo "$OVERVIEW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('pnl_total', 0))" 2>/dev/null)
        TRADES=$(echo "$OVERVIEW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('trades_today', 0))" 2>/dev/null)
        WINRATE=$(echo "$OVERVIEW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('win_rate', 0))" 2>/dev/null)
        
        echo "Equity:      \$$EQUITY"
        
        if (( $(echo "$PNL_TODAY >= 0" | bc -l) )); then
            echo -e "PnL Today:   ${GREEN}\$$PNL_TODAY${NC}"
        else
            echo -e "PnL Today:   ${RED}\$$PNL_TODAY${NC}"
        fi
        
        if (( $(echo "$PNL_TOTAL >= 0" | bc -l) )); then
            echo -e "PnL Total:   ${GREEN}\$$PNL_TOTAL${NC}"
        else
            echo -e "PnL Total:   ${RED}\$$PNL_TOTAL${NC}"
        fi
        
        echo "Trades:      $TRADES"
        echo "Win Rate:    $(echo "$WINRATE * 100" | bc)%"
    else
        echo -e "${RED}Unable to fetch data${NC}"
    fi
    
    echo ""
    
    # Compliance Status
    echo -e "${BLUE}COMPLIANCE STATUS${NC}"
    echo "─────────────────────────────────────────"
    
    COMPLIANCE=$(curl -s http://localhost:8000/api/analytics/compliance 2>/dev/null)
    if [ $? -eq 0 ]; then
        # Parse rules (simplified)
        VIOLATIONS=$(echo "$COMPLIANCE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rules = data.get('rules', [])
    violations = sum(1 for r in rules if r.get('status') == 'red')
    print(violations)
except:
    print('?')
" 2>/dev/null)
        
        if [ "$VIOLATIONS" == "0" ]; then
            echo -e "Status:      ${GREEN}✓ All Compliant${NC}"
        else
            echo -e "Status:      ${RED}⚠ $VIOLATIONS Violations${NC}"
        fi
        
        # Show key rules
        echo "$COMPLIANCE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rules = data.get('rules', [])[:4]  # First 4 rules
    for rule in rules:
        name = rule.get('name', 'Unknown')[:12]
        status = rule.get('status', 'unknown')
        symbol = '●'
        if status == 'green':
            color = '\033[0;32m'
        elif status == 'yellow':
            color = '\033[1;33m'
        else:
            color = '\033[0;31m'
        print(f'{name:12} {color}{symbol}\033[0m')
except:
    pass
" 2>/dev/null
    else
        echo -e "${RED}Unable to fetch data${NC}"
    fi
    
    echo ""
    
    # Active Signals
    echo -e "${BLUE}ACTIVE SIGNALS${NC}"
    echo "─────────────────────────────────────────"
    
    SIGNALS=$(curl -s "http://localhost:8000/api/signals?equity=1000" 2>/dev/null)
    if [ $? -eq 0 ]; then
        SIGNAL_COUNT=$(echo "$SIGNALS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null)
        
        if [ "$SIGNAL_COUNT" == "0" ]; then
            echo "No signals available"
        else
            echo "Count: $SIGNAL_COUNT"
            echo ""
            echo "$SIGNALS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    signals = data.get('signals', [])[:3]  # First 3 signals
    for sig in signals:
        symbol = sig.get('symbol', 'N/A')
        action = sig.get('action', 'N/A')
        qstar = sig.get('q_star', 0)
        lots = sig.get('lots', 0)
        print(f'{symbol:8} {action:4} Q*={qstar:.1f} Lots={lots:.2f}')
except:
    pass
" 2>/dev/null
        fi
    else
        echo -e "${RED}Unable to fetch data${NC}"
    fi
    
    echo ""
    
    # System Resources
    echo -e "${BLUE}SYSTEM RESOURCES${NC}"
    echo "─────────────────────────────────────────"
    
    # CPU
    CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    echo "CPU:         ${CPU}%"
    
    # Memory
    MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "Memory:      ${MEM}%"
    
    # Disk
    DISK=$(df -h / | awk 'NR==2 {print $5}')
    echo "Disk:        $DISK"
    
    echo ""
    echo "─────────────────────────────────────────"
    echo "Press Ctrl+C to exit | Refresh: 5s"
    
    # Wait 5 seconds
    sleep 5
done
