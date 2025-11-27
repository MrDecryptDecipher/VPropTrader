"""Configuration management using Pydantic settings"""

from pydantic import BaseSettings, Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Base Path
    base_path: str = Field(default=".", env="BASE_PATH")
    
    # Server
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=54321, env="PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # SQLite
    database_path: str = Field(default="./data/vproptrader.db", env="DATABASE_PATH")
    
    # FAISS
    faiss_index_path: str = Field(default="./data/faiss_index", env="FAISS_INDEX_PATH")
    
    # MT5
    mt5_login: str = Field(default="", env="MT5_LOGIN")
    mt5_password: str = Field(default="", env="MT5_PASSWORD")
    mt5_server: str = Field(default="", env="MT5_SERVER")
    mt5_path: str = Field(default="", env="MT5_PATH")
    
    # External APIs
    calendar_api_url: str = Field(default="https://www.forexfactory.com/calendar", env="CALENDAR_API_URL")
    calendar_api_key: str = Field(default="", env="CALENDAR_API_KEY")
    fred_api_key: str = Field(default="", env="FRED_API_KEY")
    fred_api_url: str = Field(default="https://api.stlouisfed.org/fred", env="FRED_API_URL")
    news_api_url: str = Field(default="", env="NEWS_API_URL")
    news_api_key: str = Field(default="", env="NEWS_API_KEY")
    
    # Additional Data Sources (Optional - Free Tiers Available)
    alphavantage_api_key: str = Field(default="", env="ALPHAVANTAGE_API_KEY")
    twelvedata_api_key: str = Field(default="", env="TWELVEDATA_API_KEY")
    polygon_api_key: str = Field(default="", env="POLYGON_API_KEY")
    
    # Browserbase
    browserbase_project_id: str = Field(default="", env="BROWSERBASE_PROJECT_ID")
    browserbase_api_key: str = Field(default="", env="BROWSERBASE_API_KEY")
    
    # OpenRouter
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    
    # Data Pipeline Configuration
    collection_interval: int = Field(default=1, env="COLLECTION_INTERVAL")
    max_bars_cache: int = Field(default=5000, env="MAX_BARS_CACHE")
    batch_write_interval: int = Field(default=10, env="BATCH_WRITE_INTERVAL")
    feature_cache_ttl: int = Field(default=2, env="FEATURE_CACHE_TTL")
    redis_pool_size: int = Field(default=20, env="REDIS_POOL_SIZE")
    http_pool_size: int = Field(default=10, env="HTTP_POOL_SIZE")
    
    # Model Configuration
    model_path: str = Field(default="./models", env="MODEL_PATH")
    retrain_schedule: str = Field(default="0 2 * * *", env="RETRAIN_SCHEDULE")
    drift_threshold: float = Field(default=0.01, env="DRIFT_THRESHOLD")
    
    # Trading Configuration
    symbols: str = Field(default="NAS100,XAUUSD,EURUSD", env="SYMBOLS")
    short_term_memory_size: int = Field(default=1000, env="SHORT_TERM_MEMORY_SIZE")
    long_term_memory_days: int = Field(default=365, env="LONG_TERM_MEMORY_DAYS")
    
    # Bootstrap Configuration
    bootstrap_on_startup: bool = Field(default=True, env="BOOTSTRAP_ON_STARTUP")
    min_historical_bars: int = Field(default=5000, env="MIN_HISTORICAL_BARS")
    synthetic_data_count: int = Field(default=1000, env="SYNTHETIC_DATA_COUNT")
    
    # Risk Parameters
    daily_loss_limit: float = Field(default=-45.0, env="DAILY_LOSS_LIMIT")
    total_loss_limit: float = Field(default=-100.0, env="TOTAL_LOSS_LIMIT")
    profit_target: float = Field(default=100.0, env="PROFIT_TARGET")
    equity_disable_threshold: float = Field(default=900.0, env="EQUITY_DISABLE_THRESHOLD")
    daily_profit_cap_pct: float = Field(default=1.8, env="DAILY_PROFIT_CAP_PCT")
    
    # Performance Targets
    target_sharpe: float = Field(default=4.0, env="TARGET_SHARPE")
    target_hit_rate: float = Field(default=0.65, env="TARGET_HIT_RATE")
    max_intraday_dd: float = Field(default=0.006, env="MAX_INTRADAY_DD")
    max_peak_dd: float = Field(default=0.015, env="MAX_PEAK_DD")
    
    @property
    def symbols_list(self) -> list[str]:
        """Parse symbols string into list"""
        return [s.strip() for s in self.symbols.split(",")]
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
