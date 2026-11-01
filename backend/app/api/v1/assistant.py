from fastapi import APIRouter
from ...models.schemas import ChatRequest, ChatResponse
from ...services.serpapi_service import serpapi_service
from ...services.rag_engine import rag_engine
from .search import normalize_shopping_item

router = APIRouter()

@router.post("/assistant/messages", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Grounded RAG Shopping Assistant endpoint.
    Retrieves facts, review intelligence, and multi-retailer offers, then synthesizes a verified answer with citations.
    """
    # Determine search topic from query or default
    q_topic = "laptop"
    msg_lower = request.message.lower()
    for category in ["macbook", "chromebook", "gaming laptop", "ultrabook", "monitor", "headphones", "tablet"]:
        if category in msg_lower:
            q_topic = category
            break

    # Fetch candidate products
    raw_search = serpapi_service.fetch_shopping_products(query=q_topic)
    shopping_items = raw_search.get("shopping_results", [])
    candidates = [normalize_shopping_item(item, idx) for idx, item in enumerate(shopping_items)]

    # If current_product_ids are provided by client, prioritize those in context
    if request.current_product_ids:
        prioritized = [p for p in candidates if p.id in request.current_product_ids]
        remaining = [p for p in candidates if p.id not in request.current_product_ids]
        candidates = prioritized + remaining

    response = rag_engine.generate_grounded_answer(user_query=request.message, products=candidates)
    return response
