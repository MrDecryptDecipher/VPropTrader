"""
Strategy Genome Module
Defines the genetic structure of a trading strategy.
"""

import uuid
import hashlib
from typing import Dict, Any, Optional

class StrategyGenome:
    """
    Represents a single trading strategy in the evolutionary pool.
    Contains the source code (genotype) and performance metrics (phenotype).
    """
    
    def __init__(self, code: str, parents: list[str] = None, generation: int = 0):
        self.id = str(uuid.uuid4())
        self.code = code
        self.parents = parents or []
        self.generation = generation
        
        # Phenotype (Performance Metrics)
        self.fitness: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.sortino_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.total_return: float = 0.0
        self.trades_count: int = 0
        
        # Metadata
        self.metadata: Dict[str, Any] = {}

    @property
    def hash(self) -> str:
        """Unique hash of the code logic to detect duplicates"""
        return hashlib.md5(self.code.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            "id": self.id,
            "code": self.code,
            "parents": self.parents,
            "generation": self.generation,
            "fitness": self.fitness,
            "metrics": {
                "sharpe": self.sharpe_ratio,
                "sortino": self.sortino_ratio,
                "drawdown": self.max_drawdown,
                "return": self.total_return,
                "trades": self.trades_count
            }
        }

    def get_executable_code(self) -> str:
        """
        Returns the code wrapped in a standard execution template if needed.
        For now, we assume the code is a valid Python function body or class.
        """
        return self.code
