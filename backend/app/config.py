import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "ShopMind RAG"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # SerpApi configuration provided by user
    SERPAPI_KEY: str = os.getenv(
        "SERPAPI_KEY",
        "fcbccfa7e47cb5bc6ffd027ddf306a6edf7fdc11248fba0d2ea741054ef6ce40"
    )
    
    # Regional and Currency Settings (India / INR)
    REGION: str = "in"
    GOOGLE_DOMAIN: str = "google.co.in"
    HL: str = "en"
    CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"
    
    # Cache and Freshness rules (per Section 10.5 in blueprint)
    CACHE_DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "cache.db"
    )
    PRICE_FRESHNESS_TTL_SECONDS: int = 1800  # 30 minutes TTL
    
    # Pagination / Infinite scroll defaults
    DEFAULT_PAGE_SIZE: int = 12
    MAX_PAGE_SIZE: int = 40
    
    # RAG parameters
    MAX_RETRIEVAL_K: int = 10
    EVIDENCE_BUDGET: int = 6

settings = Settings()
