from fastapi import APIRouter
from ...services.serpapi_service import serpapi_service

router = APIRouter()

@router.get("/health/live")
async def health_live():
    return {"status": "ok", "service": "shopmind-rag"}

@router.get("/health/ready")
async def health_ready():
    return {
        "status": "ready",
        "serpapi_configured": bool(serpapi_service.api_key),
        "cache_db_path": serpapi_service.cache_db
    }
