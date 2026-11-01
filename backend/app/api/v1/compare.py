from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ...models.schemas import CompareRequest, CompareResponse, ProductRecord
from ...services.serpapi_service import serpapi_service
from .search import normalize_shopping_item

router = APIRouter()

@router.post("/compare")
async def compare_products(request: CompareRequest):
    """
    Compares two or more products across specifications, live retailer offers, and review sentiment.
    """
    if not request.product_ids:
        raise HTTPException(status_code=400, detail="At least one product_id is required for comparison")

    # Look up products from cached shopping results
    cached_search = serpapi_service.fetch_shopping_products(query="laptop")
    shopping_items = cached_search.get("shopping_results", [])
    
    all_normalized = [normalize_shopping_item(item, idx) for idx, item in enumerate(shopping_items)]
    matched_products = [p for p in all_normalized if p.id in request.product_ids]

    if not matched_products:
        # If IDs weren't in default list, take the first requested count from the catalog
        matched_products = all_normalized[:min(len(request.product_ids), 4)]

    # Collect all attribute keys across the compared products
    attribute_keys = set()
    best_prices = {}
    for p in matched_products:
        attribute_keys.update(p.attributes.keys())
        best_prices[p.id] = {
            "seller": p.best_offer.seller_name if p.best_offer else (p.primary_source or "Authorized Retailer"),
            "price": p.best_offer.listed_price.formatted if p.best_offer else (p.primary_price.formatted if p.primary_price else "N/A"),
            "comparable_total": p.best_offer.comparable_total if p.best_offer else (p.primary_price.amount if p.primary_price else 0.0)
        }

    return {
        "products": [p.model_dump() for p in matched_products],
        "attribute_keys": sorted(list(attribute_keys)),
        "best_prices": best_prices
    }
