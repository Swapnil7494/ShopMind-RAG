from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PriceInfo(BaseModel):
    amount: float
    amount_minor: int  # Price in paise (integer representation: 1 INR = 100 paise)
    currency: str = "INR"
    formatted: str

class OfferRecord(BaseModel):
    offer_id: str
    canonical_variant_id: str
    seller_name: str
    seller_logo: Optional[str] = None
    listed_price: PriceInfo
    original_price: Optional[PriceInfo] = None
    discount: Optional[str] = None
    shipping_cost: Optional[float] = 0.0
    comparable_total: Optional[float] = None  # listed_price + shipping
    availability: str = "IN_STOCK"
    details_and_offers: List[str] = Field(default_factory=list)
    observed_at: str
    freshness: str = "FRESH"  # FRESH, CACHED, STALE
    offer_url: Optional[str] = None
    tag: Optional[str] = None

class ReviewAspect(BaseModel):
    aspect: str
    polarity: str  # positive, negative, mixed
    score: float   # 0.0 to 1.0 sentiment score
    positive_count: int
    negative_count: int
    sample_size: int
    evidence_quotes: List[str] = Field(default_factory=list)

class ProductRecord(BaseModel):
    id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    thumbnail: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = 0
    primary_price: Optional[PriceInfo] = None
    primary_source: Optional[str] = None
    delivery_info: Optional[str] = None
    tag: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    offers: List[OfferRecord] = Field(default_factory=list)
    best_offer: Optional[OfferRecord] = None
    review_aspects: List[ReviewAspect] = Field(default_factory=list)
    evidence_summary: Optional[str] = None
    observed_at: str

class SearchResponse(BaseModel):
    query: str
    total_results: int
    offset: int
    limit: int
    has_more: bool
    products: List[ProductRecord]
    available_filters: Dict[str, List[Any]] = Field(default_factory=dict)
    source_status: Dict[str, str] = Field(default_factory=dict)

class EvidenceItem(BaseModel):
    id: str
    source_type: str  # product_spec, review_intelligence, retailer_offer
    product_id: str
    product_title: str
    excerpt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    current_product_ids: Optional[List[str]] = None

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    citations: List[str] = Field(default_factory=list)
    evidence_bundle: List[EvidenceItem] = Field(default_factory=list)
    recommended_product_ids: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    query_plan: Optional[Dict[str, Any]] = None

class CompareRequest(BaseModel):
    product_ids: List[str]

class CompareResponse(BaseModel):
    products: List[ProductRecord]
    attribute_keys: List[str]
    best_prices: Dict[str, Dict[str, Any]]
