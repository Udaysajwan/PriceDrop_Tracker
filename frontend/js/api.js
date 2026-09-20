// API Client wrapper for Price Drop Tracker

const API_BASE = window.location.origin;

class ApiClient {
  constructor() {
    this.token = localStorage.getItem("access_token") || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem("access_token", token);
    } else {
      localStorage.removeItem("access_token");
    }
  }

  getHeaders() {
    const headers = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...(options.headers || {}),
      },
    };

    const response = await fetch(url, config);

    if (response.status === 401) {
      this.setToken(null);
      window.dispatchEvent(new CustomEvent("auth-change", { detail: null }));
    }

    if (!response.ok) {
      let errorMsg = `Request failed: ${response.statusText}`;
      try {
        const data = await response.json();
        if (data.detail) {
          errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
        }
      } catch (e) {}
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  }

  // Auth Endpoints
  async register(email, password) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email, password) {
    const data = await this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    window.dispatchEvent(new CustomEvent("auth-change", { detail: data }));
    return data;
  }

  logout() {
    this.setToken(null);
    window.dispatchEvent(new CustomEvent("auth-change", { detail: null }));
  }

  async getCurrentUser() {
    if (!this.token) return null;
    try {
      return await this.request("/auth/me");
    } catch (e) {
      return null;
    }
  }

  // Products Endpoints
  async getProducts() {
    return this.request("/products");
  }

  async createProduct(url, targetPrice, title = null) {
    return this.request("/products", {
      method: "POST",
      body: JSON.stringify({
        url,
        target_price: parseFloat(targetPrice),
        title: title || null,
      }),
    });
  }

  async deleteProduct(productId) {
    return this.request(`/products/${productId}`, {
      method: "DELETE",
    });
  }

  async getProductHistory(productId) {
    return this.request(`/products/${productId}/history`);
  }

  async getProductSummary(productId) {
    return this.request(`/products/${productId}/summary`);
  }

  async checkProductNow(productId) {
    return this.request(`/products/${productId}/check`, {
      method: "POST",
    });
  }

  // Mock Store Endpoints
  async getMockProducts() {
    return this.request("/mock-store/list");
  }

  async updateMockPrice(sku, newPrice) {
    return this.request(`/mock-store/product/${sku}/set-price`, {
      method: "POST",
      body: JSON.stringify({ price: parseFloat(newPrice) }),
    });
  }
}

window.api = new ApiClient();
