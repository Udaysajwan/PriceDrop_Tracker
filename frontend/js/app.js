// Main application logic

document.addEventListener("DOMContentLoaded", async () => {
  // Elements
  const navAuth = document.getElementById("nav-auth");

  const addProductModal = document.getElementById("add-product-modal");
  const addProductForm = document.getElementById("add-product-form");
  const addProductError = document.getElementById("add-product-error");
  const addProductBtn = document.getElementById("btn-add-product");

  const chartModal = document.getElementById("chart-modal");
  const chartModalTitle = document.getElementById("chart-modal-title");
  const chartCanvas = document.getElementById("price-chart");
  const chartStats = document.getElementById("chart-stats");

  const productsContainer = document.getElementById("products-container");
  const targetHitAlert = document.getElementById("target-hit-alert");
  const targetHitMessage = document.getElementById("target-hit-message");
  const targetHitClose = document.getElementById("target-hit-close");
  const statTotal = document.getElementById("stat-total");
  const statDrops = document.getElementById("stat-drops");
  const statSavings = document.getElementById("stat-savings");

  const demoSelect = document.getElementById("demo-product-select");
  const demoPriceInput = document.getElementById("demo-new-price");
  const btnApplyDemoPrice = document.getElementById("btn-apply-demo-price");
  const demoStatusMsg = document.getElementById("demo-status-msg");

  let currentUser = null;
  let activeProducts = [];

  // ----------------------------------------------------
  // Firebase Auth Elements & Flow (Email & Password)
  // ----------------------------------------------------
  const firebaseAuthModal = document.getElementById("firebase-auth-modal");
  const firebaseAuthForm = document.getElementById("firebase-auth-form");
  const firebaseAuthTitle = document.getElementById("firebase-auth-title");
  const firebaseAuthError = document.getElementById("firebase-auth-error");
  const firebaseAuthSuccess = document.getElementById("firebase-auth-success");
  const fbEmail = document.getElementById("fb-email");
  const fbPassword = document.getElementById("fb-password");
  const fbSubmitBtn = document.getElementById("fb-submit-btn");
  const fbForgotPassword = document.getElementById("fb-forgot-password");
  const firebaseModalClose = document.getElementById("firebase-modal-close");

  let isRegisterMode = false;

  function openFirebaseAuthModal(register = false) {
    isRegisterMode = register;
    updateModalMode();
    if (firebaseAuthError) firebaseAuthError.style.display = "none";
    if (firebaseAuthSuccess) firebaseAuthSuccess.style.display = "none";
    if (firebaseAuthModal) {
      firebaseAuthModal.classList.add("active");
      if (fbEmail) fbEmail.focus();
    }
  }

  function closeFirebaseAuthModal() {
    if (firebaseAuthModal) firebaseAuthModal.classList.remove("active");
  }

  // Expose globally for instant button clicks
  window.openFirebaseAuthModal = openFirebaseAuthModal;
  window.closeFirebaseAuthModal = closeFirebaseAuthModal;

  function updateModalMode() {
    const switchContainer = document.getElementById("fb-switch-container");
    if (!switchContainer) return;

    if (isRegisterMode) {
      if (firebaseAuthTitle) firebaseAuthTitle.textContent = "Create Firebase Account";
      if (fbSubmitBtn) fbSubmitBtn.textContent = "Create Account";
      switchContainer.innerHTML = `
        Already have an account? <a href="#" id="fb-toggle-mode" style="color: var(--primary); font-weight: 600; text-decoration: none;">Sign In Instead</a>
      `;
    } else {
      if (firebaseAuthTitle) firebaseAuthTitle.textContent = "Sign In with Firebase";
      if (fbSubmitBtn) fbSubmitBtn.textContent = "Sign In";
      switchContainer.innerHTML = `
        Don't have an account? <a href="#" id="fb-toggle-mode" style="color: var(--primary); font-weight: 600; text-decoration: none;">Create Firebase Account</a>
      `;
    }

    const toggleBtn = document.getElementById("fb-toggle-mode");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        isRegisterMode = !isRegisterMode;
        updateModalMode();
      });
    }
  }

  if (firebaseModalClose) {
    firebaseModalClose.addEventListener("click", closeFirebaseAuthModal);
  }
  if (firebaseAuthModal) {
    firebaseAuthModal.addEventListener("click", (e) => {
      if (e.target === firebaseAuthModal) closeFirebaseAuthModal();
    });
  }

  if (fbForgotPassword) {
    fbForgotPassword.addEventListener("click", async (e) => {
      e.preventDefault();
      const email = fbEmail.value.trim();
      if (!email) {
        firebaseAuthError.textContent = "Please enter your email address in the field above.";
        firebaseAuthError.style.display = "block";
        return;
      }
      try {
        await window.firebaseAuth.sendPasswordReset(email);
        firebaseAuthSuccess.textContent = `Password reset email sent to ${email}. Check your inbox!`;
        firebaseAuthSuccess.style.display = "block";
        firebaseAuthError.style.display = "none";
      } catch (err) {
        firebaseAuthError.textContent = err.message || "Failed to send password reset email.";
        firebaseAuthError.style.display = "block";
      }
    });
  }

  if (firebaseAuthForm) {
    firebaseAuthForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      firebaseAuthError.style.display = "none";
      firebaseAuthSuccess.style.display = "none";
      const email = fbEmail.value.trim();
      const password = fbPassword.value;

      const originalText = fbSubmitBtn.textContent;
      fbSubmitBtn.textContent = isRegisterMode ? "Creating Account..." : "Signing In...";
      fbSubmitBtn.disabled = true;

      try {
        if (isRegisterMode) {
          await window.firebaseAuth.signUpWithEmail(email, password);
        } else {
          await window.firebaseAuth.signInWithEmail(email, password);
        }
        closeFirebaseAuthModal();
        fbPassword.value = "";
        await checkAuth();
      } catch (err) {
        console.error("Firebase Auth Error:", err);
        let message = err.message || "Authentication failed.";
        if (err.code === "auth/invalid-credential" || err.code === "auth/wrong-password") {
          message = "Incorrect email or password.";
        } else if (err.code === "auth/user-not-found") {
          message = "No account found with this email. Click 'Create Firebase Account' to register.";
        } else if (err.code === "auth/email-already-in-use") {
          message = "An account with this email already exists. Please sign in.";
        } else if (err.code === "auth/weak-password") {
          message = "Password should be at least 6 characters.";
        } else if (err.code === "auth/invalid-email") {
          message = "Please enter a valid email address.";
        }
        firebaseAuthError.textContent = message;
        firebaseAuthError.style.display = "block";
      } finally {
        fbSubmitBtn.textContent = originalText;
        fbSubmitBtn.disabled = false;
      }
    });
  }

  async function checkAuth() {
    currentUser = await window.api.getCurrentUser();
    updateNav();
    if (currentUser) {
      await loadProducts();
      initDemoSelector();
    } else {
      renderLoggedOutState();
    }
  }

  function renderLoggedOutState() {
    statTotal.textContent = "0";
    statDrops.textContent = "0";
    statSavings.textContent = "₹0.00";
    if (targetHitAlert) targetHitAlert.classList.add("hidden");
    productsContainer.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 3rem 1.5rem; background: var(--white); border-radius: var(--radius); border: 1px dashed var(--gray-300);">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🔐</div>
        <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--gray-800); margin-bottom: 0.5rem;">Sign In with Firebase</h3>
        <p style="color: var(--gray-600); max-width: 460px; margin: 0 auto 1.5rem auto; font-size: 0.95rem;">
          Sign in or register with your email and password to track products, receive price drop alerts, and view price trends.
        </p>
        <button id="btn-login-hero" class="btn btn-primary">
          Sign In / Register
        </button>
      </div>
    `;
    const heroLogin = document.getElementById("btn-login-hero");
    if (heroLogin) {
      heroLogin.addEventListener("click", () => openFirebaseAuthModal(false));
    }
  }

  function updateNav() {
    if (currentUser) {
      const displayName = currentUser.display_name || currentUser.email || "Firebase User";
      navAuth.innerHTML = `
        <span class="user-badge">👤 ${displayName}</span>
        <button id="btn-logout" class="btn btn-outline btn-sm">Sign Out</button>
      `;
      document.getElementById("btn-logout").addEventListener("click", () => {
        window.api.logout();
      });
    } else {
      navAuth.innerHTML = `
        <button id="btn-firebase-login" class="btn btn-primary btn-sm">Sign In / Register</button>
      `;
      document.getElementById("btn-firebase-login")?.addEventListener("click", () => openFirebaseAuthModal(false));
    }
  }

  // Bind initial navbar button immediately
  document.getElementById("btn-firebase-login")?.addEventListener("click", () => openFirebaseAuthModal(false));

  // Subscribe to Firebase Auth state changes
  if (window.firebaseAuth) {
    window.firebaseAuth.onFirebaseAuthStateChanged(async (user) => {
      await checkAuth();
    });
  } else {
    checkAuth();
  }

  window.addEventListener("auth-change", () => {
    checkAuth();
  });

  // ----------------------------------------------------
  // Products Management
  // ----------------------------------------------------
  targetHitClose?.addEventListener("click", () => {
    targetHitAlert.classList.add("hidden");
  });

  function renderTargetHitAlert(products) {
    const hitProduct = products.find(p => p.price_dropped);

    if (!hitProduct) {
      targetHitAlert.classList.add("hidden");
      return;
    }

    const price = Number(hitProduct.target_price ?? 0);
    const title = hitProduct.title || "This product";
    targetHitMessage.textContent = `${title} has reached your target price of ₹${price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.`;
    targetHitAlert.classList.remove("hidden");
  }

  async function loadProducts() {
    try {
      activeProducts = await window.api.getProducts();
      renderTargetHitAlert(activeProducts);
      renderProducts(activeProducts);
      updateDashboardStats(activeProducts);
    } catch (err) {
      console.error("Error loading products:", err);
    }
  }

  function updateDashboardStats(products) {
    statTotal.textContent = products.length;
    const droppedCount = products.filter(p => p.price_dropped).length;
    statDrops.textContent = droppedCount;

    let totalSavings = 0;
    products.forEach(p => {
      if (p.price_dropped && p.current_price !== null) {
        totalSavings += Math.max(0, p.target_price - p.current_price);
      }
    });
    statSavings.textContent = `₹${totalSavings.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }


  function renderProducts(products) {
    if (!products || products.length === 0) {
      productsContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <h3>No tracked products yet</h3>
          <p>Add a product URL and set your target price to start receiving price drop alerts!</p>
          <button class="btn btn-primary" id="btn-empty-add">Track Your First Product</button>
        </div>
      `;
      document.getElementById("btn-empty-add")?.addEventListener("click", () => {
        addProductModal.classList.add("active");
      });
      return;
    }

    productsContainer.innerHTML = products.map(p => {
      const isDropped = p.price_dropped;
      const badgeClass = isDropped ? "badge-dropped" : "badge-tracking";
      const badgeText = isDropped ? "🎉 Target Met!" : "Tracking";
      const priceClass = isDropped ? "price-hit" : "price-miss";
      const currentPriceStr = p.current_price !== null ? `₹${p.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : "Pending";
      const targetPriceStr = `₹${p.target_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      const imgSrc = p.image_url || "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&auto=format&fit=crop";
      const lastScrapedStr = p.last_scraped_at ? new Date(p.last_scraped_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never';

      return `
        <div class="product-card" data-id="${p.id}">
          <div class="card-img-wrap">
            <img src="${imgSrc}" alt="${p.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&auto=format&fit=crop'">
            <span class="card-badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="card-body">
            <h3 class="card-title">
              <a href="${p.url}" target="_blank" rel="noopener noreferrer" title="${p.title}">${p.title}</a>
            </h3>
            <div class="price-row">
              <div class="price-group">
                <span class="price-group-label">Current</span>
                <span class="current-price ${priceClass}">${currentPriceStr}</span>
              </div>
              <div class="price-group" style="text-align: right;">
                <span class="price-group-label">Target Price</span>
                <span class="target-price">${targetPriceStr}</span>
              </div>
            </div>
            <div class="meta-row">
              <span>Last checked: ${lastScrapedStr}</span>
              <span>${p.percent_change_from_target !== null ? `${p.percent_change_from_target > 0 ? '+' : ''}${p.percent_change_from_target}% from target` : ''}</span>
            </div>
            <div class="card-actions">
              <button class="btn btn-outline btn-sm btn-check" data-id="${p.id}">🔄 Check</button>
              <button class="btn btn-outline btn-sm btn-chart" data-id="${p.id}">📈 Trends</button>
              <button class="btn btn-danger-outline btn-sm btn-delete" data-id="${p.id}" style="margin-left: auto;">🗑️</button>
            </div>
          </div>
        </div>
      `;
    }).join("");

    // Bind action buttons
    document.querySelectorAll(".btn-check").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        const originalText = e.currentTarget.textContent;
        e.currentTarget.textContent = "Checking...";
        e.currentTarget.disabled = true;
        try {
          await window.api.checkProductNow(id);
          await loadProducts();
        } catch (err) {
          alert(`Check failed: ${err.message}`);
        } finally {
          e.currentTarget.textContent = originalText;
          e.currentTarget.disabled = false;
        }
      });
    });

    document.querySelectorAll(".btn-chart").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        openChartModal(id);
      });
    });

    document.querySelectorAll(".btn-delete").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.dataset.id;
        if (confirm("Are you sure you want to stop tracking this product?")) {
          try {
            await window.api.deleteProduct(id);
            await loadProducts();
          } catch (err) {
            alert(`Delete failed: ${err.message}`);
          }
        }
      });
    });
  }

  // ----------------------------------------------------
  // Add Product Modal & Form
  // ----------------------------------------------------
  addProductBtn.addEventListener("click", () => {
    if (!currentUser) {
      openFirebaseAuthModal(false);
      return;
    }
    addProductModal.classList.add("active");
    addProductError.style.display = "none";
  });

  addProductForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    addProductError.style.display = "none";
    const submitBtn = document.getElementById("btn-submit-product");
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Scraping & Adding...";
    submitBtn.disabled = true;

    const url = document.getElementById("product-url").value.trim();
    const targetPrice = document.getElementById("product-target-price").value;
    const title = document.getElementById("product-custom-title").value.trim();

    try {
      await window.api.createProduct(url, targetPrice, title);
      addProductModal.classList.remove("active");
      addProductForm.reset();
      await loadProducts();
    } catch (err) {
      addProductError.textContent = err.message;
      addProductError.style.display = "block";
    } finally {
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  });

  // Quick Demo Fill buttons
  document.querySelectorAll(".btn-fill-demo").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const sku = e.currentTarget.dataset.sku;
      const target = e.currentTarget.dataset.target;
      const origin = window.location.origin;
      document.getElementById("product-url").value = `${origin}/mock-store/product/${sku}`;
      document.getElementById("product-target-price").value = target;
      document.getElementById("product-custom-title").value = "";
    });
  });

  // ----------------------------------------------------
  // Price History & Chart Modal
  // ----------------------------------------------------
  async function openChartModal(productId) {
    const product = activeProducts.find(p => p.id == productId);
    if (!product) return;

    chartModalTitle.textContent = `Price Trends: ${product.title}`;
    chartModal.classList.add("active");

    try {
      const [history, summary] = await Promise.all([
        window.api.getProductHistory(productId),
        window.api.getProductSummary(productId)
      ]);

      renderPriceHistoryChart(chartCanvas, history, product.target_price, "₹");

      chartStats.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 1.5rem; text-align: center;">
          <div style="background: var(--gray-50); padding: 0.75rem; border-radius: 8px;">
            <div style="font-size: 0.75rem; color: var(--gray-600); font-weight: 600;">LOWEST</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--success);">${summary.lowest_price != null ? '₹' + summary.lowest_price.toLocaleString('en-IN') : 'N/A'}</div>
          </div>
          <div style="background: var(--gray-50); padding: 0.75rem; border-radius: 8px;">
            <div style="font-size: 0.75rem; color: var(--gray-600); font-weight: 600;">HIGHEST</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--danger);">${summary.highest_price != null ? '₹' + summary.highest_price.toLocaleString('en-IN') : 'N/A'}</div>
          </div>
          <div style="background: var(--gray-50); padding: 0.75rem; border-radius: 8px;">
            <div style="font-size: 0.75rem; color: var(--gray-600); font-weight: 600;">AVERAGE</div>
            <div style="font-size: 1.25rem; font-weight: 700;">${summary.average_price != null ? '₹' + summary.average_price.toLocaleString('en-IN') : 'N/A'}</div>
          </div>
          <div style="background: var(--gray-50); padding: 0.75rem; border-radius: 8px;">
            <div style="font-size: 0.75rem; color: var(--gray-600); font-weight: 600;">CHECKS</div>
            <div style="font-size: 1.25rem; font-weight: 700;">${summary.total_checks}</div>
          </div>
        </div>
      `;
    } catch (err) {
      console.error("Error loading chart data:", err);
    }
  }

  // ----------------------------------------------------
  // Demo Price Drop Simulator
  // ----------------------------------------------------
  async function initDemoSelector() {
    try {
      const mockItems = await window.api.getMockProducts();
      demoSelect.innerHTML = Object.entries(mockItems).map(([sku, item]) => {
        return `<option value="${sku}" data-price="${item.price}">${item.title} (Current: ₹${item.price.toLocaleString('en-IN')})</option>`;
      }).join("");

      if (demoSelect.options.length > 0) {
        demoPriceInput.value = (parseFloat(demoSelect.selectedOptions[0].dataset.price) - 5000).toFixed(2);
      }
    } catch (e) {}
  }

  demoSelect?.addEventListener("change", () => {
    const selected = demoSelect.selectedOptions[0];
    if (selected) {
      const curr = parseFloat(selected.dataset.price);
      demoPriceInput.value = Math.max(100, curr - 5000).toFixed(2);
    }
  });

  btnApplyDemoPrice?.addEventListener("click", async () => {
    const sku = demoSelect.value;
    const newPrice = demoPriceInput.value;
    if (!sku || !newPrice) return;

    btnApplyDemoPrice.textContent = "Updating...";
    btnApplyDemoPrice.disabled = true;

    try {
      const res = await window.api.updateMockPrice(sku, newPrice);
      demoStatusMsg.textContent = `✅ ${res.message}! Triggering instant check...`;
      demoStatusMsg.style.display = "block";

      // Automatically trigger check on any tracked products matching this mock SKU
      const matchingProduct = activeProducts.find(p => p.url.includes(`/mock-store/product/${sku}`));
      if (matchingProduct) {
        await window.api.checkProductNow(matchingProduct.id);
      }
      await loadProducts();
      await initDemoSelector();
    } catch (err) {
      demoStatusMsg.textContent = `❌ ${err.message}`;
      demoStatusMsg.style.display = "block";
    } finally {
      btnApplyDemoPrice.textContent = "Drop / Update Price";
      btnApplyDemoPrice.disabled = false;
      setTimeout(() => { demoStatusMsg.style.display = "none"; }, 5000);
    }
  });

  // Modal Closers
  document.querySelectorAll(".modal-close").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const modal = e.target.closest(".modal-backdrop");
      if (modal) modal.classList.remove("active");
    });
  });

  document.querySelectorAll(".modal-backdrop").forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });
  });

  // Boot
  checkAuth();
});
