#!/bin/bash
#
# Firewall Safety Check Script
# Scans deployment scripts for prohibited firewall modification commands
# 
# This script ensures no deployment scripts attempt to modify firewall settings,
# which could compromise AWS instance security.
#

set -e

echo "========================================="
echo "Firewall Safety Check"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prohibited commands and patterns
PROHIBITED_COMMANDS=(
    "iptables"
    "ufw"
    "firewalld"
    "firewall-cmd"
    "/etc/sysconfig/iptables"
    "/etc/ufw/"
    "systemctl.*firewalld"
    "service.*firewalld"
    "systemctl.*ufw"
    "service.*ufw"
)

# Directories to scan
SCAN_DIRS=(
    "scripts"
    "deploy"
)

# Track violations
VIOLATIONS_FOUND=0
TOTAL_FILES_SCANNED=0

echo "Scanning for prohibited firewall commands..."
echo ""

# Function to check a file
check_file() {
    local file=$1
    local violations=()
    
    for cmd in "${PROHIBITED_COMMANDS[@]}"; do
        if grep -qE "$cmd" "$file" 2>/dev/null; then
            violations+=("$cmd")
        fi
    done
    
    if [ ${#violations[@]} -gt 0 ]; then
        echo -e "${RED}✗ VIOLATION FOUND${NC}: $file"
        for violation in "${violations[@]}"; do
            echo -e "  ${YELLOW}→${NC} Contains: $violation"
            # Show the line
            grep -n "$violation" "$file" | head -3 | while read line; do
                echo -e "    ${YELLOW}Line:${NC} $line"
            done
        done
        echo ""
        return 1
    else
        echo -e "${GREEN}✓${NC} $file"
        return 0
    fi
}

# Scan all script files
for dir in "${SCAN_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Scanning directory: $dir/"
        echo "---"
        
        while IFS= read -r -d '' file; do
            ((TOTAL_FILES_SCANNED++))
            if ! check_file "$file"; then
                ((VIOLATIONS_FOUND++))
            fi
        done < <(find "$dir" -type f \( -name "*.sh" -o -name "*.bash" \) -print0)
        
        echo ""
    fi
done

# Summary
echo "========================================="
echo "Scan Summary"
echo "========================================="
echo "Files scanned: $TOTAL_FILES_SCANNED"
echo "Violations found: $VIOLATIONS_FOUND"
echo ""

if [ $VIOLATIONS_FOUND -gt 0 ]; then
    echo -e "${RED}✗ FIREWALL SAFETY CHECK FAILED${NC}"
    echo ""
    echo "The following files contain prohibited firewall commands:"
    echo "These commands could compromise AWS instance security."
    echo ""
    echo "REQUIRED ACTIONS:"
    echo "1. Remove all firewall modification commands"
    echo "2. Use application-level port configuration instead"
    echo "3. Document required ports in deployment guide"
    echo "4. Never modify iptables, ufw, or firewalld"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ FIREWALL SAFETY CHECK PASSED${NC}"
    echo ""
    echo "No prohibited firewall commands found."
    echo "All deployment scripts are safe to run."
    echo ""
    exit 0
fi
