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
        
        # Massive Swarm Configuration (12+ Free Models)
        # We group them by capability, but can fallback to any.
        self.swarm = {
            "coder": [
                "kwaipilot/kat-coder-pro:free",
                "qwen/qwen3-coder:free",
                "google/gemini-2.0-flash-exp:free"
            ],
            "reasoner": [
                "tngtech/deepseek-r1t2-chimera:free",
                "alibaba/tongyi-deepresearch-30b-a3b:free",
                "nvidia/nemotron-nano-12b-v2-vl:free" # Good at reasoning too
            ],
            "general": [
                "google/gemma-3-27b-it:free",
                "meituan/longcat-flash-chat:free",
                "openai/gpt-oss-20b:free",
                "z-ai/glm-4.5-air:free",
                "moonshotai/kimi-k2:free",
                "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                "nvidia/nemotron-nano-9b-v2:free"
            ]
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
            # Dynamic sleep: 5s + random jitter
            await asyncio.sleep(5 + random.random() * 5) 
            
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
            
            # Dynamic sleep: 5s + random jitter
            await asyncio.sleep(5 + random.random() * 5) 
                
        self.population = new_population

    async def _generate_code(self, prompt: str, task_type: str = "general") -> str:
        """Calls LLM to generate code with massive swarm rotation"""
        
        # Get list of models for this task type
        primary_models = self.swarm.get(task_type, self.swarm["general"])
        # Get all other models as backup
        backup_models = []
        for k, v in self.swarm.items():
            if k != task_type:
                backup_models.extend(v)
        
        # Shuffle to spread load
        random.shuffle(primary_models)
        random.shuffle(backup_models)
        
        # Try primary models first, then backups
        models_to_try = primary_models + backup_models
        
        # Limit total attempts to avoid infinite loops, but try enough models
        models_to_try = models_to_try[:10] 
        
        base_delay = 10 # Increased base delay
        
        for model in models_to_try:
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
                    delay = base_delay + random.uniform(0, 5)
                    logger.warning(f"Rate limit on {model}. Switching in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Error with {model}: {e}")
                    # Don't sleep for non-rate-limit errors, just switch
                    
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
