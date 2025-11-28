"""Symbol mapper for converting between broker symbols"""

from typing import Dict, Optional
from loguru import logger


class SymbolMapper:
    """Maps symbols between different broker formats"""
    
    def __init__(self):
        # Common symbol mappings
        self.mappings: Dict[str, str] = {
            "NAS100": "US100",
            "US100": "NAS100",
            "XAUUSD": "GOLD",
            "GOLD": "XAUUSD",
            "EURUSD": "EURUSD",
        }
        logger.info("SymbolMapper initialized")
    
    def map_symbol(self, symbol: str) -> str:
        """Map a symbol to its alternative format"""
        return self.mappings.get(symbol, symbol)
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to standard format"""
        symbol = symbol.upper().strip()
        # Remove common suffixes
        for suffix in [".a", ".b", "_", "-"]:
            symbol = symbol.replace(suffix, "")
        return symbol
