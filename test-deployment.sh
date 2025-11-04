#!/bin/bash

# VPropTrader Comprehensive Deployment Test Script
# Tests all aspects of the deployment to ensure everything is working

# Don't exit on error - we want to run all tests
set +e

echo "========================================="
echo "VPropTrader Deployment Test Suite"
echo "========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo "=== TEST 1: PM2 Process Status ==="
echo ""

# Check if sidecar is running
if pm2 list | grep -q "vproptrader-sidecar.*online"; then
    test_result 0 "Sidecar process is online"
else
    test_result 1 "Sidecar process is not online"
fi

# Check if dashboard is running
if pm2 list | grep -q "vproptrader-dashboard.*online"; then
    test_result 0 "Dashboard process is online"
else
    test_result 1 "Dashboard process is not online"
fi

echo ""
echo "=== TEST 2: Port Availability ==="
echo ""

# Check if sidecar port is listening
if ss -tlnp 2>/dev/null | grep -q ":8001"; then
    test_result 0 "Sidecar listening on port 8001"
else
    test_result 1 "Sidecar not listening on port 8001"
fi

# Check if dashboard port is listening
if ss -tlnp 2>/dev/null | grep -q ":3001"; then
    test_result 0 "Dashboard listening on port 3001"
else
    test_result 1 "Dashboard not listening on port 3001"
fi

echo ""
echo "=== TEST 3: Sidecar API Health ==="
echo ""

# Test sidecar health endpoint
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8001/health)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    test_result 0 "Sidecar health endpoint returns 200"
else
    test_result 1 "Sidecar health endpoint returns $HTTP_CODE (expected 200)"
fi

# Check if response is valid JSON
if echo "$HEALTH_BODY" | python3 -m json.tool > /dev/null 2>&1; then
    test_result 0 "Sidecar health response is valid JSON"
else
    test_result 1 "Sidecar health response is not valid JSON"
fi

# Check health status field
HEALTH_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "error")
if [ "$HEALTH_STATUS" = "degraded" ] || [ "$HEALTH_STATUS" = "healthy" ]; then
    test_result 0 "Sidecar health status is '$HEALTH_STATUS'"
else
    test_result 1 "Sidecar health status is '$HEALTH_STATUS' (expected 'degraded' or 'healthy')"
fi

# Check Redis component
REDIS_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('components', {}).get('redis', {}).get('status', 'unknown'))" 2>/dev/null || echo "error")
if [ "$REDIS_STATUS" = "healthy" ]; then
    test_result 0 "Redis component is healthy"
else
    test_result 1 "Redis component status is '$REDIS_STATUS' (expected 'healthy')"
fi

# Check Database component
DB_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('components', {}).get('database', {}).get('status', 'unknown'))" 2>/dev/null || echo "error")
if [ "$DB_STATUS" = "healthy" ]; then
    test_result 0 "Database component is healthy"
else
    test_result 1 "Database component status is '$DB_STATUS' (expected 'healthy')"
fi

# Check FAISS component
FAISS_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('components', {}).get('faiss', {}).get('status', 'unknown'))" 2>/dev/null || echo "error")
if [ "$FAISS_STATUS" = "healthy" ]; then
    test_result 0 "FAISS component is healthy"
else
    test_result 1 "FAISS component status is '$FAISS_STATUS' (expected 'healthy')"
fi

echo ""
echo "=== TEST 4: Dashboard Health ==="
echo ""

# Test dashboard endpoint
DASHBOARD_RESPONSE=$(curl -s -I http://localhost:3001 2>&1)
if echo "$DASHBOARD_RESPONSE" | grep -q "HTTP/1.1 200"; then
    test_result 0 "Dashboard returns HTTP 200"
else
    test_result 1 "Dashboard does not return HTTP 200"
fi

# Check if Next.js is serving
if echo "$DASHBOARD_RESPONSE" | grep -q "X-Powered-By: Next.js"; then
    test_result 0 "Dashboard is powered by Next.js"
else
    test_result 1 "Dashboard X-Powered-By header not found"
fi

echo ""
echo "=== TEST 5: Configuration Files ==="
echo ""

# Check ecosystem.config.js
if [ -f "ecosystem.config.js" ]; then
    test_result 0 "ecosystem.config.js exists"
    
    # Check if port 3001 is configured
    if grep -q "PORT.*3001" ecosystem.config.js; then
        test_result 0 "Dashboard port 3001 configured in ecosystem.config.js"
    else
        test_result 1 "Dashboard port 3001 not found in ecosystem.config.js"
    fi
    
    # Check if port 8001 is configured
    if grep -q "PORT.*8001" ecosystem.config.js; then
        test_result 0 "Sidecar port 8001 configured in ecosystem.config.js"
    else
        test_result 1 "Sidecar port 8001 not found in ecosystem.config.js"
    fi
else
    test_result 1 "ecosystem.config.js not found"
fi

# Check nginx config
if [ -f "vproptrader-nginx.conf" ]; then
    test_result 0 "vproptrader-nginx.conf exists"
    
    # Check if proxy to 3001 is configured
    if grep -q "proxy_pass.*3001" vproptrader-nginx.conf; then
        test_result 0 "Nginx proxy to port 3001 configured"
    else
        test_result 1 "Nginx proxy to port 3001 not found"
    fi
    
    # Check if proxy to 8001 is configured
    if grep -q "proxy_pass.*8001" vproptrader-nginx.conf; then
        test_result 0 "Nginx proxy to port 8001 configured"
    else
        test_result 1 "Nginx proxy to port 8001 not found"
    fi
else
    test_result 1 "vproptrader-nginx.conf not found"
fi

echo ""
echo "=== TEST 6: Python Code Fixes ==="
echo ""

# Check if database import is fixed in features.py
if grep -q "from app.data.database import db" sidecar/app/data/features.py; then
    test_result 0 "Database import fixed in features.py (using 'db')"
else
    test_result 1 "Database import not fixed in features.py"
fi

# Check if db. is used instead of database.
if grep -q "await db\." sidecar/app/data/features.py; then
    test_result 0 "Database usage fixed in features.py (using 'db.')"
else
    test_result 1 "Database usage not fixed in features.py"
fi

# Check if base_path is in config
if grep -q "base_path.*str" sidecar/app/core/config.py; then
    test_result 0 "base_path attribute added to Settings"
else
    test_result 1 "base_path attribute not found in Settings"
fi

echo ""
echo "=== TEST 7: TypeScript/Next.js Fixes ==="
echo ""

# Check if window check is in websocket-client.ts
if grep -q "typeof window !== 'undefined'" dashboard/src/lib/websocket-client.ts; then
    test_result 0 "SSR window check added to websocket-client.ts"
else
    test_result 1 "SSR window check not found in websocket-client.ts"
fi

# Check if lazy initialization is present
if grep -q "wsClient.*typeof window" dashboard/src/lib/websocket-client.ts; then
    test_result 0 "Lazy initialization added for wsClient export"
else
    test_result 1 "Lazy initialization not found for wsClient export"
fi

echo ""
echo "=== TEST 8: API Endpoints ==="
echo ""

# Test root endpoint
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8001/)
ROOT_HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -n1)
if [ "$ROOT_HTTP_CODE" = "200" ]; then
    test_result 0 "Sidecar root endpoint accessible"
else
    test_result 1 "Sidecar root endpoint returns $ROOT_HTTP_CODE"
fi

# Test docs endpoint
DOCS_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8001/docs)
DOCS_HTTP_CODE=$(echo "$DOCS_RESPONSE" | tail -n1)
if [ "$DOCS_HTTP_CODE" = "200" ]; then
    test_result 0 "Sidecar API docs accessible"
else
    test_result 1 "Sidecar API docs returns $DOCS_HTTP_CODE"
fi

echo ""
echo "=== TEST 9: Process Stability ==="
echo ""

# Check sidecar uptime
SIDECAR_UPTIME=$(pm2 jlist | python3 -c "import sys, json; data=json.load(sys.stdin); print([p for p in data if p['name']=='vproptrader-sidecar'][0]['pm2_env']['pm_uptime'])" 2>/dev/null || echo "0")
CURRENT_TIME=$(date +%s)000
UPTIME_SECONDS=$(( ($CURRENT_TIME - $SIDECAR_UPTIME) / 1000 ))

if [ $UPTIME_SECONDS -gt 60 ]; then
    test_result 0 "Sidecar has been running for ${UPTIME_SECONDS}s (stable)"
else
    test_result 1 "Sidecar uptime is only ${UPTIME_SECONDS}s (may be unstable)"
fi

# Check dashboard uptime
DASHBOARD_UPTIME=$(pm2 jlist | python3 -c "import sys, json; data=json.load(sys.stdin); print([p for p in data if p['name']=='vproptrader-dashboard'][0]['pm2_env']['pm_uptime'])" 2>/dev/null || echo "0")
DASHBOARD_UPTIME_SECONDS=$(( ($CURRENT_TIME - $DASHBOARD_UPTIME) / 1000 ))

if [ $DASHBOARD_UPTIME_SECONDS -gt 60 ]; then
    test_result 0 "Dashboard has been running for ${DASHBOARD_UPTIME_SECONDS}s (stable)"
else
    test_result 1 "Dashboard uptime is only ${DASHBOARD_UPTIME_SECONDS}s (may be unstable)"
fi

echo ""
echo "=== TEST 10: Log Files ==="
echo ""

# Check if log directory exists
if [ -d "logs" ]; then
    test_result 0 "Logs directory exists"
    
    # Check if sidecar logs exist
    if [ -f "logs/sidecar-out.log" ] || [ -f "logs/sidecar-error.log" ]; then
        test_result 0 "Sidecar log files exist"
    else
        test_result 1 "Sidecar log files not found"
    fi
    
    # Check if dashboard logs exist
    if [ -f "logs/dashboard-out.log" ] || [ -f "logs/dashboard-error.log" ]; then
        test_result 0 "Dashboard log files exist"
    else
        test_result 1 "Dashboard log files not found"
    fi
else
    test_result 1 "Logs directory not found"
fi

echo ""
echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo ""
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo "Success Rate: ${SUCCESS_RATE}%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================="
    echo "✓ ALL TESTS PASSED!"
    echo "=========================================${NC}"
    echo ""
    echo "Your VPropTrader deployment is fully operational."
    echo ""
    echo "Next steps:"
    echo "1. Run: sudo bash setup-nginx.sh"
    echo "2. Test external access at http://3.111.22.56:4001"
    echo ""
    exit 0
else
    echo -e "${YELLOW}========================================="
    echo "⚠ SOME TESTS FAILED"
    echo "=========================================${NC}"
    echo ""
    echo "Please review the failed tests above."
    echo "Check logs with: pm2 logs"
    echo ""
    exit 1
fi
