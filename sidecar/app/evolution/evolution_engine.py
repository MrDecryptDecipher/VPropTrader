"""
Evolution Engine Module
Manages the lifecycle of strategy evolution: Birth, Testing, Selection, Mutation.
"""

import asyncio
import random
from typing import List
from loguru import logger
from openai import OpenAI
from app.core.config import settings
from app.evolution.strategy_genome import StrategyGenome
from app.evolution.vector_backtester import VectorBacktester
from app.data.mt5_client import mt5_client
import pandas as pd

class EvolutionEngine:
    """
    The 'Arena' Master.
    Breeds strategies using LLMs and tests them using VectorBacktester.
    """
    
    def __init__(self, population_size: int = 10):
        self.population_size = population_size
        self.population: List[StrategyGenome] = []
        self.backtester = VectorBacktester()
        self.generations_history = []
        
        # LLM Client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        
        # Swarm Configuration (Free Tier Models)
        self.swarm = {
            "coder": "kwaipilot/kat-coder-pro:free",          # Best for writing code
            "reasoner": "tngtech/deepseek-r1t2-chimera:free", # Best for optimizing logic
            "general": "google/gemma-3-27b-it:free",         # Fallback / Crossover
            "backup": "nvidia/nemotron-nano-9b-v2:free"      # Lightweight backup
        }

    async def initialize_population(self):
        """Generates the initial pool of random strategies"""
        logger.info("Genesis: Creating initial population...")
        
        prompt = """
        Write a Python code snippet for a trading strategy.
        Input: 'df' (Pandas DataFrame with Open, High, Low, Close, Volume).
        Output: Modify 'df' to add a 'signal' column (1 for Buy, -1 for Sell, 0 for Hold).
        
        Rules:
        1. Use technical indicators (SMA, RSI, Bollinger Bands, etc.).
        2. Keep it simple but effective.
        3. Do NOT import libraries other than pandas/numpy (assumed available as pd/np).
        4. Output ONLY the code block.
        """
        
        # Run sequentially to avoid rate limits
        for i in range(self.population_size):
            # Use the specialized Coder model for Genesis
            code = await self._generate_code(prompt, task_type="coder")
            if code:
                self.population.append(StrategyGenome(code, generation=0))
                logger.info(f"Created genome {i+1}/{self.population_size}")
            await asyncio.sleep(2) 
            
        logger.info(f"Genesis complete. Population size: {len(self.population)}")

    async def run_generation(self, data: pd.DataFrame):
        """Runs one generation of evolution"""
        if not self.population:
            logger.error("Population is empty! Cannot run generation.")
            return

        current_gen = self.population[0].generation if self.population else 0
        logger.info(f"⚔️ Starting Generation {current_gen} Tournament")
        
        # 1. Evaluate Fitness
        for genome in self.population:
            if genome.fitness == 0: # Avoid re-testing if already tested
                fitness, metrics = self.backtester.run_backtest(genome, data)
                genome.fitness = fitness
                genome.sharpe_ratio = metrics.get('sharpe', 0)
                genome.max_drawdown = metrics.get('drawdown', 0)
            
        # 2. Sort by Fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Log best performer
        if self.population:
            best = self.population[0]
            logger.info(f"🏆 Gen {current_gen} Best: Sharpe={best.sharpe_ratio:.2f}, DD={best.max_drawdown:.2%}")
            self.generations_history.append(best)
        
        # 3. Selection (Top 30%)
        survivors_count = max(1, int(self.population_size * 0.3))
        survivors = self.population[:survivors_count]
        
        # 4. Reproduction (Fill the rest)
        new_population = survivors.copy()
        
        while len(new_population) < self.population_size:
            parent_a = random.choice(survivors)
            parent_b = random.choice(survivors)
            
            # 50% chance of Crossover, 50% Mutation
            if random.random() < 0.5:
                child_code = await self._crossover(parent_a, parent_b)
                child = StrategyGenome(child_code, parents=[parent_a.id, parent_b.id], generation=current_gen + 1)
            else:
                child_code = await self._mutate(parent_a)
                child = StrategyGenome(child_code, parents=[parent_a.id], generation=current_gen + 1)
                
            if child_code:
                new_population.append(child)
            
            await asyncio.sleep(2) 
                
        self.population = new_population

    async def _generate_code(self, prompt: str, task_type: str = "general") -> str:
        """Calls LLM to generate code with swarm fallback logic"""
        
        # Determine primary model based on task
        primary_model = self.swarm.get(task_type, self.swarm["general"])
        # Create a list of models to try (Primary -> General -> Backup)
        models_to_try = [primary_model]
        if primary_model != self.swarm["general"]:
            models_to_try.append(self.swarm["general"])
        models_to_try.append(self.swarm["backup"])
        
        base_delay = 5
        
        for model in models_to_try:
            for attempt in range(2): # Try each model twice
                try:
                    # logger.debug(f"Asking {model}...")
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are an expert Quant Developer. Output ONLY Python code."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    code = response.choices[0].message.content
                    return self._clean_code(code)
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "rate limit" in error_str:
                        delay = base_delay + random.uniform(0, 2)
                        logger.warning(f"Rate limit on {model}. Switching/Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Error with {model}: {e}")
                        break # Move to next model on non-rate-limit error
        
        logger.error("All swarm models failed.")
        return ""

    async def _mutate(self, genome: StrategyGenome) -> str:
        """Asks LLM to improve a strategy"""
        prompt = f"""
        Here is a trading strategy:
        ```python
        {genome.code}
        ```
        Task: Optimize this strategy. Add a filter or change parameters to improve Sharpe Ratio.
        Output ONLY the modified code.
        """
        # Use Reasoner model for mutation logic
        return await self._generate_code(prompt, task_type="reasoner")

    async def _crossover(self, genome_a: StrategyGenome, genome_b: StrategyGenome) -> str:
        """Asks LLM to combine two strategies"""
        prompt = f"""
        Strategy A:
        ```python
        {genome_a.code}
        ```
        Strategy B:
        ```python
        {genome_b.code}
        ```
        Task: Create a new strategy that combines the best logic from A and B.
        Output ONLY the merged code.
        """
        # Use General model for merging
        return await self._generate_code(prompt, task_type="general")

    def _clean_code(self, text: str) -> str:
        """Extracts code from markdown blocks and dedents it"""
        import textwrap
        
        if "```python" in text:
            text = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        # Normalize indentation
        return textwrap.dedent(text).strip()
