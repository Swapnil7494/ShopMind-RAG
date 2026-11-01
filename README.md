# ShopMind RAG

**Evidence-Grounded AI Shopping Assistant • Dynamic Scroll Loading • Multi-Retailer Price Comparison • Review Intelligence**

---

## 🌟 Overview & Key Capabilities

ShopMind RAG implements an evidence-grounded e-commerce discovery engine adhering strictly to the principle:
> **"Keep product facts, customer opinions, and live seller offers in separate systems of record. Combine them only through an explicit, testable orchestration layer that returns traceable evidence."**

### 🎯 Features Implemented
1. **Dynamic Infinite Scroll ("products dynamically load as I scroll")**:
   - Modern `IntersectionObserver` observing sentinel element at the bottom of the product grid.
   - Automatically and smoothly requests paginated batches (`offset` & `limit`) from `/api/v1/search` without page reloads.
   - Shows progressive skeleton cards, live count updates ("Showing X of Y products"), and an end-of-results state.
2. **Real SerpApi Integration (`engine=google_shopping` & `engine=google_product`)**:
   - Uses the provided SerpApi key for live shopping discovery across thousands of real merchant listings.
   - Local SQLite cache (`data/cache.db`) stores observations with TTL policy (`PRICE_FRESHNESS_TTL_SECONDS = 1800`), tagging offers as `FRESH (<30m)`, `CACHED`, or `STALE`.
3. **Multi-Retailer Price Comparison Matrix**:
   - Normalizes offers across verified merchants (Best Buy, Walmart, Amazon, B&H, Target, etc.).
   - Computes **Total Comparable Cost** = `Listed Price + Mandatory Shipping Fees`.
   - Tracks stock status, delivery guarantees, discount tags, and direct retailer links.
4. **Aspect-Based Review Intelligence**:
   - Extracts aspect mentions: *Thermal Performance & Cooling, Battery Endurance, System Speed, Display & Screen Clarity, Build Quality*.
   - Computes polarity ratios, sentiment bars, sample sizes, and representative customer quotes.
5. **Grounded Conversational RAG Assistant**:
   - Generates answers strictly grounded in the retrieved evidence bundle.
   - Clickable citation badges:
     - `[prod_ev_*]` - Structured specifications
     - `[off_ev_*]` - Retailer pricing and availability
     - `[rev_ev_*]` - Verified review consensus
   - Clicking any citation opens the **Evidence Passage Drawer** showing the exact source text.
6. **Side-by-Side Product Comparison Drawer**:
   - Select multiple products to view an attribute-by-attribute matrix comparing specs, best prices across sellers, and review sentiment.

---

## 🚀 Quickstart Guide

### 1. Launch the Server
From the project directory:
```bash
python run.py
```
Or with specific Python interpreter:
```bash
& "C:\Users\Swap\AppData\Local\Programs\Python\Python310\python.exe" run.py
```

### 2. Access the Application
- **Web User Interface**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Readiness Health Endpoint**: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)

---

## 📁 Project Architecture

```
shopmind-rag/
├── backend/
│   └── app/
│       ├── main.py                     # FastAPI application & route mounting
│       ├── config.py                   # App settings, SerpApi key & freshness TTL
│       ├── models/
│       │   └── schemas.py              # Pydantic schemas for products, offers, reviews, chat
│       ├── services/
│       │   ├── serpapi_service.py      # SerpApi integration with SQLite caching & extraction
│       │   ├── price_service.py        # Multi-retailer price aggregator & total cost calculator
│       │   ├── review_intelligence.py  # Aspect sentiment analyzer & review evidence synthesizer
│       │   └── rag_engine.py           # Grounded evidence bundle composer & citation validator
│       ├── api/
│       │   └── v1/
│       │       ├── search.py           # /api/v1/search (offset/limit infinite scroll)
│       │       ├── products.py         # /api/v1/products/{id} & /offers
│       │       ├── compare.py          # /api/v1/compare
│       │       ├── assistant.py        # /api/v1/assistant/messages (grounded chat)
│       │       └── health.py           # /api/v1/health/live & /ready
│       └── static/
│           ├── index.html              # Sleek dark-mode SPA
│           ├── css/custom.css          # Glassmorphic styles & skeleton animations
│           └── js/
│               ├── api.js              # Typed API client
│               └── app.js              # State manager & infinite scroll IntersectionObserver
├── data/
│   └── cache.db                        # SQLite cache for SerpApi responses with timestamps
├── run.py                              # Server launcher
└── README.md
```
