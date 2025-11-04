#!/usr/bin/env python3
"""
Test script to verify signal generation with ES95 constraints
"""

import requests
import json
from datetime import datetime

def test_signal_generation():
    """Test the signal generation API"""
    
    print("=" * 80)
    print("VPropTrader Signal Generation Test")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
    
    # Test with different equity levels
    equity_levels = [1000, 5000, 10000]
    
    for equity in equity_levels:
        print(f"\n{'='*80}")
        print(f"Testing with Equity: ${equity}")
        print(f"{'='*80}")
        
        try:
            response = requests.get(
                f"http://localhost:8002/api/signals",
                params={"equity": equity},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                signals = data.get('signals', [])
                
                print(f"\n✅ API Response: {response.status_code}")
                print(f"📊 Signals Generated: {len(signals)}")
                
                if signals:
                    print("\n" + "─" * 80)
                    print("Signal Details:")
                    print("─" * 80)
                    
                    for i, signal in enumerate(signals, 1):
                        print(f"\n🎯 Signal #{i}:")
                        print(f"   Symbol:      {signal.get('symbol')}")
                        print(f"   Action:      {signal.get('action')}")
                        print(f"   Alpha:       {signal.get('alpha_id')}")
                        print(f"   Q* Score:    {signal.get('q_star', 0):.2f}")
                        print(f"   ES95:        ${signal.get('es95', 0):.2f}")
                        print(f"   Confidence:  {signal.get('confidence', 0):.2f}")
                        print(f"   P(win):      {signal.get('ml_predictions', {}).get('rf_pwin', 0):.2f}")
                        print(f"   Expected RR: {signal.get('expected_rr', 0):.2f}")
                        
                        # Check VPropTrader compliance
                        es95 = signal.get('es95', 0)
                        if es95 <= 10.0:
                            print(f"   ✅ ES95 Compliant (≤ $10)")
                        else:
                            print(f"   ❌ ES95 VIOLATION (> $10)")
                else:
                    print("\n⚠️  No signals generated (all filtered)")
                    
            else:
                print(f"\n❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Connection Error: {e}")
            print("Make sure the sidecar is running: pm2 status vproptrader-sidecar")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_signal_generation()
