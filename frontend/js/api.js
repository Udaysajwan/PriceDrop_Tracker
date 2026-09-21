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
      const rawText = await response.text();
      let errorMsg = `Request failed (HTTP ${response.status}${response.statusText ? ': ' + response.statusText : ''})`;

      if (response.status === 401) {
        errorMsg = "Session expired or unauthorized. Please sign in again.";
      }

      if (rawText) {
        try {
          const data = JSON.parse(rawText);
          if (data.detail) {
            if (typeof data.detail === "string") {
              errorMsg = data.detail;
            } else if (Array.isArray(data.detail)) {
              errorMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join("; ");
            } else {
              errorMsg = JSON.stringify(data.detail);
            }
          } else if (data.message) {
            errorMsg = data.message;
          } else if (data.error) {
            errorMsg = typeof data.error === "string" ? data.error : JSON.stringify(data.error);
          }
        } catch (e) {
          // Response is plain text (e.g. 500 error or HTML error page from proxy)
          const stripped = rawText.replace(/<[^>]*>?/gm, " ").replace(/\s+/g, " ").trim();
          if (stripped) {
            errorMsg = `${errorMsg} - ${stripped.slice(0, 150)}`;
          }
        }
      }
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  }

  logout() {
    this.setToken(null);
    if (window.firebaseAuth) {
      window.firebaseAuth.signOutFirebase();
    }
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

  // Alerts Endpoints
  async getAlerts() {
    return this.request("/alerts");
  }

  async getActiveAlerts() {
    return this.request("/alerts/active");
  }

  async dismissAlert(alertId) {
    return this.request(`/alerts/${alertId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "dismissed" }),
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
