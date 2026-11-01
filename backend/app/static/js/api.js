/**
 * ShopMind RAG API Client
 */
const API_BASE = '/api/v1';

export const apiClient = {
  /**
   * Search products with offset/limit for dynamic infinite scroll
   */
  async searchProducts({ q = 'laptop', offset = 0, limit = 12, minPrice = null, maxPrice = null, brand = null, sortBy = 'relevance' }) {
    const params = new URLSearchParams({
      q,
      offset: offset.toString(),
      limit: limit.toString(),
      sort_by: sortBy
    });

    if (minPrice !== null && minPrice !== undefined && minPrice !== '') {
      params.append('min_price', minPrice.toString());
    }
    if (maxPrice !== null && maxPrice !== undefined && maxPrice !== '') {
      params.append('max_price', maxPrice.toString());
    }
    if (brand && brand !== 'all') {
      params.append('brand', brand);
    }

    const response = await fetch(`${API_BASE}/search?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Search failed: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Fetch complete product detail with live retailer offers
   */
  async getProductDetails(productId) {
    const response = await fetch(`${API_BASE}/products/${encodeURIComponent(productId)}`);
    if (!response.ok) {
      throw new Error(`Product lookup failed: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Compare multiple products side-by-side
   */
  async compareProducts(productIds) {
    const response = await fetch(`${API_BASE}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_ids: productIds })
    });
    if (!response.ok) {
      throw new Error(`Comparison failed: HTTP ${response.status}`);
    }
    return await response.json();
  },

  /**
   * Send prompt to grounded conversational shopping assistant
   */
  async sendChatMessage(message, currentProductIds = []) {
    const response = await fetch(`${API_BASE}/assistant/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        current_product_ids: currentProductIds
      })
    });
    if (!response.ok) {
      throw new Error(`Chat assistant failed: HTTP ${response.status}`);
    }
    return await response.json();
  }
};
