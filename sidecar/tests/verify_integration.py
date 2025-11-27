"""
System Integration Verification
Simulates the full Scanner loop to verify all components work together.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add sidecar to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntegrationTest")

# Import Scanner
from app.scanner.scanner import global_scanner
from app.data.user_db import user_db, PropFirmConfig, PropRules

async def run_integration_test():
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║   Starting System Integration Test                ║")
    print("╚═══════════════════════════════════════════════════╝")
    
    # 1. Setup Prop Rules (Block unsafe trades)
    print("\n[STEP 1] Configuring Prop Rules...")
    await user_db.init_db()
    config = PropFirmConfig(firm_name="IntegrationFirm", login="999", password="xxx", server="Demo")
    rules = PropRules(
        max_daily_loss=1000.0,
        max_total_loss=2000.0,
        profit_target=5000.0,
        trading_hours_start="00:00", # Allow all day for test
        trading_hours_end="23:59",
        timezone="UTC"
    )
    await user_db.save_prop_config(1, config, rules)
    print("✓ Prop Rules Saved")

    # 2. Run Scanner (Single Pass)
    print("\n[STEP 2] Running Scanner...")
    # We need to mock some data sources if they rely on external APIs that might fail
    # But let's try running it as is first. The scanner has try/except blocks.
    
    # We expect the scanner to:
    # 1. Check Macro Regime
    # 2. Check Prop Risk
    # 3. Calculate Quant Features
    # 4. Get Transformer Prediction
    # 5. Output Plans
    
    plans = await global_scanner.scan()
    
    print("\n[STEP 3] Analyzing Results...")
    print(f"Generated {len(plans)} Trading Plans")
    
    for plan in plans:
        print(f"  → Symbol: {plan.symbol}, Action: {plan.action}")
        print(f"    Reason: {plan.reason}")
        print(f"    Conf: {plan.confidence:.2f}, Q*: {plan.q_star:.2f}")
        
        # Verify Features present
        if 'hurst' in plan.features:
            print(f"    ✓ Quant Feature (Hurst): {plan.features['hurst']:.2f}")
        else:
            print("    ✗ Missing Quant Features")
            
        # Verify ML
        if 'tft_confidence' in plan.ml_predictions:
            print(f"    ✓ Transformer Prediction: {plan.ml_predictions['tft_confidence']:.2f}")
        else:
            print("    ✗ Missing Transformer Prediction")

    print("\n╔═══════════════════════════════════════════════════╗")
    print("║   Integration Test Complete                       ║")
    print("╚═══════════════════════════════════════════════════╝")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
