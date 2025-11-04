#!/usr/bin/env python3
"""Test signals endpoint"""

import asyncio
import sys
sys.path.insert(0, '/home/ubuntu/Sandeep/projects/Vproptrader/sidecar')

async def test_signals():
    """Test the signals endpoint"""
    from app.scanner.scanner import global_scanner
    
    print("Testing scanner...")
    plans = await global_scanner.scan([])
    print(f"Got {len(plans)} plans")
    
    for plan in plans:
        print(f"  {plan.symbol} {plan.action} Q*={plan.q_star:.2f}")

if __name__ == "__main__":
    asyncio.run(test_signals())
