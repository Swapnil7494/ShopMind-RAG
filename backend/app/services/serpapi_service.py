import sqlite3
import json
import time
import requests
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..config import settings
from ..models.schemas import ProductRecord, OfferRecord, PriceInfo, ReviewAspect

class SerpApiService:
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.cache_db = settings.CACHE_DB_PATH
        self._init_cache_db()

    def _init_cache_db(self):
        """Initializes SQLite cache tables for SerpApi responses with observation timestamps."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                query_key TEXT PRIMARY KEY,
                raw_json TEXT,
                created_at REAL,
                item_count INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_cache (
                product_id TEXT PRIMARY KEY,
                raw_json TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def _get_search_cache(self, query: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("SELECT raw_json, created_at FROM search_cache WHERE query_key = ?", (query.lower().strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            raw_json, created_at = row
            age = time.time() - created_at
            data = json.loads(raw_json)
            data["_cache_age"] = age
            data["_is_fresh"] = age < settings.PRICE_FRESHNESS_TTL_SECONDS
            return data
        return None

    def _save_search_cache(self, query: str, data: Dict[str, Any]):
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        item_count = len(data.get("shopping_results", []))
        cursor.execute(
            "INSERT OR REPLACE INTO search_cache (query_key, raw_json, created_at, item_count) VALUES (?, ?, ?, ?)",
            (query.lower().strip(), json.dumps(data), time.time(), item_count)
        )
        conn.commit()
        conn.close()

    def _get_product_cache(self, product_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("SELECT raw_json, created_at FROM product_cache WHERE product_id = ?", (str(product_id),))
        row = cursor.fetchone()
        conn.close()
        if row:
            raw_json, created_at = row
            age = time.time() - created_at
            data = json.loads(raw_json)
            data["_cache_age"] = age
            data["_is_fresh"] = age < settings.PRICE_FRESHNESS_TTL_SECONDS
            return data
        return None

    def _save_product_cache(self, product_id: str, data: Dict[str, Any]):
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO product_cache (product_id, raw_json, created_at) VALUES (?, ?, ?)",
            (str(product_id), json.dumps(data), time.time())
        )
        conn.commit()
        conn.close()

    def fetch_shopping_products(self, query: str = "laptops", force_refresh: bool = False) -> Dict[str, Any]:
        """Fetches products using SerpApi Google Shopping engine with caching and provenance."""
        cache_key = f"{settings.REGION}_{query.strip().lower()}"
        cached = self._get_search_cache(cache_key)

        if cached and not force_refresh:
            # If fresh or has reasonable results, use cache
            if cached.get("_is_fresh") or len(cached.get("shopping_results", [])) > 0:
                cached["source_provenance"] = "CACHE_HIT"
                return cached

        # Fetch from SerpApi
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": self.api_key,
            "num": 40,
            "gl": settings.REGION,
            "hl": settings.HL,
            "google_domain": settings.GOOGLE_DOMAIN
        }
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                data["_is_fresh"] = True
                data["_cache_age"] = 0
                data["source_provenance"] = "LIVE_SERPAPI"
                self._save_search_cache(cache_key, data)
                return data
            elif cached:
                # Fallback to stale cache if API error occurs
                cached["source_provenance"] = "FALLBACK_CACHE"
                return cached
            else:
                return {"shopping_results": [], "error": f"API Error {resp.status_code}: {resp.text}"}
        except Exception as e:
            if cached:
                cached["source_provenance"] = "FALLBACK_CACHE"
                return cached
            return {"shopping_results": [], "error": str(e)}

    def fetch_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Fetches detailed product information including cross-retailer stores and specs."""
        cached = self._get_product_cache(product_id)
        if cached and cached.get("_is_fresh"):
            return cached

        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_product",
            "product_id": product_id,
            "api_key": self.api_key,
            "gl": settings.REGION,
            "hl": settings.HL
        }
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                data["_is_fresh"] = True
                data["_cache_age"] = 0
                self._save_product_cache(product_id, data)
                return data
            elif cached:
                return cached
            return None
        except Exception:
            return cached

    def extract_attributes_from_title(self, title: str) -> Dict[str, str]:
        """Extracts common structured specs (RAM, SSD/Storage, CPU, Screen, GPU) from product titles."""
        attrs = {}
        # RAM extraction (e.g. 8GB RAM, 16 GB, 32GB)
        ram_match = re.search(r'(\d+)\s*(?:GB|gb)\s*(?:RAM|Memory|DDR[45]?)?', title, re.IGNORECASE)
        if ram_match:
            attrs["RAM"] = f"{ram_match.group(1)} GB"

        # Storage (e.g. 512GB SSD, 1TB NVMe, 256 GB)
        storage_match = re.search(r'(\d+)\s*(?:GB|TB)\s*(?:SSD|HDD|NVMe|Storage|EMMC)', title, re.IGNORECASE)
        if storage_match:
            attrs["Storage"] = storage_match.group(0).strip()
        else:
            tb_match = re.search(r'(\d+)\s*TB', title, re.IGNORECASE)
            if tb_match:
                attrs["Storage"] = f"{tb_match.group(1)} TB SSD"

        # Screen size (e.g. 14", 15.6", 16-inch)
        screen_match = re.search(r'(\d{1,2}(?:\.\d)?)\s*(?:\"|\'|\-inch|\s*inch)', title, re.IGNORECASE)
        if screen_match:
            attrs["Screen Size"] = f'{screen_match.group(1)}"'

        # Processor / GPU
        if re.search(r'intel|core i[3579]|celeron|n150|n100', title, re.IGNORECASE):
            attrs["Processor Family"] = "Intel Core / N-Series"
        elif re.search(r'ryzen|amd', title, re.IGNORECASE):
            attrs["Processor Family"] = "AMD Ryzen"
        elif re.search(r'apple|m1|m2|m3|m4', title, re.IGNORECASE):
            attrs["Processor Family"] = "Apple Silicon"

        # GPU
        gpu_match = re.search(r'(rtx\s*\d{4}|gtx\s*\d{4}|radeon|intel iris|uhd graphics)', title, re.IGNORECASE)
        if gpu_match:
            attrs["Graphics"] = gpu_match.group(0).upper()

        return attrs

serpapi_service = SerpApiService()
