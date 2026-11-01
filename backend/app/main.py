import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import settings
from .api.v1.search import router as search_router
from .api.v1.products import router as products_router
from .api.v1.compare import router as compare_router
from .api.v1.assistant import router as assistant_router
from .api.v1.health import router as health_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="ShopMind RAG - Production-Grade AI Shopping Assistant with Multi-Retailer Price Comparison and Review Intelligence"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(health_router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(search_router, prefix=settings.API_PREFIX, tags=["Search"])
app.include_router(products_router, prefix=settings.API_PREFIX, tags=["Products & Offers"])
app.include_router(compare_router, prefix=settings.API_PREFIX, tags=["Comparison"])
app.include_router(assistant_router, prefix=settings.API_PREFIX, tags=["RAG Assistant"])

# Mount static folder
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "ShopMind RAG API is operational. Static frontend not yet compiled."}
