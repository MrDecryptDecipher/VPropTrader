import asyncio
import pandas as pd
import numpy as np
from app.evolution.evolution_engine import EvolutionEngine

async def main():
    print("🧬 Initializing The Arena...")
    engine = EvolutionEngine(population_size=3) # Small population for testing
    
    # Create dummy data for backtesting
    print("📊 Generating synthetic market data...")
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='15min')
    df = pd.DataFrame(index=dates)
    df['Close'] = np.cumsum(np.random.randn(1000)) + 100
    df['Open'] = df['Close'] + np.random.randn(1000) * 0.1
    df['High'] = df[['Open', 'Close']].max(axis=1) + 0.2
    df['Low'] = df[['Open', 'Close']].min(axis=1) - 0.2
    df['Volume'] = np.random.randint(100, 1000, size=1000)
    
    print("🚀 Starting Evolution...")
    await engine.initialize_population()
    
    print("\n⚔️ Running Generation 0...")
    await engine.run_generation(df)
    
    best_gen0 = engine.generations_history[-1]
    print(f"Gen 0 Best Code Snippet:\n{best_gen0.code[:100]}...")
    
    print("\n🧬 Mutating and Evolving (Generation 1)...")
    await engine.run_generation(df)
    
    best_gen1 = engine.generations_history[-1]
    print(f"Gen 1 Best Sharpe: {best_gen1.sharpe_ratio:.2f}")
    
    if best_gen1.sharpe_ratio >= best_gen0.sharpe_ratio:
        print("\n✅ Evolution Successful: Fitness improved or maintained.")
    else:
        print("\n⚠️ Evolution Variance: Fitness decreased (normal in small samples).")

if __name__ == "__main__":
    asyncio.run(main())
