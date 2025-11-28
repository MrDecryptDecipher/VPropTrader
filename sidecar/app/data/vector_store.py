"""FAISS vector store for similarity search"""

import faiss
import numpy as np
from pathlib import Path
from loguru import logger
from app.core import settings


class VectorStore:
    """FAISS-based vector store"""
    
    def __init__(self):
        self.index_path = Path(settings.faiss_index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.dimension = 128  # Default dimension
        logger.info(f"VectorStore initialized: {self.index_path}")
    
    def initialize(self):
        """Initialize or load FAISS index"""
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"Created new FAISS index (dim={self.dimension})")
        except Exception as e:
            logger.warning(f"FAISS initialization failed: {e}")
            self.index = faiss.IndexFlatL2(self.dimension)
    
    def save(self):
        """Save FAISS index to disk"""
        if self.index:
            faiss.write_index(self.index, str(self.index_path))
            logger.info("FAISS index saved")
    
    def save_index(self):
        """Alias for save"""
        self.save()
    
    def get_stats(self) -> dict:
        """Get vector store statistics"""
        return {
            "initialized": self.index is not None,
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension
        }


# Global instance
vector_store = VectorStore()
