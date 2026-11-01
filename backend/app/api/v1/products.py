from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from ...services.serpapi_service import serpapi_service
from ...services.price_service import price_service
from ...services.review_intelligence import review_intelligence_service
from ...models.schemas import ProductRecord, OfferRecord

router = APIRouter()

@router.get("/products/{product_id}")
async def get_product_details(product_id: str):
    """
    Fetches full product details, attributes, live cross-retailer offers, and review aspects.
    """
    details = serpapi_service.fetch_product_details(product_id)
    if not details or "product_results" not in details:
        # If google_product details are not available directly for this ID, check search cache
        raise HTTPException(status_code=404, detail=f"Detailed product record {product_id} not found")

    pr = details.get("product_results", {})
    title = pr.get("title", "Product Details")
    brand = pr.get("brand")
    
    # Extract attributes
    attrs = {}
    for attr in pr.get("product_attributes", []):
        if isinstance(attr, dict) and "name" in attr and "value" in attr:
            attrs[attr["name"].title()] = str(attr["value"])

    # Fallback title attributes if needed
    if not attrs:
        attrs = serpapi_service.extract_attributes_from_title(title)

    # Stores / Offers normalization
    raw_stores = pr.get("stores", [])
    offers = price_service.normalize_offers(raw_stores, product_id, observation_age=details.get("_cache_age", 0))
    best_offer = offers[0] if offers else None

    # Reviews & aspect intelligence
    aspects = review_intelligence_service.analyze_product_reviews(title, 4.5, 50, attrs)

    thumbnail = None
    if pr.get("thumbnails"):
        thumbnail = pr["thumbnails"][0]

    return {
        "id": product_id,
        "title": title,
        "brand": brand,
        "thumbnail": thumbnail,
        "thumbnails": pr.get("thumbnails", []),
        "about": pr.get("about_the_product"),
        "attributes": attrs,
        "offers": [o.model_dump() for o in offers],
        "best_offer": best_offer.model_dump() if best_offer else None,
        "review_aspects": [a.model_dump() for a in aspects],
        "price_insights": pr.get("price_insights")
    }

@router.get("/products/{product_id}/offers")
async def get_product_offers(product_id: str):
    """Returns normalized cross-retailer offers with freshness and comparable total."""
    details = serpapi_service.fetch_product_details(product_id)
    if details and "product_results" in details:
        raw_stores = details["product_results"].get("stores", [])
        offers = price_service.normalize_offers(raw_stores, product_id, observation_age=details.get("_cache_age", 0))
        return {
            "product_id": product_id,
            "offers_count": len(offers),
            "offers": [o.model_dump() for o in offers]
        }
    return {"product_id": product_id, "offers_count": 0, "offers": []}
